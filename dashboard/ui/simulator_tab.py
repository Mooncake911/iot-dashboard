import streamlit as st

from dashboard.services import SimulatorService
from dashboard.ui.utils.components import section_header


def render_simulator_tab(service: SimulatorService):
    section_header("Simulator Monitor", "IoT Traffic Simulation Control.", icon="📡", level=3)

    # Get status
    status = service.get_status()
    is_running = status.get("running", False)

    # Main UI Layout
    col1, col2 = st.columns([2, 1], gap="medium")

    with col1:
        with st.container(border=True):
            section_header("Simulation Parameters", icon="⚙️", level=4)
            c1, c2 = st.columns(2)
            count = c1.number_input("Devices", 1, 10000, int(status.get("deviceCount", 10)))
            rate = c2.number_input("Msgs/sec", 1, 1000, int(status.get("messagesPerSecond", 1)))

            btn_clicked = st.button("💾 Apply Configuration", key="sim_params_btn", width="stretch")
            if btn_clicked:
                try:
                    if service.update_config(count, rate):
                        st.toast("Configuration updated", icon="✅")
                    else:
                        st.error("Failed to update configuration")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    with col2:
        with st.container(border=True):
            section_header("Current Status", icon="📊", level=4)
            if status:
                c1, c2 = st.columns(2)
                c1.metric("Active Devices", f"{status.get('deviceCount', 0)} units")
                c2.metric("Throughput", f"{status.get('messagesPerSecond', 0)} msg/s")
                st.metric("Message Load",
                          f"{status.get('deviceCount', 0) * status.get('messagesPerSecond', 0)} msg/s total")
            else:
                st.warning("Unable to reach the simulator backend. Please check your connection.")

    with st.container(border=True):
        section_header("Operations", icon="🎮", level=4)
        status_text = "🟢 RUNNING" if is_running else "🔴 STOPPED"
        st.info(f"Status: **{status_text}**")

        btn_clicked = st.button("Stop Simulation" if is_running else "Start Simulation",
                                key="start_stop_sim_btn", width="stretch")
        if btn_clicked:
            try:
                if service.toggle_simulator(is_running):
                    st.rerun()
                else:
                    st.error("Failed to toggle simulator state")
            except Exception as e:
                st.error(f"Error: {str(e)}")
