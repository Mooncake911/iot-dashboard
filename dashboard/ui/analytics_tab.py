import streamlit as st
import pandas as pd
from datetime import datetime
from dashboard.mongo.alerts import get_mongo_client
from dashboard.mongo.analytics import fetch_analytics_history
from dashboard.http_client import request

from dashboard.ui.utils.components import section_header, metric_row, render_apply_button

def render_analytics_tab(analytics_api: str, mongo_uri: str, mongo_db: str, mongo_collection: str, limit_default: int = 100):
    """Render Analytics Monitor tab."""
    section_header("Analytics Monitor", "Real-time device statistics and health trends.", icon="📊")

    # Fetch status
    status_resp = request("GET", f"{analytics_api}/api/analytics/status")
    body = status_resp.get("body", {}) if status_resp and status_resp.get("status") == 200 else {}
    current_method = body.get("method", "Unknown")
    current_batch_size = body.get("batchSize", 0)

    # Config & Status Row
    main_col1, main_col2 = st.columns(2)

    with main_col1:
        st.subheader("⚙️ Configuration")
        method = st.selectbox(
            "Processing Method", 
            ["Sequential", "Flowable", "Observable", "CustomCollector", "ParallelStream"],
            index=1, help="RxJava processing method"
        )
        batch_size = st.number_input(
            "Batch Size", min_value=1, max_value=100000, 
            value=int(current_batch_size) or 20, step=10
        )
        if render_apply_button("analytics_config"):
            url = f"{analytics_api}/api/analytics/config?method={method}&batchSize={int(batch_size)}"
            if request("POST", url).get("status") == 200:
                st.success("Configuration applied!")
                st.rerun()
            else:
                st.error("Failed to update")

    with main_col2:
        st.subheader("📊 Current Status")
        metric_row({"Active Method": current_method, "Active Batch Size": str(current_batch_size)}, columns=1)

    st.divider()

    # UX Controls
    st.subheader("📈 Graphs")
    col_ux1, col_ux2 = st.columns([2, 1])
    with col_ux1:
        st.session_state.refresh_seconds = st.slider("🔄 Auto-refresh (sec)", 1, 60, st.session_state.refresh_seconds)
    with col_ux2:
        limit = st.number_input("📊 Show last N points", 10, 1000, int(limit_default), 10)

    # Fetch and process data
    try:
        data = fetch_analytics_history(mongo_uri, mongo_db, mongo_collection, limit=limit)
        if not data:
            st.info("No analytics data found.")
            return

        df_rows = []
        for doc in data:
            m = doc.get("metrics", {})
            df_rows.append({
                "Timestamp": pd.to_datetime(doc.get("timestamp")),
                "Battery %": m.get("battery", {}).get("avg", 0),
                "Signal %": m.get("signal", {}).get("avg", 0),
                "Online": m.get("onlineDevices", 0),
                "Total": m.get("totalDevices", 0),
                "Heartbeat": m.get("heartbeat", {}).get("avg", 0),
            })
        
        df = pd.DataFrame(df_rows).sort_values("Timestamp")
        
        # Latest metrics row
        latest = df.iloc[-1]
        st.divider()
        metric_row({
            "Online Devices": f"{int(latest['Online'])} / {int(latest['Total'])}",
            "Avg Battery": f"{latest['Battery %']:.1f}%",
            "Avg Signal": f"{latest['Signal %']:.1f}%",
            "Last Update": latest["Timestamp"].strftime("%H:%M:%S")
        })
        
        st.divider()
        
        # Charts
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Battery level**")
            st.line_chart(df.set_index("Timestamp")[["Battery %"]])
        with c2:
            st.markdown("**Signal strength**")
            st.line_chart(df.set_index("Timestamp")[["Signal %"]])

    except Exception as e:
        st.error(f"Error: {e}")
