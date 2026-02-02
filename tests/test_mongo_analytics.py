"""Tests for MongoDB analytics module."""

import pytest
from unittest.mock import MagicMock, patch

from dashboard.mongo.analytics import fetch_analytics_history

@pytest.fixture
def sample_analytics():
    """Sample analytics documents for testing."""
    return [
        {
            "_id": "65a1234567890abcdef12345",
            "deviceId": 1,
            "timestamp": "2026-02-02T04:00:00.000Z",
            "metrics": {"onlineDevices": 45, "totalDevices": 50}
        },
        {
            "_id": "65a1234567890abcdef12346",
            "deviceId": 1,
            "timestamp": "2026-02-02T04:05:00.000Z",
            "metrics": {"onlineDevices": 46, "totalDevices": 50}
        }
    ]

class TestFetchAnalyticsHistory:
    """Test fetching analytics history from MongoDB."""

    def test_fetch_analytics_success(self, sample_analytics):
        """Test successfully fetching analytics history."""
        with patch('dashboard.mongo.analytics.get_mongo_client') as mock_get_client:
            mock_client = MagicMock()
            mock_db = MagicMock()
            mock_collection = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.__getitem__.return_value = mock_db
            mock_db.__getitem__.return_value = mock_collection
            
            mock_cursor = MagicMock()
            mock_cursor.limit.return_value = mock_cursor
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.__iter__.return_value = iter(sample_analytics)
            mock_collection.find.return_value = mock_cursor
            
            result = fetch_analytics_history(
                "mongodb://localhost:27017",
                "test_db",
                "analytics",
                10
            )
            
            assert len(result) == 2
            assert all(isinstance(doc['_id'], str) for doc in result)
            assert result[0]["timestamp"] == "2026-02-02T04:00:00.000Z"

    def test_fetch_analytics_empty_on_error(self):
        """Test returning empty list on MongoDB error."""
        with patch('dashboard.mongo.analytics.get_mongo_client') as mock_get_client:
            mock_get_client.side_effect = Exception("Connection failed")
            
            result = fetch_analytics_history(
                "mongodb://localhost:27017",
                "test_db",
                "analytics",
                10
            )
            
            assert result == []

    def test_fetch_analytics_mock_mode(self, monkeypatch):
        """Test fetching analytics in mock mode."""
        monkeypatch.setenv("MOCK_MODE", "true")
        from dashboard.mock import set_mock_mode
        set_mock_mode(True)
        
        with patch('dashboard.mock.MockMongoAnalytics.fetch_analytics_history') as mock_fetch:
            mock_fetch.return_value = [{"mock": "data"}]
            
            result = fetch_analytics_history(
                "mongodb://localhost:27017",
                "test_db",
                "analytics",
                10
            )
            
            assert result == [{"mock": "data"}]
            mock_fetch.assert_called_once()
