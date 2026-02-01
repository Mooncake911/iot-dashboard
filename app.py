import logging

import streamlit as st

from dashboard.config import load_config
from dashboard.ui.alerts_tab import render_alerts_tab
from dashboard.ui.api_tab import render_api_tab

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="IoT Dashboard",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load configuration
try:
    cfg = load_config()
    
    # Initialize mock mode state based on configuration
    from dashboard.mock import set_mock_mode
    set_mock_mode(cfg.mock_mode)
    
    logger.info(f"Configuration loaded successfully (Mock Mode: {cfg.mock_mode})")
except Exception as e:
    st.error(f"❌ Failed to load configuration: {e}")
    logger.error(f"Configuration loading failed: {e}")
    st.stop()

# Initialize session state for configuration
if 'simulator_api' not in st.session_state:
    st.session_state.simulator_api = cfg.simulator_api_url
if 'analytics_api' not in st.session_state:
    st.session_state.analytics_api = cfg.analytics_api_url
if 'controller_api' not in st.session_state:
    st.session_state.controller_api = cfg.controller_api_url
if 'mongo_uri' not in st.session_state:
    st.session_state.mongo_uri = cfg.mongo_uri
if 'mongo_db' not in st.session_state:
    st.session_state.mongo_db = cfg.mongo_db
if 'mongo_alerts_collection' not in st.session_state:
    st.session_state.mongo_alerts_collection = cfg.mongo_alerts_collection

# Main title
st.title("🌐 IoT Dashboard")
st.markdown("**Real-time monitoring and control for IoT services**")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Show mock mode indicator
    from dashboard.mock import is_mock_mode
    if is_mock_mode():
        st.warning("⚠️ MOCK MODE ENABLED")
        st.info("Using fake data and simulated responses")
        st.divider()
    
    st.subheader("🔌 Service Endpoints")
    st.session_state.simulator_api = st.text_input(
        "Simulator API",
        st.session_state.simulator_api,
        help="Base URL for the IoT Data Simulator service"
    )
    st.session_state.analytics_api = st.text_input(
        "Analytics API",
        st.session_state.analytics_api,
        help="Base URL for the Analytics service"
    )
    st.session_state.controller_api = st.text_input(
        "Controller API",
        st.session_state.controller_api,
        help="Base URL for the Controller service"
    )
    
    st.divider()
    
    st.subheader("🗄️ MongoDB")
    st.session_state.mongo_uri = st.text_input(
        "Connection URI",
        st.session_state.mongo_uri,
        type="password",
        help="MongoDB connection string"
    )
    st.session_state.mongo_db = st.text_input(
        "Database",
        st.session_state.mongo_db,
        help="MongoDB database name"
    )
    st.session_state.mongo_alerts_collection = st.text_input(
        "Alerts Collection",
        st.session_state.mongo_alerts_collection,
        help="Collection name for alerts"
    )
    
    st.divider()
    
    # Connection status indicators
    st.subheader("📊 Status")
    st.caption(f"✅ Configuration loaded from application.yml")
    st.caption(f"🔄 Auto-refresh: Enabled")

# Main content tabs
tab_api, tab_alerts = st.tabs(["🔌 API Control", "🚨 Alerts Monitor"])

with tab_api:
    render_api_tab(
        st.session_state.simulator_api,
        st.session_state.analytics_api,
        st.session_state.controller_api
    )

with tab_alerts:
    render_alerts_tab(
        mongo_uri=st.session_state.mongo_uri,
        mongo_db=st.session_state.mongo_db,
        mongo_alerts_collection=st.session_state.mongo_alerts_collection,
        refresh_default=cfg.refresh_seconds_default,
        limit_default=cfg.alerts_limit_default,
    )

# Footer
st.divider()
st.caption("🚀 IoT Dashboard v2.0 - Powered by Streamlit")
