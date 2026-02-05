from datetime import datetime
import pandas as pd

import streamlit as st

from dashboard.services import AlertsService
from dashboard.ui.utils.components import section_header

SEVERITY_EMOJI = {"critical": "🔴", "warning": "🟡", "info": "🔵"}


def render_alerts_tab(service: AlertsService, refresh_default: int, limit_default: int):
    section_header("Alerts Monitor", "Real-time rule engine notifications.", icon="🚨", level=3)

    # Main UI Layout
    with st.container(border=True):
        section_header("Alerts Table", icon="📋", level=4)

        # Controls outside fragment
        c1, c2, c3 = st.columns([3, 1, 1])
        refresh_sec = c1.slider("🔄 Refresh rate (sec)", 1, 60, int(refresh_default), key="alerts_refresh_slider")
        refresh_clicked = c2.button("🔄 Refresh Now", key="alerts_refresh_btn", width="stretch")
        limit = c3.number_input("📊 Buffer size", 1, 1000, int(limit_default), 10, key="alerts_limit_input")

        if refresh_clicked:
            st.toast("Forced refresh", icon="🔄")

        @st.fragment(run_every=refresh_sec)
        def show_alerts():
            if "alerts_data" not in st.session_state:
                st.session_state.alerts_data = []

            try:
                # Fetch data
                st.session_state.alerts_data = service.get_alerts(limit=int(limit))
                st.session_state.last_alerts_refresh = datetime.now()

                alerts = st.session_state.alerts_data

                if not alerts:
                    st.info("📭 No active alerts.")
                    return

                # Metrics
                st.divider()
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total Alerts", len(alerts))
                c2.metric("Triggered Rules", len({a.get("ruleId") for a in alerts if a.get("ruleId")}))
                c3.metric("Affected Devices", len({a.get("deviceId") for a in alerts if a.get("deviceId")}))
                c4.metric("Last Sync", st.session_state.last_alerts_refresh.strftime("%H:%M:%S"))
                st.divider()

                # Table Preparation
                df = pd.DataFrame(alerts)
                if "severity" in df.columns:
                    df["severity"] = df["severity"].map(
                        lambda x: f"{SEVERITY_EMOJI.get(x.lower(), '⚪')} {x.upper()}"
                    )

                st.dataframe(
                    df,
                    width="stretch",
                    hide_index=True,
                    column_order=("severity", "ruleId", "message", "deviceId", "timestamp"),
                    column_config={
                        "severity": st.column_config.TextColumn("Severity", width="small"),
                        "ruleId": st.column_config.TextColumn("Rule ID", width="medium"),
                        "message": st.column_config.TextColumn("Alert Message", width="large"),
                        "deviceId": st.column_config.TextColumn("Device ID", width="medium"),
                        "timestamp": st.column_config.DatetimeColumn("Detected At",
                                                                     format="HH:mm:ss",
                                                                     width="small"),
                    }
                )

                # Footer
                update_time = st.session_state.last_alerts_refresh.strftime('%H:%M:%S')
                db_info = f"📍 Connected to {service.repository.db_name}.{service.repository.collection_name} | "
                st.caption(f"{db_info}Last refresh: {update_time} | Auto-refresh every {refresh_sec}s")

            except Exception as e:
                st.error(f"Alerts Pipeline Error: {e}", icon="❌")

        # Call the fragment
        show_alerts()
