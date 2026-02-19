from dataclasses import dataclass
from typing import Dict, Any

import streamlit as st

from dashboard.services import SimulatorService
from dashboard.ui.utils.components import section_header


@dataclass(frozen=True)
class SimulatorStatus:
    device_count: int = 10
    frequency_seconds: int = 1
    batch_size: int = 500
    is_running: bool = False

    @property
    def total_load(self) -> float:
        return self.device_count / self.frequency_seconds if self.frequency_seconds > 0 else 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            device_count=int(data.get("deviceCount", 10)),
            frequency_seconds=int(data.get("frequencySeconds", 1)),
            batch_size=int(data.get("batchSize", 500)),
            is_running=bool(data.get("running", False))
        )


class SimulatorTab:
    VIEW_CONFIG = {
        True: {"label": "STARTED 🟢", "btn_label": "Stop Simulation"},
        False: {"label": "STOPPED 🔴", "btn_label": "Start Simulation"}
    }

    def __init__(self, service: SimulatorService):
        self._service = service

        if "simulator_status" not in st.session_state:
            self._sync_status()

    def _sync_status(self):
        """Синхронизация состояния сессии с сервером."""
        try:
            raw_data = self.get_status()
            st.session_state.simulator_status = SimulatorStatus.from_dict(raw_data)
        except Exception as e:
            st.error(f"Failed to sync simulator status: {e}")
            st.session_state.simulator_status = SimulatorStatus()

    @property
    def _status(self) -> SimulatorStatus:
        return st.session_state.simulator_status

    def render(self):
        section_header("Simulator Monitor", "IoT Traffic Simulation Control.", icon="📡", level=3)
        st.divider()

        with st.container(border=True):
            self._render_configuration_block()

        with st.container(border=True):
            self._render_operations_block()

    @st.fragment
    def _render_configuration_block(self):
        col1, col2 = st.columns(2, gap="xxlarge")

        with col1:
            section_header("Simulation Parameters", icon="⚙️", level=4)
            c1, c2 = st.columns(2)

            count = c1.number_input("Devices", 1, 100000, self._status.device_count, key="sim_count_input")
            freq = c2.number_input("Freq (s)", 1, 3600, self._status.frequency_seconds, key="sim_freq_input")
            
            btn_clicked = st.button("💾 Apply Configuration", width="stretch", key="sim_params_btn")

            if btn_clicked:
                self.update_config(count, freq)
                st.rerun(scope="app")

        with col2:
            c1, c2, c3 = st.columns(3)
            c1.metric("Devices", f"{self._status.device_count:,}")
            c2.metric("Frequency", f"1/{self._status.frequency_seconds}s")
            c3.metric("Batch Size", f"{self._status.batch_size:,}", help="Fixed by global configuration")
            st.metric("Aggregate Load", f"{self._status.total_load:,.1f} msg/s", help="Count / Frequency")

    @st.fragment
    def _render_operations_block(self):
        section_header("Operations", icon="🎮", level=4)

        view = self.VIEW_CONFIG[self._status.is_running]
        st.info(f"Current Status: **{view['label']}**")
        btn_toggle = st.button(view['btn_label'], width="stretch", key="sim_toggle_btn")

        if btn_toggle:
            self.toggle_simulator(self._status.is_running)
            st.rerun(scope="fragment")

    def get_status(self) -> Dict[str, Any]:
        try:
            return self._service.get_status()
        except Exception as e:
            st.error(f"Error: {str(e)}")
            return {}

    def update_config(self, count: int, frequency: int):
        try:
            if self._service.update_config(count, frequency):
                self._sync_status()
                st.toast("Configuration updated", icon="✅", duration=2)
            else:
                st.error("Server failed to update configuration")
        except Exception as e:
            st.error(f"Update error: {e}")

    def toggle_simulator(self, target_state: bool):
        try:
            if self._service.toggle_simulator(target_state):
                self._sync_status()
                st.toast("Simulation STARTED" if not target_state else "Simulation STOPPED", icon="✅", duration=2)
            else:
                st.error("Server failed to toggle simulator")
        except Exception as e:
            st.error(f"Toggle error: {e}")
