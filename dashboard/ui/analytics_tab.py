import streamlit as st
import pandas as pd
from datetime import datetime
from dashboard.mongo_analytics import fetch_analytics_history
from dashboard.http_client import request

def render_analytics_tab(analytics_api: str, mongo_uri: str, mongo_db: str, mongo_collection: str):
    st.header("📊 Analytics Monitor")
    
    # --- 1. Processing Configuration (Moved from API tab) ---
    with st.expander("⚙️ Processing Settings", expanded=False):
        status_response = request("GET", f"{analytics_api}/api/analytics/status")
        current_method = "Unknown"
        current_batch_size = 0

        if status_response and status_response.get("status") == 200:
            body = status_response.get("body", {})
            current_method = body.get("method", "Unknown")
            current_batch_size = body.get("batchSize", 0)

        col_cfg1, col_cfg2 = st.columns(2)
        with col_cfg1:
            method = st.selectbox(
                "Processing Method",
                options=["Sequential", "Flowable", "Observable", "CustomCollector", "ParallelStream"],
                index=1,
                help="RxJava processing method for analytics"
            )
        with col_cfg2:
            batch_size = st.number_input(
                "Batch Size",
                min_value=1,
                max_value=100000,
                value=int(current_batch_size) if current_batch_size > 0 else 20,
                step=10
            )

        if st.button("💾 Apply Processor Config", key="analytics_config", use_container_width=True):
            url = f"{analytics_api}/api/analytics/config?method={method}&batchSize={int(batch_size)}"
            response = request("POST", url)
            if response and response.get("status") == 200:
                st.success("Configuration updated!")
            else:
                st.error("Failed to update configuration")

    st.divider()

    # --- 2. Monitoring Section ---
    col_ctrl1, col_ctrl2 = st.columns([1, 4])
    with col_ctrl1:
        limit = st.selectbox("Data Points", options=[50, 100, 200, 500], index=1)
    
    # Fetch data
    data = fetch_analytics_history(mongo_uri, mongo_db, mongo_collection, limit=limit)
    
    if not data:
        st.info("No analytics data found in MongoDB. Start the simulator to generate data.")
        return

    # Process data for charts
    df = pd.DataFrame([
        {
            "Timestamp": doc.get("timestamp"),
            "Battery %": doc.get("metrics", {}).get("averageBattery", 0),
            "Signal %": doc.get("metrics", {}).get("averageSignal", 0),
            "Online": doc.get("metrics", {}).get("onlineDevices", 0),
            "Total": doc.get("metrics", {}).get("totalDevices", 0),
            "Heartbeat (min)": doc.get("metrics", {}).get("averageHeartbeatDelay", 0),
            **{k: v for k, v in doc.get("metrics", {}).items() if k.startswith(("type.", "manufacturer."))}
        }
        for doc in data
    ])
    
    # Sort by timestamp ascending for charts
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df = df.sort_values("Timestamp")
    
    # Latest metrics
    latest = df.iloc[-1]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Online Devices", f"{int(latest['Online'])} / {int(latest['Total'])}")
    m2.metric("Avg Battery", f"{latest['Battery %']:.1f}%")
    m3.metric("Avg Signal", f"{latest['Signal %']:.1f}%")
    m4.metric("Last Update", latest["Timestamp"].strftime("%H:%M:%S"))

    st.divider()

    # Trend Charts
    st.subheader("📈 Trends")
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.write("**Battery Level Trend**")
        st.line_chart(df.set_index("Timestamp")[["Battery %"]])
        
    with chart_col2:
        st.write("**Signal Strength Trend**")
        st.line_chart(df.set_index("Timestamp")[["Signal %"]])

    st.divider()
    
    # Distribution
    st.subheader("🌐 Device Distribution")
    dist_col1, dist_col2 = st.columns(2)
    
    with dist_col1:
        # Filter type columns
        type_cols = [c for c in df.columns if c.startswith("type.")]
        if type_cols:
            st.write("**Device Types**")
            type_data = df[type_cols].iloc[-1].rename(lambda x: x.replace("type.", ""))
            st.bar_chart(type_data)
        else:
            st.caption("No type data available")
            
    with dist_col2:
        # Filter manufacturer columns
        man_cols = [c for c in df.columns if c.startswith("manufacturer.")]
        if man_cols:
            st.write("**Manufacturers**")
            man_data = df[man_cols].iloc[-1].rename(lambda x: x.replace("manufacturer.", ""))
            st.bar_chart(man_data)
        else:
            st.caption("No manufacturer data available")
