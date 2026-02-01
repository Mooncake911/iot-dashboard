"""Pytest configuration and fixtures for dashboard tests."""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_config_data():
    """Sample configuration data for testing."""
    from dashboard.mock_data import get_default_mock_config

    config = get_default_mock_config()
    # Override mock-mode for standard tests (we usually want to test non-mock behavior unless specified)
    config['dashboard']['mock-mode'] = False
    # Use 'test-' prefix for URLs to distinguish from runtime mocks if needed, 
    # though technically not strictly required if we mock the calls anyway.
    # Leaving them close to the original for consistency with existing tests.
    config['dashboard']['services']['simulator']['url'] = 'http://test-simulator:8080'
    config['dashboard']['services']['analytics']['url'] = 'http://test-analytics:8081'
    config['dashboard']['services']['controller']['url'] = 'http://test-controller:8082'

    # Override MongoDB settings to match test expectations
    config['dashboard']['mongodb']['uri'] = 'mongodb://test:test@localhost:27017/test_db'
    config['dashboard']['mongodb']['database'] = 'test_db'
    config['dashboard']['mongodb']['collections']['alerts'] = 'test_alerts'

    # Override UI settings to match test expectations
    config['dashboard']['ui']['alerts-limit-default'] = 100

    return config


@pytest.fixture
def mock_mongo_client():
    """Mock MongoDB client for testing."""
    client = MagicMock()
    db = MagicMock()
    collection = MagicMock()

    client.__getitem__.return_value = db
    db.__getitem__.return_value = collection

    return client


@pytest.fixture
def sample_alerts():
    """Sample alert documents for testing."""
    from dashboard.mock_data import generate_fake_alert
    from datetime import datetime

    now = datetime(2026, 1, 12, 12, 5, 0)
    return [
        generate_fake_alert(1, now),
        generate_fake_alert(0, now)
    ]


@pytest.fixture(autouse=True)
def reset_mongo_client_state():
    """Reset the MongoDB client global state before each test."""
    import dashboard.mongo_alerts as mongo_module

    # Reset global state
    mongo_module._mongo_client = None
    mongo_module._mongo_uri = None

    yield

    # Cleanup after a test
    mongo_module._mongo_client = None
    mongo_module._mongo_uri = None
