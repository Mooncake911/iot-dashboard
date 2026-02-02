"""Shared mock data generators for dashboard and tests."""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

RULE_IDS = [
    "LOW_BATTERY",
    "HIGH_TEMPERATURE",
    "SUSTAINED_LOW_SIGNAL",
    "RAPID_BATTERY_DRAIN",
    "SIGNAL_LOSS"
]

SEVERITIES = ["INFO", "WARNING", "CRITICAL"]

MESSAGES = {
    "LOW_BATTERY": "Battery level below threshold",
    "HIGH_TEMPERATURE": "Temperature exceeds safe limits",
    "SUSTAINED_LOW_SIGNAL": "Signal strength critically low",
    "RAPID_BATTERY_DRAIN": "Battery draining faster than normal",
    "SIGNAL_LOSS": "Complete signal loss detected"
}


def generate_fake_alert(index: int, now: datetime) -> Dict[str, Any]:
    """Generate a single fake alert document."""
    rule_id = random.choice(RULE_IDS)
    severity = random.choice(SEVERITIES)
    device_id = random.randint(1, 100)

    # Generate timestamp going backwards
    timestamp = now - timedelta(minutes=index * 5)

    return {
        "_id": f"mock_{index:03d}",
        "ruleId": rule_id,
        "severity": severity,
        "deviceId": device_id,
        "message": MESSAGES.get(rule_id, "Unknown alert"),
        "receivedAt": timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "value": round(random.uniform(0, 100), 2),
        "threshold": round(random.uniform(50, 90), 2)
    }


def generate_fake_alerts_list(limit: int) -> List[Dict[str, Any]]:
    """Generate a list of fake alerts."""
    alerts = []
    now = datetime.now()

    for i in range(min(limit, 50)):
        alerts.append(generate_fake_alert(i, now))

    return alerts


def generate_fake_analytics_point(index: int, now: datetime) -> Dict[str, Any]:
    """Generate a single fake analytics document."""
    timestamp = now - timedelta(minutes=index)
    
    return {
        "_id": f"mock_analytics_{index:03d}",
        "deviceId": 1,
        "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "metrics": {
            "totalDevices": 50.0,
            "onlineDevices": 45.0 + random.randint(-5, 5),
            "coverageVolume": 1000.0,
            "battery": {
                "avg": round(random.uniform(50, 95) - index * 0.1, 2),
                "min": 20.0,
                "max": 100.0
            },
            "signal": {
                "avg": round(random.uniform(60, 90) + random.uniform(-5, 5), 2),
                "min": 10.0,
                "max": 95.0
            },
            "heartbeat": {
                "avg": round(random.uniform(0.5, 5.0), 2),
                "min": 0.0,
                "max": 10.0
            },
            "byType": {
                "SENSOR": 25.0,
                "ACTUATOR": 15.0,
                "GATEWAY": 10.0
            },
            "byManufacturer": {
                "ACME": 20.0,
                "GLOBEX": 30.0
            }
        }
    }


def generate_fake_analytics_list(limit: int) -> List[Dict[str, Any]]:
    """Generate a list of fake analytics history points."""
    points = []
    now = datetime.now()
    for i in range(limit):
        points.append(generate_fake_analytics_point(i, now))
    return points


def get_default_mock_config() -> Dict[str, Any]:
    """Get the default mock configuration for development and testing."""
    return {
        'dashboard': {
            'mock-mode': True,  # Default to True for mock config
            'services': {
                'simulator': {'url': 'http://mock-simulator:8080'},
                'analytics': {'url': 'http://mock-analytics:8081'}
            },
            'mongodb': {
                'uri': 'mongodb://mock:mock@localhost:27017/mock_db',
                'database': 'mock_db',
                'collections': {
                    'alerts': 'mock_alerts',
                    'analytics': 'mock_analytics'
                }
            },
            'ui': {
                'refresh-seconds-default': 5,
                'alerts-limit-default': 20
            }
        }
    }
