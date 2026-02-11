import logging
from pymongo import MongoClient
from dashboard.config import DashboardConfig
from dashboard.mock import (
    MockMongoAlertsRepository,
    MockMongoAnalyticsRepository,
    set_mock_mode,
    get_mock_source,
)
from dashboard.core.client import RealApiClient, MockApiClient
from dashboard.mongo import MongoAlertsRepository, MongoAnalyticsRepository
from dashboard.services import SimulatorService, AnalyticsService, AlertsService

logger = logging.getLogger(__name__)


class DashboardFactory:
    """Factory to initialize clients, repositories, and services."""

    @staticmethod
    def create_application_layer(cfg: DashboardConfig):
        """Initializes all clients, repositories, and services based on config."""
        set_mock_mode(cfg.mock_mode)

        if cfg.mock_mode:
            logger.info("Initializing services in MOCK mode")

            sim_client = MockApiClient(get_mock_source())
            analytics_client = MockApiClient(get_mock_source())

            alerts_repo = MockMongoAlertsRepository()
            analytics_repo = MockMongoAnalyticsRepository()

        else:
            logger.info("Initializing services in REAL mode")
            client = MongoClient(cfg.mongo_uri, serverSelectionTimeoutMS=3000)

            sim_client = RealApiClient(cfg.simulator_api_url)
            analytics_client = RealApiClient(cfg.analytics_api_url)

            alerts_repo = MongoAlertsRepository(client, cfg.mongo_db, cfg.mongo_alerts_collection)
            analytics_repo = MongoAnalyticsRepository(client, cfg.mongo_db, cfg.mongo_analytics_collection)

        return (
            SimulatorService(sim_client),
            AnalyticsService(analytics_client, analytics_repo),
            AlertsService(alerts_repo)
        )
