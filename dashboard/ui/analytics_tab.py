from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any

import pandas as pd
import streamlit as st

from dashboard.services import AnalyticsService
from dashboard.ui.utils.components import section_header


@dataclass(frozen=True)
class AnalyticsStatus:
    method: str = "N/A"
    batch_size: int = 1

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            method=data.get("method", "N/A"),
            batch_size=int(data.get("batchSize", 10))
        )

    def get_method_index(self, options: list) -> int:
        try:
            return options.index(self.method)
        except ValueError:
            return 0

class AnalyticsServiceTab:
    STRATEGIES = ["Sequential", "Flowable", "Observable", "CustomCollector", "ParallelStream"]

    def __init__(self, service: AnalyticsService, refresh_default: int, limit_default: int):
        self._service = service

        if "analytics_refresh" not in st.session_state:
            st.session_state.analytics_refresh = refresh_default

        if "analytics_limit" not in st.session_state:
            st.session_state.analytics_limit = limit_default

        if "analytics_status" not in st.session_state:
            self._sync_status()

    @property
    def _refresh(self) -> int:
        return st.session_state.analytics_refresh

    @property
    def _limit(self) -> int:
        return st.session_state.analytics_limit

    @property
    def _status(self) -> AnalyticsStatus:
        return st.session_state.analytics_status

    def _sync_status(self):
        """Обновляет статус в сессии, преобразуя его в dataclass."""
        try:
            raw = self.get_status()
            st.session_state.analytics_status = AnalyticsStatus.from_dict(raw)
        except Exception as e:
            st.error(f"Status Sync Error: {e}")
            st.session_state.analytics_status = AnalyticsStatus()

    def render(self):
        section_header("Analytics Monitor", "Device performance and trends.", icon="📊", level=3)
        st.divider()

        with st.container(border=True):
            self._render_configuration_block()

        with st.container(border=True):
            self._render_trends_block()

    @st.fragment
    def _render_configuration_block(self):
        col1, col2 = st.columns(2, gap="xxlarge")

        with col1:
            section_header("Engine Config", icon="⚙️", level=4)

            c1, c2 = st.columns(2)
            current_idx = self._status.get_method_index(self.STRATEGIES)
            method = c1.selectbox("Strategy", self.STRATEGIES, index=current_idx, key="analytics_engine_select")
            batch = c2.number_input("Batch Size", 1, 100000, max(1, self._status.batch_size), key="analytics_batch_input")
            btn_clicked = st.button("💾 Apply Configuration", width="stretch", key="analytics_config_btn")

            if btn_clicked:
                self.update_config(method, batch)
                st.rerun(scope="fragment")

        with col2:
            st.metric("Engine", self._status.method)
            st.metric("Batch", self._status.batch_size)

    def _render_trends_block(self):
        section_header("Trend Analysis", icon="📈", level=4)

        c1, c2, c3 = st.columns([3, 1, 1])
        current_refresh = c1.slider("🔄 Refresh rate (sec)", 1, 60, self._refresh, key="analytics_refresh_slider")
        refresh_btn = c2.button("🔄 Refresh Now", width="stretch", key="analytics_refresh_btn")
        current_limit = c3.number_input("📊 Buffer size", 1, 1000, self._limit, 10, key="analytics_limit_input")

        if refresh_btn:
            st.toast("Forced refresh", icon="🔄", duration=2)
            st.rerun()

        st.session_state.analytics_refresh = int(current_refresh)
        st.session_state.analytics_limit = int(current_limit)

        @st.fragment(run_every=self._refresh)
        def graph_fragment():
            self._render_graphs(self._limit)

        graph_fragment()

    def _render_graphs(self, limit: int):
        try:
            analytics = self.get_history(limit)
            last_refresh_time = datetime.now()

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
            db_info = f"📍 Connected to {self._service.repository.source_name} | "
            st.caption(
                f"{db_info}Last refresh: {last_refresh_time.strftime('%H:%M:%S')} | "
                f"Auto-refresh every {self._refresh}s"
            )

        except Exception as exp:
            st.error(f"Analytics Pipeline Error: {exp}", icon="❌")

    def get_status(self) -> Dict[str, Any]:
        try:
            return self._service.get_status()
        except Exception as e:
            st.error(f"Error: {str(e)}")
            return {}

    def get_history(self, limit: int) -> List[Dict[str, Any]]:
        try:
            return self._service.get_history(limit)
        except Exception as e:
            st.error(f"Error: {str(e)}")
            return []

    def update_config(self, method: str, batch: int) -> None:
        try:
            if self._service.update_config(method, batch):
                self._sync_status()
                st.toast("Configuration updated", icon="✅", duration=2)
            else:
                st.error("Failed to update configuration")
        except Exception as e:
            st.error(f"Error: {str(e)}")
