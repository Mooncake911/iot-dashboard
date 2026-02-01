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


def get_default_mock_config() -> Dict[str, Any]:
    """Get the default mock configuration for development and testing."""
    return {
        'dashboard': {
            'mock-mode': True,  # Default to True for mock config
            'services': {
                'simulator': {'url': 'http://mock-simulator:8080'},
                'analytics': {'url': 'http://mock-analytics:8081'},
                'controller': {'url': 'http://mock-controller:8082'}
            },
            'mongodb': {
                'uri': 'mongodb://mock:mock@localhost:27017/mock_db',
                'database': 'mock_db',
                'collections': {'alerts': 'mock_alerts'}
            },
            'ui': {
                'refresh-seconds-default': 5,
                'alerts-limit-default': 20
            }
        }
    }
