import logging
from datetime import datetime

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from dashboard.mongo.alerts import fetch_alerts

from dashboard.ui.utils.components import section_header, metric_row

def render_alerts_tab(mongo_uri, mongo_db, mongo_alerts_collection, refresh_default, limit_default):
    """Render alerts monitoring tab."""
    section_header("Alerts Monitor", "Real-time monitoring of alerts from the Rule Engine.", icon="🚨")

    # Config Row
    col1, col2 = st.columns([2, 1])
    with col1:
        refresh_seconds = st.slider("🔄 Auto-refresh (sec)", 1, 30, int(refresh_default))
    with col2:
        limit = st.number_input("📊 Show last N alerts", 1, 1000, int(limit_default), 10)

    st_autorefresh(interval=int(refresh_seconds) * 1000, key="alerts_autorefresh")
    st.divider()

    try:
        alerts = fetch_alerts(mongo_uri, mongo_db, mongo_alerts_collection, int(limit))
    except Exception as e:
        st.error(f"Error fetching alerts: {e}")
        return

    if not alerts:
        st.info("No alerts found.")
        return

    # Metrics Row
    metric_row({
        "Total Alerts": len(alerts),
        "Triggered Rules": len(set(a.get("ruleId") for a in alerts if a.get("ruleId"))),
        "Affected Devices": len(set(a.get("deviceId") for a in alerts if a.get("deviceId"))),
        "Last Update": datetime.now().strftime("%H:%M:%S")
    })

    st.divider()

    # Alerts Table
    import pandas as pd
    df = pd.DataFrame(alerts)
    for col in ["currentValue", "threshold"]:
        if col in df.columns: df[col] = df[col].astype(str)

    st.dataframe(
        df, width="stretch", hide_index=True,
        column_config={
            "_id": st.column_config.TextColumn("ID", width="small"),
            "ruleId": st.column_config.TextColumn("Rule", width="medium"),
            "severity": st.column_config.TextColumn("Severity", width="small"),
            "message": st.column_config.TextColumn("Message", width="large"),
        }
    )
    st.caption(f"📡 Backend: {mongo_db}.{mongo_alerts_collection}")
