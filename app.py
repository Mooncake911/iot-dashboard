import streamlit as st
import logging

from dashboard.config import load_config
from dashboard.ui import render_alerts_tab, render_simulator_tab, render_analytics_tab
from dashboard.ui.utils.styles import apply_custom_styles

# Apply custom styles (optional)
apply_custom_styles()

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
    from dashboard.mock import set_mock_mode

    cfg = load_config()
    set_mock_mode(cfg.mock_mode)
    logger.info(f"Configuration loaded successfully (Mock Mode: {cfg.mock_mode})")

except Exception as e:
    st.error(f"❌ Failed to load configuration: {e}")
    logger.error(f"Configuration loading failed: {e}")
    st.stop()

# Auto-refresh logic
# refresh_interval = cfg.refresh_seconds_default * 1000
# st_autorefresh(interval=refresh_interval, key="data_refresh")

# Main title
st.title("🌐 IoT Dashboard")
st.markdown("**Real-time monitoring and control for IoT services**")

# Initialize services (Dependency Injection Root)
if 'services_initialized' not in st.session_state:
    from dashboard.core.client import RealApiClient, MockApiClient
    from dashboard.services.simulator_service import SimulatorService
    from dashboard.services.analytics_service import AnalyticsService
    from dashboard.mock import is_mock_mode

    # 1. Create API Client Strategy
    if is_mock_mode():
        logger.info("Initializing services in MOCK mode")
        from dashboard.core.client import MockApiClient
        from dashboard.mock import MockMongoAlerts, MockMongoAnalytics
        
        sim_client = MockApiClient()
        analytics_client = MockApiClient()
        
        alerts_repo = MockMongoAlerts()
        analytics_repo = MockMongoAnalytics()
    else:
        logger.info("Initializing services in REAL mode")
        from dashboard.core.client import RealApiClient
        from dashboard.mongo.alerts import MongoAlertsRepository
        from dashboard.mongo.analytics import MongoAnalyticsRepository
        
        sim_client = RealApiClient(cfg.simulator_api_url)
        analytics_client = RealApiClient(cfg.analytics_api_url)
        
        alerts_repo = MongoAlertsRepository(cfg.mongo_uri, cfg.mongo_db, cfg.mongo_alerts_collection)
        analytics_repo = MongoAnalyticsRepository(cfg.mongo_uri, cfg.mongo_db, cfg.mongo_analytics_collection)

    # 2. Wire Services
    from dashboard.services.simulator_service import SimulatorService
    from dashboard.services.analytics_service import AnalyticsService
    from dashboard.services.alerts_service import AlertsService

    st.session_state.simulator_service = SimulatorService(sim_client)
    st.session_state.analytics_service = AnalyticsService(analytics_client, analytics_repo)
    st.session_state.alerts_service = AlertsService(alerts_repo)
    st.session_state.services_initialized = True

# Sidebar configuration
with st.sidebar:
    from dashboard.mock import is_mock_mode

    st.header("⚙️ Configuration")

    if is_mock_mode():
        st.warning("⚠️ MOCK MODE ENABLED")
        st.info("Using fake data and simulated responses")
        st.divider()

    st.info(f"Simulator API: {cfg.simulator_api_url if not is_mock_mode() else 'Internal Mock'}")
    st.info(f"Analytics API: {cfg.analytics_api_url if not is_mock_mode() else 'Internal Mock'}")

    st.divider()

    st.subheader("🗄️ MongoDB")
    st.text_input("Connection URI", cfg.mongo_uri, type="password", help="MongoDB connection string")
    st.text_input("Database", cfg.mongo_db, help="MongoDB database name")
    st.text_input("Alerts Collection", cfg.mongo_alerts_collection, help="Collection name for alerts")
    st.text_input("Analytics Collection", cfg.mongo_analytics_collection, help="Collection name for analytics data")
    st.divider()

    # Connection status indicators
    st.subheader("📊 Status")
    st.caption(f"✅ Configuration loaded from application.yml")
    st.caption(f"🔄 Auto-refresh: Enabled")

# Main content tabs
tab_data, tab_analytics, tab_alerts = st.tabs(["📡 Simulator Monitor", "📊 Analytics Monitor", "🚨 Alerts Monitor", ])

with tab_data:
    render_simulator_tab(
        service=st.session_state.simulator_service
    )

with tab_analytics:
    render_analytics_tab(
        service=st.session_state.analytics_service,
        refresh_default=cfg.refresh_seconds_default,
        limit_default=cfg.analytics_limit_default
    )

with tab_alerts:
    render_alerts_tab(
        service=st.session_state.alerts_service,
        refresh_default=cfg.refresh_seconds_default,
        limit_default=cfg.alerts_limit_default,
    )

# Footer
st.divider()
st.caption("🚀 IoT Dashboard v3.0 - Powered by Streamlit")
