import logging
from datetime import datetime

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from dashboard.mongo_alerts import fetch_alerts

logger = logging.getLogger(__name__)


def render_alerts_tab(
    mongo_uri: str,
    mongo_db: str,
    mongo_alerts_collection: str,
    refresh_default: int,
    limit_default: int
):
    """
    Render alerts monitoring tab with MongoDB integration.

    Features:
    - Auto-refresh capability
    - Configurable alert limit
    - Metrics dashboard
    - Alert filtering and display
    """
    st.markdown("### 🚨 Alerts Monitor")
    st.markdown("Real-time monitoring of alerts from the Rule Engine.")

    # Configuration controls
    col1, col2 = st.columns([2, 1])

    with col1:
        refresh_seconds = st.slider(
            "🔄 Auto-refresh interval (seconds)",
            min_value=1,
            max_value=30,
            value=int(refresh_default),
            help="How often to refresh alerts from MongoDB"
        )

    with col2:
        limit = st.number_input(
            "📊 Show last N alerts",
            min_value=1,
            max_value=1000,
            value=int(limit_default),
            step=10,
            help="Maximum number of alerts to display"
        )

    # Auto-refresh mechanism
    st_autorefresh(interval=int(refresh_seconds) * 1000, key="alerts_autorefresh")

    st.divider()

    # Fetch alerts from MongoDB
    try:
        st.spinner("Loading alerts from MongoDB...")
        alerts = fetch_alerts(mongo_uri, mongo_db, mongo_alerts_collection, int(limit))
    except Exception as e:
        st.error(f"❌ Failed to load alerts from MongoDB: {e}")
        logger.error(f"Failed to fetch alerts: {e}")
        alerts = []

    # Display message if no alerts
    if not alerts:
        st.info("ℹ️ No alerts found yet. Alerts will appear here when rules are triggered.")
        return

    # Metrics dashboard
    st.markdown("#### 📊 Alert Metrics")

    metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)

    with metrics_col1:
        st.metric("Total Alerts", len(alerts))

    with metrics_col2:
        severities = [a.get("severity") for a in alerts if a.get("severity") is not None]
        unique_severities = len(set(severities))
        st.metric("Severity Levels", unique_severities)

    with metrics_col3:
        rule_ids = [a.get("ruleId") for a in alerts if a.get("ruleId") is not None]
        unique_rules = len(set(rule_ids))
        st.metric("Triggered Rules", unique_rules)

    with metrics_col4:
        device_ids = [a.get("deviceId") for a in alerts if a.get("deviceId") is not None]
        unique_devices = len(set(device_ids))
        st.metric("Affected Devices", unique_devices)

    st.divider()

    # Severity breakdown
    if severities:
        st.markdown("#### 🎯 Severity Distribution")
        severity_counts = {}
        for sev in severities:
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        severity_col1, severity_col2, severity_col3 = st.columns(3)

        for idx, (severity, count) in enumerate(sorted(severity_counts.items())):
            col = [severity_col1, severity_col2, severity_col3][idx % 3]
            with col:
                # Use different emoji based on severity
                emoji = "🔴" if severity == "CRITICAL" else "🟡" if severity == "WARNING" else "🟢"
                st.metric(f"{emoji} {severity}", count)

    st.divider()

    # Alerts table
    st.markdown("#### 📋 Recent Alerts")

    # Display alerts in a dataframe with better formatting
    import pandas as pd
    df = pd.DataFrame(alerts)

    # Define color mapping function
    def color_severity(val):
        color = 'transparent'
        if isinstance(val, str):
            val_upper = val.upper()
            if val_upper == 'CRITICAL':
                color = 'red'
            elif val_upper == 'WARNING':
                color = 'yellow'
            elif val_upper == 'INFO':
                color = 'green'
        return f'background-color: {color}'

    # Apply styling
    # Note: Streamlit's style support maps pandas styler object
    styled_df = df.style.map(color_severity, subset=['severity'])

    st.dataframe(
        styled_df,
        width="stretch",
        hide_index=True,
        column_config={
            "_id": st.column_config.TextColumn("ID", width="small"),
            "ruleId": st.column_config.TextColumn("Rule", width="medium"),
            "severity": st.column_config.TextColumn("Severity", width="small"),
            "deviceId": st.column_config.NumberColumn("Device ID", width="small"),
            "message": st.column_config.TextColumn("Message", width="large"),
        }
    )

    # Footer with last refresh time
    st.caption(f"🕐 Last refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption(f"📡 Connected to: {mongo_db}.{mongo_alerts_collection}")
