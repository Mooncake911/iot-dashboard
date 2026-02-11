from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import requests
import logging

from dashboard.mock import MockDataSource

logger = logging.getLogger(__name__)


class ApiClient(ABC):
    """Abstract base class for API interactions."""

    @abstractmethod
    def get(self, path: str) -> Dict[str, Any]:
        """Execute a GET request."""
        pass

    @abstractmethod
    def post(self, path: str, json: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> bool:
        """Execute a POST request."""
        pass


class RealApiClient(ApiClient):
    """Implementation that uses Python requests to call a real HTTP API."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    def get(self, path: str) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.error(f"GET {url} failed: {e}")
        return {}

    def post(self, path: str, json: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> bool:
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            resp = requests.post(url, json=json, params=params, timeout=5)
            return resp.status_code in (200, 201)
        except Exception as e:
            logger.error(f"POST {url} failed: {e}")
            return False


class MockApiClient(ApiClient):
    """Implementation that interacts with the MockDataSource within the application."""

    def __init__(self, source: MockDataSource):
        self.source = source
        
        # Declarative route mapping
        self._get_routes = {
            "simulator/status": lambda: self.source.simulator,
            "analytics/status": lambda: self.source.analytics,
        }
        
    def get(self, path: str) -> Dict[str, Any]:
        path = path.lstrip('/')
        # Remove /api prefix if present
        if path.startswith("api/"):
            path = path[4:]
            
        handler = self._get_routes.get(path)
        if handler:
            return handler()
        
        logger.warning(f"Mock GET: No handler for path '{path}'")
        return {}

    def post(self, path: str, json: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> bool:
        path = path.lstrip('/')
        if path.startswith("api/"):
            path = path[4:]
            
        params = params or {}

        if path == "simulator/start":
            return self.source.toggle_simulator(True)
        if path == "simulator/stop":
            return self.source.toggle_simulator(False)
        if path == "simulator/config":
            return self.source.update_simulator_config(
                int(params.get("deviceCount", 10)),
                int(params.get("messagesPerSecond", 1))
            )
        if path == "analytics/config":
            return self.source.update_analytics_config(
                params.get("method", "SEQUENTIAL"),
                int(params.get("batchSize", 20))
            )

        logger.warning(f"Mock POST: No handler for path '{path}'")
        return True
