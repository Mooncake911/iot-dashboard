import streamlit as st
import logging

from dashboard.config import load_config
from dashboard.ui import AlertsTab, SimulatorTab, AnalyticsServiceTab
from dashboard.ui.utils.styles import apply_custom_styles
from dashboard.factory import DashboardFactory

# --- 1. CONFIGURATION & LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="IoT Dashboard",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --- 2. CACHED SERVICE INITIALIZATION ---
@st.cache_resource
def init_application_layer(cfg):
    """Инициализирует все клиенты, репозитории и сервисы через Factory."""
    return DashboardFactory.create_application_layer(cfg)


# --- 3. MAIN APP LOGIC ---
def main():
    apply_custom_styles()

    # Load config with error handling
    try:
        cfg = load_config()
    except Exception as e:
        st.error(f"❌ Critical Error: Failed to load configuration: {e}")
        st.stop()

    # Initialize Services (once)
    sim_svc, analytics_svc, alerts_svc = init_application_layer(cfg)

    # UI: Header
    st.title("🌐 IoT Dashboard")
    st.markdown(f"**Real-time monitoring for {('MOCK' if cfg.mock_mode else 'REAL')} environment**")

    # UI: Sidebar
    render_sidebar(cfg)

    # UI: Tabs
    tab_sim, tab_analytics, tab_alerts = st.tabs([
        "📡 Simulator Monitor",
        "📊 Analytics Monitor",
        "🚨 Alerts Monitor"
    ])

    with tab_sim:
        SimulatorTab(service=sim_svc).render()

    with tab_analytics:
        AnalyticsServiceTab(
            service=analytics_svc,
            refresh_default=cfg.refresh_seconds_default,
            limit_default=cfg.analytics_limit_default
        ).render()

    with tab_alerts:
        AlertsTab(
            service=alerts_svc,
            refresh_default=cfg.refresh_seconds_default,
            limit_default=cfg.alerts_limit_default,
        ).render()

    # Footer
    st.divider()
    st.caption(f"🚀 v3.0 | Status: Online | Mode: {'Mock' if cfg.mock_mode else 'Production'}")


# --- 4. UI COMPONENTS ---
def render_sidebar(cfg):
    with st.sidebar:
        st.header("⚙️ Configuration")

        from dashboard.mock import is_mock_mode
        if is_mock_mode():
            st.warning("⚠️ MOCK MODE ENABLED")

        with st.expander("🌐 API Endpoints", expanded=not cfg.mock_mode):
            st.info(f"Simulator: {cfg.simulator_api_url if not cfg.mock_mode else 'Mock'}")
            st.info(f"Analytics: {cfg.analytics_api_url if not cfg.mock_mode else 'Mock'}")

        with st.expander("🗄️ Database Info", expanded=False):
            st.text_input("URI", cfg.mongo_uri, type="password", disabled=True)
            st.text_input("Database", cfg.mongo_db, disabled=True)
            st.caption("ℹ️ DB settings are read-only (application.yml)")

        st.divider()
        st.subheader("📊 System Status")
        st.success("✅ Configuration Loaded")
        st.success("✅ Services Connected")


if __name__ == "__main__":
    main()
