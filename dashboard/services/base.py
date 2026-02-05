from dashboard.core.client import ApiClient
import logging

logger = logging.getLogger(__name__)


class BaseService:
    def __init__(self, api_client: ApiClient):
        self.client = api_client

    def _get(self, path: str) -> dict:
        """Helper to make GET requests."""
        return self.client.get(path)

    def _post(self, path: str, **kwargs) -> bool:
        """Helper to make POST requests."""
        return self.client.post(path, **kwargs)
