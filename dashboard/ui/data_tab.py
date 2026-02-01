import streamlit as st
import logging
from dashboard.http_client import request

logger = logging.getLogger(__name__)

def render_data_monitor_tab(simulator_api: str):
    """Render Data Monitor tab with Simulator controls."""
    st.header("📡 Data Monitor")
    st.markdown("Control and monitor the IoT Data Simulator.")

    # --- 1. Fetch Current Status (Early) ---
    status_response = request("GET", f"{simulator_api}/api/simulator/status")
    is_running = False
    current_device_count = 0
    current_msg_rate = 0

    if status_response and status_response.get("status") == 200:
        body = status_response.get("body", {})
        is_running = body.get("running", False)
        current_device_count = body.get("deviceCount", 0)
        current_msg_rate = body.get("messagesPerSecond", 0)

    # --- 2. Configuration Section ---
    st.subheader("⚙️ Simulator Configuration")
    col_input1, col_input2 = st.columns(2)
    
    with col_input1:
        device_count = st.number_input(
            "Device Count",
            min_value=1,
            max_value=10000,
            value=int(current_device_count) if current_device_count > 0 else 10,
            step=1,
            help="Number of simulated IoT devices"
        )

    with col_input2:
        messages_per_second = st.number_input(
            "Messages Per Second",
            min_value=1,
            max_value=1000,
            value=int(current_msg_rate) if current_msg_rate > 0 else 1,
            step=1,
            help="Rate of message generation per device"
        )

    if st.button("💾 Apply Configuration", key="sim_config", width="stretch"):
        url = f"{simulator_api}/api/simulator/config?deviceCount={int(device_count)}&messagesPerSecond={int(messages_per_second)}"
        st.spinner("Configuring simulator...")
        response = request("POST", url)
        if response and response.get("status") == 200:
            st.success("Configuration applied!")
            # Force refresh would be good here but let streamlit handle it on next cycle
        else:
            st.error(f"Failed to configuration: {response}")

    st.divider()

    # --- 3. Status Display ---
    st.subheader("📊 Current Status")

    if status_response and status_response.get("status") == 200:
        status_col1, status_col2, status_col3 = st.columns(3)
        status_col1.metric(
            "Simulator State",
            "Running" if is_running else "Stopped",
            delta="Active" if is_running else "Inactive",
            delta_color="normal" if is_running else "off"
        )
        status_col2.metric("Device Count", f"{current_device_count}")
        status_col3.metric("Msg Rate (per sec)", f"{current_msg_rate}")
    else:
        st.warning("⚠️ Simulator status unavailable")

    st.divider()

    # --- 4. Control Section (Toggle Button) ---
    st.subheader("🎮 Simulator Controls")
    if is_running:
        if st.button("⏹️ Stop Simulator", key="sim_toggle_stop", use_container_width=True, type="primary"):
            st.spinner("Stopping simulator...")
            request("POST", f"{simulator_api}/api/simulator/stop")
            st.rerun()
    else:
        if st.button("▶️ Start Simulator", key="sim_toggle_start", use_container_width=True):
            st.spinner("Starting simulator...")
            request("POST", f"{simulator_api}/api/simulator/start")
            st.rerun()
