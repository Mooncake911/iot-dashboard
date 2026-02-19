from datetime import datetime
from typing import List

import pandas as pd
import streamlit as st

from dashboard.services import AlertsService
from dashboard.ui.utils.components import section_header


class AlertsTab:
    SEVERITY_EMOJI = {"critical": "🔴", "warning": "🟡", "info": "🔵"}

    def __init__(self, service: AlertsService, refresh_default: int, limit_default: int):
        self._service = service

        if "alerts_refresh" not in st.session_state:
            st.session_state.alerts_refresh = refresh_default

        if "alerts_limit" not in st.session_state:
            st.session_state.alerts_limit = limit_default

    @property
    def _refresh(self) -> int:
        return st.session_state.alerts_refresh

    @property
    def _limit(self) -> int:
        return st.session_state.alerts_limit

    def render(self):
        section_header("Alerts Monitor", "Real-time rule engine notifications.", icon="🚨", level=3)
        st.divider()

        with st.container(border=True):
            self._render_controls_block()

    def _render_controls_block(self):
        section_header("Monitoring Settings", icon="⚙️", level=4)

        c1, c2, c3 = st.columns([3, 1, 1])
        current_refresh = c1.slider("🔄 Refresh rate (sec)", 1, 60, self._refresh, key="alerts_refresh_slider")
        refresh_clicked = c2.button("🔄 Refresh Now", width="stretch", key="alerts_refresh_btn")
        current_limit = c3.number_input("📊 Buffer size", 1, 1000, self._limit, 10, key="alerts_limit_input")

        if refresh_clicked:
            st.toast("Forced refresh", icon="🔄")
            st.rerun()

        st.session_state.alerts_refresh = int(current_refresh)
        st.session_state.alerts_limit = int(current_limit)

        @st.fragment(run_every=self._refresh)
        def table_fragment():
            self._render_table(self._limit)

        table_fragment()

    def _render_table(self, limit: int):
        try:
            alerts = self.get_alerts(limit)
            last_refresh_time = datetime.now()

            if not alerts:
                st.info("📭 No active alerts.")
                return

            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("Total Alerts", len(alerts))
            mc2.metric("Triggered Rules", len({a.get("ruleId") for a in alerts if a.get("ruleId")}))
            mc3.metric("Affected Devices", len({a.get("deviceId") for a in alerts if a.get("deviceId")}))
            mc4.metric("Last Sync", last_refresh_time.strftime("%H:%M:%S"))
            st.divider()

            df = pd.DataFrame(alerts)

            # Fix Arrow serialization: ensure Object columns are strings if they contain mixed types
            for col in ["currentValue", "threshold", "ruleType"]:
                if col in df.columns:
                    df[col] = df[col].astype(str)

            if "severity" in df.columns:
                df["severity"] = df["severity"].map(
                    lambda x: f"{self.SEVERITY_EMOJI.get(str(x).lower(), '🔴')} {str(x).upper()}"
                )

            st.dataframe(
                df,
                width="stretch",
                hide_index=True,
                column_order=("severity", "ruleType", "ruleId", "currentValue", "threshold", "deviceId", "timestamp"),
                column_config={
                    "severity": st.column_config.TextColumn("Severity", width="small"),
                    "ruleType": st.column_config.TextColumn("Type", width="small"),
                    "ruleId": st.column_config.TextColumn("Rule ID", width="medium"),
                    "currentValue": st.column_config.TextColumn("Value", width="small"),
                    "threshold": st.column_config.TextColumn("Threshold", width="small"),
                    "deviceId": st.column_config.TextColumn("Device ID", width="medium"),
                    "timestamp": st.column_config.DatetimeColumn(
                        "Detected At",
                        format="HH:mm:ss",
                        width="small"
                    ),
                }
            )

            # Footer info
            db_info = f"📍 Connected to {self._service.repository.source_name} | "
            st.caption(
                f"{db_info}Last refresh: {last_refresh_time.strftime('%H:%M:%S')} | "
                f"Auto-refresh every {self._refresh}s"
            )

        except Exception as e:
            st.error(f"Alerts Pipeline Error: {e}", icon="❌")

    def get_alerts(self, limit: int) -> List:
        try:
            return self._service.get_alerts(limit)
        except Exception as e:
            st.error(f"Error: {str(e)}")
            return []
