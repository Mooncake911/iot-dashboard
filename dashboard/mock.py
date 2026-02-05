"""Mock implementations for local development without external services."""

import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import logging
from dashboard.core.repository import Repository

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


class MockDataSource:
    """State holder for mock data."""
    def __init__(self):
        self.simulator = {
            "running": False,
            "deviceCount": 10,
            "messagesPerSecond": 5
        }
        self.analytics = {
            "running": False,
            "method": "SEQUENTIAL",
            "batchSize": 100
        }

    def toggle_simulator(self, run: bool):
        self.simulator["running"] = run
        return True

    def update_simulator_config(self, count: int, rate: int):
        self.simulator["deviceCount"] = count
        self.simulator["messagesPerSecond"] = rate
        return True

    def toggle_analytics(self, run: bool):
        self.analytics["running"] = run
        return True

    def update_analytics_config(self, method: str, batch: int):
        self.analytics["method"] = method
        self.analytics["batchSize"] = batch
        return True

# Global instance for state persistence across re-runs
_mock_source = MockDataSource()

def get_mock_source():
    return _mock_source


class MockMongoAlerts(Repository):
    """Mock MongoDB alerts generator for local development."""
    def __init__(self):
        self.db_name = "MOCK_DB"
        self.collection_name = "MOCK_ALERTS"

    def fetch_data(self, limit: int) -> List[Dict[str, Any]]:
        """Generate fake alerts for display."""
        return [
            {
                "ruleId": "RULE_001",
                "severity": "critical",
                "message": "High temperature detected",
                "deviceId": "SENSOR_01",
                "timestamp": datetime.now().isoformat()
            },
            {
                 "ruleId": "RULE_002",
                 "severity": "warning",
                 "message": "Low battery",
                 "deviceId": "SENSOR_02",
                 "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat()
             }
        ][:limit]


class MockMongoAnalytics(Repository):
    """Mock MongoDB analytics generator for local development."""
    def __init__(self):
        self.db_name = "MOCK_DB"
        self.collection_name = "MOCK_ANALYTICS"

    def fetch_data(self, limit: int) -> List[Dict[str, Any]]:
        """Generate fake analytics history for display."""
        # Simple mock data generation inline to avoid external deps if file missing
        current_time = datetime.now()
        data = []
        for i in range(limit):
            t = current_time - timedelta(seconds=i*5)
            data.append({
                "timestamp": t.isoformat(),
                "metrics": {
                    "battery": {"avg": 50 + (i % 20)},
                    "signal": {"avg": 80 - (i % 10)},
                    "onlineDevices": 42,
                    "totalDevices": 50
                }
            })
        return data


def get_mock_config() -> Dict[str, Any]:
    """Get a mock configuration for local development."""
    from dashboard.mock_data import get_default_mock_config
    return get_default_mock_config()
