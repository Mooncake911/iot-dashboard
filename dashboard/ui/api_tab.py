import logging

import streamlit as st

from dashboard.http_client import request

logger = logging.getLogger(__name__)


def render_simulator_section(simulator_api: str):
    """Render Simulator API controls section."""
    st.subheader("🔄 Simulator")

    # --- 1. Fetch Current Status (Early) ---
    # Need status to determine button state
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
    # Configuration inputs
    device_count = st.number_input(
        "Device Count",
        min_value=1,
        max_value=10000,
        value=int(current_device_count) if current_device_count > 0 else 10,
        step=1,
        help="Number of simulated IoT devices"
    )

    messages_per_second = st.number_input(
        "Messages Per Second",
        min_value=1,
        max_value=1000,
        value=int(current_msg_rate) if current_msg_rate > 0 else 1,
        step=1,
        help="Rate of message generation per device"
    )

    # Configuration button
    if st.button("⚙️ Set Configuration", key="sim_config", width="stretch"):
        url = f"{simulator_api}/api/simulator/config?deviceCount={int(device_count)}&messagesPerSecond={int(messages_per_second)}"
        st.spinner("Configuring simulator...")
        response = request("POST", url)
        if response and response.get("status") == 200:
            # Refresh status
            status_response = request("GET", f"{simulator_api}/api/simulator/status")
            if status_response and status_response.get("status") == 200:
                body = status_response.get("body", {})
                is_running = body.get("running", False)
                current_device_count = body.get("deviceCount", 0)
                current_msg_rate = body.get("messagesPerSecond", 0)
        else:
            st.error(f"Failed to configuration: {response}")

    st.divider()

    # --- 3. Status Display ---
    st.markdown("##### Current Status")

    if status_response and status_response.get("status") == 200:
        status_col1, status_col2 = st.columns(2)
        status_col1.metric(
            "State",
            "Running" if is_running else "Stopped",
            delta="Active" if is_running else "Inactive",
            delta_color="normal" if is_running else "off"
        )
        status_col2.metric("Devices / Msg Rate", f"{current_device_count} / {current_msg_rate}")
    else:
        st.warning("Status unavailable")

    # --- 4. Control Section (Toggle Button) ---
    # Single toggle button logic
    if is_running:
        # If running, show the STOP button (Red - Primary)
        if st.button("⏹️ Stop Simulator", key="sim_toggle_stop", width="stretch"):
            st.spinner("Stopping simulator...")
            request("POST", f"{simulator_api}/api/simulator/stop")
    else:
        # If stopped, show the START button (Standard)
        if st.button("▶️ Start Simulator", key="sim_toggle_start", width="stretch"):
            st.spinner("Starting simulator...")
            request("POST", f"{simulator_api}/api/simulator/start")


def render_analytics_section(analytics_api: str):
    """Render Analytics API controls section."""
    st.subheader("📈 Analytics")

    # --- 1. Fetch Current Status (Early) ---
    status_response = request("GET", f"{analytics_api}/api/analytics/status")
    current_method = "Unknown"
    current_batch_size = 0

    if status_response and status_response.get("status") == 200:
        body = status_response.get("body", {})
        current_method = body.get("method", "Unknown")
        current_batch_size = body.get("batchSize", 0)

    # --- 2. Configuration Section ---
    # Configuration inputs
    method = st.selectbox(
        "Processing Method",
        options=["Sequential", "Flowable", "Observable", "CustomCollector", "ParallelStream"],
        index=1,  # Default to Flowable
        help="RxJava processing method for analytics"
    )

    batch_size = st.number_input(
        "Batch Size",
        min_value=1,
        max_value=100000,
        # Use the current batch size if valid, else default
        value=int(current_batch_size) if current_batch_size > 0 else 20,
        step=10,
        help="Number of records to process in each batch"
    )

    # Configuration button
    if st.button("⚙️ Set Configuration", key="analytics_config", width="stretch"):
        url = f"{analytics_api}/api/analytics/config?method={method}&batchSize={int(batch_size)}"
        st.spinner("Configuring analytics...")
        response = request("POST", url)
        if response and response.get("status") == 200:
            # Re-fetch status to ensure consistency after action
            status_response = request("GET", f"{analytics_api}/api/analytics/status")
            if status_response and status_response.get("status") == 200:
                body = status_response.get("body", {})
                current_method = body.get("method", "Unknown")
                current_batch_size = body.get("batchSize", 0)
        else:
            st.error(f"Configuration failed: {response}")

    st.divider()

    # --- 3. Status Display (Beautified) ---
    st.markdown("##### Current Status")

    if status_response and status_response.get("status") == 200:
        stat_col1, stat_col2 = st.columns(2)
        stat_col1.metric("Method", current_method)
        stat_col2.metric("Batch Size", current_batch_size)
    else:
        st.warning("Status unavailable")


def render_controller_section(controller_api: str):
    """Render Controller API section (manual data ingestion - not implemented per requirements)."""
    st.subheader("🎛️ Controller")

    st.info("ℹ️ Manual data ingestion is not implemented as per requirements. Use the Simulator to generate data.")

    # Show an example payload for reference
    with st.expander("📄 Example Payload Format"):
        example_payload = [
            {
                "id": 42,
                "status": {
                    "batteryLevel": 15,
                    "signalStrength": 5,
                    "online": True
                },
                "timestamp": "2026-01-12T12:00:00Z"
            }
        ]
        st.json(example_payload)


def render_api_tab(simulator_api: str, analytics_api: str, controller_api: str):
    """
    Render the API control tab with all service endpoints.
    
    Implements API endpoints from GUIDE.md:
    - Simulator: config, start, stop, status
    - Analytics: config, status
    - Controller: info only (manual ingestion excluded per requirements)
    """
    st.markdown("### 🔌 API Control Panel")
    st.markdown("Control and configure IoT services through their REST APIs.")

    # Create three columns for services
    col1, col2, col3 = st.columns(3)

    with col1:
        render_simulator_section(simulator_api)

    with col2:
        render_analytics_section(analytics_api)

    with col3:
        render_controller_section(controller_api)
