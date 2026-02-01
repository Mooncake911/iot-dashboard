"""Mock implementations for local development without external services."""

import os
from typing import Any, Dict, List

# Global state for mock mode
_mock_active: bool = False


def set_mock_mode(enabled: bool):
    """Explicitly set mock mode state from configuration."""
    global _mock_active
    _mock_active = enabled


def is_mock_mode() -> bool:
    """
    Check if mock mode is enabled.
    Checks environment variable MOCK_MODE first, then internal global state.
    """
    # 1. Check environment variable (highest priority for overrides)
    env_mock = os.getenv("MOCK_MODE", "").lower()
    if env_mock in ("true", "1", "yes"):
        return True

    # 2. Check explicitly set state (from config)
    return _mock_active


class MockHTTPClient:
    """Mock HTTP client that returns fake responses for API calls."""

    # Simulated state
    _simulator_running = False
    _analytics_running = False
    _simulator_config = {"deviceCount": 10, "messagesPerSecond": 5}
    _analytics_config = {"method": "SEQUENTIAL", "batchSize": 100}

    @staticmethod
    def _parse_params(url: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters from both kwargs and URL query string."""
        params = kwargs.get("params", {}).copy() if kwargs.get("params") else {}

        if "?" in url:
            from urllib.parse import parse_qs, urlparse
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)

            for key, values in query_params.items():
                # parse_qs returns a list of values, take the first one
                if values:
                    params[key] = values[0]

        return params

    @classmethod
    def request(cls, method: str, url: str, timeout: int = 10, **kwargs) -> Dict[str, Any]:
        """Mock HTTP request that returns fake responses based on URL."""

        # Simulator endpoints
        if "/simulator/status" in url:
            return {
                "status": 200,
                "body": {
                    "running": cls._simulator_running,
                    "deviceCount": cls._simulator_config["deviceCount"],
                    "messagesPerSecond": cls._simulator_config["messagesPerSecond"]
                },
                "url": url
            }

        elif "/simulator/config" in url:
            # Extract query parameters from kwargs or URL
            params = cls._parse_params(url, kwargs)

            if "deviceCount" in params:
                try:
                    cls._simulator_config["deviceCount"] = int(params["deviceCount"])
                except (ValueError, TypeError):
                    pass

            if "messagesPerSecond" in params:
                try:
                    cls._simulator_config["messagesPerSecond"] = int(params["messagesPerSecond"])
                except (ValueError, TypeError):
                    pass

            return {
                "status": 200,
                "body": {"message": "Simulator configured successfully (MOCK)"},
                "url": url
            }

        elif "/simulator/start" in url:
            cls._simulator_running = True
            return {
                "status": 200,
                "body": {"message": "Simulator started (MOCK)"},
                "url": url
            }

        elif "/simulator/stop" in url:
            cls._simulator_running = False
            return {
                "status": 200,
                "body": {"message": "Simulator stopped (MOCK)"},
                "url": url
            }

        # Analytics endpoints
        elif "/analytics/status" in url:
            return {
                "status": 200,
                "body": {
                    "method": cls._analytics_config["method"],
                    "batchSize": cls._analytics_config["batchSize"],
                    "running": cls._analytics_running
                },
                "url": url
            }

        elif "/analytics/config" in url:
            params = cls._parse_params(url, kwargs)

            if "method" in params:
                cls._analytics_config["method"] = params["method"]
            if "batchSize" in params:
                try:
                    cls._analytics_config["batchSize"] = int(params["batchSize"])
                except (ValueError, TypeError):
                    pass

            return {
                "status": 200,
                "body": {"message": "Analytics configured successfully (MOCK)"},
                "url": url
            }

        elif "/analytics/start" in url:
            cls._analytics_running = True
            return {
                "status": 200,
                "body": {"message": "Analytics started (MOCK)"},
                "url": url
            }

        elif "/analytics/stop" in url:
            cls._analytics_running = False
            return {
                "status": 200,
                "body": {"message": "Analytics stopped (MOCK)"},
                "url": url
            }

        # Default response
        return {
            "status": 200,
            "body": {"message": "Mock response", "url": url},
            "url": url
        }


class MockMongoAlerts:
    """Mock MongoDB alerts generator for local development."""

    @classmethod
    def fetch_alerts(cls, mongo_uri: str, mongo_db: str, collection: str, limit: int) -> List[Dict[str, Any]]:
        """Generate fake alerts for display."""
        from dashboard.mock_data import generate_fake_alerts_list
        return generate_fake_alerts_list(limit)

    @classmethod
    def close_mongo_client(cls):
        """Mock close - does nothing."""
        pass


class MockMongoAnalytics:
    """Mock MongoDB analytics generator for local development."""

    @classmethod
    def fetch_analytics_history(cls, mongo_uri: str, mongo_db: str, collection: str, limit: int) -> List[Dict[str, Any]]:
        """Generate fake analytics history for display."""
        from dashboard.mock_data import generate_fake_analytics_list
        return generate_fake_analytics_list(limit)


def get_mock_config() -> Dict[str, Any]:
    """Get a mock configuration for local development."""
    from dashboard.mock_data import get_default_mock_config
    return get_default_mock_config()
