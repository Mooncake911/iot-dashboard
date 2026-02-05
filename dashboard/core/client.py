from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import requests
import logging

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
    
    def __init__(self):
        from dashboard.mock import get_mock_source
        self.source = get_mock_source()

    def get(self, path: str) -> Dict[str, Any]:
        # Mapping path -> data source
        if "simulator/status" in path:
            return self.source.simulator
        if "analytics/status" in path:
            return self.source.analytics
        return {}

    def post(self, path: str, json: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> bool:
        # Mapping path -> action
        params = params or {}
        
        if "simulator/start" in path:
            return self.source.toggle_simulator(True)
        if "simulator/stop" in path:
            return self.source.toggle_simulator(False)
        if "simulator/config" in path:
            return self.source.update_simulator_config(
                int(params.get("deviceCount", 10)),
                int(params.get("messagesPerSecond", 1))
            )
            
        if "analytics/config" in path:
            return self.source.update_analytics_config(
                params.get("method", "SEQUENTIAL"),
                int(params.get("batchSize", 20))
            )
            
        return True
