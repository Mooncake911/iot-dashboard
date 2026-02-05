from datetime import datetime
import pandas as pd

import streamlit as st

from dashboard.services import AnalyticsService
from dashboard.ui.utils.components import section_header


def render_analytics_tab(service: AnalyticsService, refresh_default: int, limit_default: int = 100):
    section_header("Analytics Monitor", "Real-time device analytics.", icon="📊", level=3)

    # Get status
    status = service.get_status()

    # Main UI Layout
    col1, col2 = st.columns([2, 1], gap="medium")

    with col1:
        with st.container(border=True):
            section_header("Engine Config", icon="⚙️", level=4)
            c1, c2 = st.columns(2)
            method = c1.selectbox("Processing Strategy",
                                  ["Sequential", "Flowable", "Observable", "CustomCollector", "ParallelStream"],
                                  index=0)
            batch = c2.number_input("Batch Size", 1, 100000, int(status.get("batchSize", 20)))

            btn_clicked = st.button("💾 Apply Configuration", key="analytics_btn", width="stretch")
            if btn_clicked:
                try:
                    if service.update_config(method, batch):
                        st.toast("Configuration updated", icon="✅")
                    else:
                        st.error("Failed to update configuration")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    with col2:
        with st.container(border=True):
            section_header("Current Status", icon="📊", level=4)
            st.metric("Engine", str(status.get("method", "N/A")))
            st.metric("Batch", str(status.get("batchSize", 0)))

    with st.container(border=True):
        section_header("Trend Analysis", icon="📈", level=4)

        # Controls outside fragment to avoid re-rendering them constantly
        c1, c2, c3 = st.columns([3, 1, 1])
        refresh_sec = c1.slider("🔄 Refresh rate (sec)", 1, 60, int(refresh_default), key="analytics_refresh_slider")
        refresh_clicked = c2.button("🔄 Refresh Now", key="analytics_refresh_btn", width="stretch")
        limit = c3.number_input("📊 Buffer size", 1, 1000, int(limit_default), 10, key="analytics_limit_input")

        if refresh_clicked:
            st.toast("Forced refresh", icon="🔄")

        @st.fragment(run_every=refresh_sec)
        def show_trends():
            if "analytics_data" not in st.session_state:
                st.session_state.analytics_data = []

            try:
                st.session_state.analytics_data = service.get_history(limit=int(limit))
                st.session_state.last_analytics_refresh = datetime.now()

                analytics = st.session_state.analytics_data

                if not analytics:
                    st.info("📭 No analytics data yet.")
                    return

                # Transformation
                df = pd.DataFrame([
                    {
                        "Time": pd.to_datetime(d.get("timestamp")),
                        "Battery": d.get("metrics", {}).get("battery", {}).get("avg", 0),
                        "Signal": d.get("metrics", {}).get("signal", {}).get("avg", 0),
                        "Online": d.get("metrics", {}).get("onlineDevices", 0),
                        "Total": d.get("metrics", {}).get("totalDevices", 0),
                    } for d in analytics
                ]).sort_values("Time")

                latest = df.iloc[-1] if len(df) > 0 else None

                if latest is not None:
                    st.divider()
                    mc1, mc2, mc3 = st.columns(3)
                    mc1.metric("Device Status", f"{int(latest['Online'])} / {int(latest['Total'])} online")
                    mc2.metric("Battery Avg", f"{latest['Battery']:.1f}%")
                    mc3.metric("Signal Avg", f"{latest['Signal']:.1f}%")
                    st.divider()

                    tab_batt, tab_sig = st.tabs(["🔋 Battery Level", "📶 Signal Strength"])
                    with tab_batt:
                        st.area_chart(df.set_index("Time")[["Battery"]], color="#2ecc71")
                    with tab_sig:
                        st.area_chart(df.set_index("Time")[["Signal"]], color="#3498db")
                else:
                    st.info("No data available yet")

                # Footer info
                update_time = st.session_state.last_analytics_refresh.strftime('%H:%M:%S')
                db_info = f"📍 Connected to {service.repository.db_name}.{service.repository.collection_name} | "
                st.caption(f"{db_info}Last refresh: {update_time} | Auto-refresh every {refresh_sec}s")

            except Exception as exp:
                st.error(f"Analytics Pipeline Error: {exp}", icon="❌")

        # Call the fragment
        show_trends()
