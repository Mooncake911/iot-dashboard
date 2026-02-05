from dashboard.services.base import BaseService
from dashboard.core.client import ApiClient
from dashboard.core.repository import Repository
import logging

logger = logging.getLogger(__name__)

class AnalyticsService(BaseService):
    def __init__(self, api_client: ApiClient, repository: Repository):
        super().__init__(api_client)
        self.repository = repository

    def get_status(self) -> dict:
        """Fetch analytics engine status."""
        return self._get("/api/analytics/status")

    def update_config(self, method: str, batch_size: int) -> bool:
        """Update analytics engine configuration."""
        return self._post(
            "/api/analytics/config",
            params={"method": method, "batchSize": batch_size}
        )

    def get_history(self, limit: int = 100) -> list:
        """Fetch analytics history."""
        return self.repository.fetch_data(limit)
