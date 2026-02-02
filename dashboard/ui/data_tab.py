import streamlit as st
import logging
from dashboard.http_client import request

from dashboard.ui.utils.components import section_header, metric_row, render_apply_button

def render_data_monitor_tab(simulator_api: str):
    """Render Data Monitor tab with Simulator controls."""
    section_header("Data Monitor", "Control and monitor the IoT Data Simulator.", icon="📡")

    # Fetch Current Status
    status_response = request("GET", f"{simulator_api}/api/simulator/status")
    status = status_response.get("body", {}) if status_response and status_response.get("status") == 200 else {}
    
    is_running = status.get("running", False)
    current_device_count = status.get("deviceCount", 0)
    current_msg_rate = status.get("messagesPerSecond", 0)

    # Config & Status Row
    main_col1, main_col2 = st.columns(2)

    with main_col1:
        st.subheader("⚙️ Configuration")
        device_count = st.number_input(
            "Device Count", min_value=1, max_value=10000, 
            value=int(current_device_count) if current_device_count > 0 else 10,
            step=1, help="Number of simulated IoT devices"
        )
        messages_per_second = st.number_input(
            "Messages Per Second", min_value=1, max_value=1000,
            value=int(current_msg_rate) if current_msg_rate > 0 else 1,
            step=1, help="Rate of message generation per device"
        )

        if render_apply_button("sim_config"):
            url = f"{simulator_api}/api/simulator/config?deviceCount={int(device_count)}&messagesPerSecond={int(messages_per_second)}"
            if request("POST", url).get("status") == 200:
                st.success("Configuration applied!")
            else:
                st.error("Failed to update configuration")

    with main_col2:
        st.subheader("📊 Current Status")
        if status:
            metric_row({
                "Simulator State": ("Running" if is_running else "Stopped", "Active" if is_running else "Inactive"),
                "Device Count": str(current_device_count),
                "Msg Rate (per sec)": str(current_msg_rate)
            }, columns=1)
        else:
            st.warning("⚠️ Simulator status unavailable")

    st.divider()

    # Control Section
    st.subheader("🎮 Simulator Controls")
    btn_label = "⏹️ Stop Simulator" if is_running else "▶️ Start Simulator"
    btn_key = "sim_stop" if is_running else "sim_start"
    endpoint = "stop" if is_running else "start"
    
    if st.button(btn_label, key=btn_key, use_container_width=True):
        request("POST", f"{simulator_api}/api/simulator/{endpoint}")
        st.rerun()
