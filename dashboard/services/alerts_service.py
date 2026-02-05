from dashboard.core.repository import Repository
import logging

logger = logging.getLogger(__name__)


class AlertsService:
    def __init__(self, repository: Repository):
        self.repository = repository

    def get_alerts(self, limit: int = 50) -> list:
        return self.repository.fetch_data(limit)
