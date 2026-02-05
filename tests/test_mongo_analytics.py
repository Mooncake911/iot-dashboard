"""Tests for MongoDB analytics repository."""

import pytest
from unittest.mock import MagicMock, patch
from dashboard.mongo.analytics import MongoAnalyticsRepository


@pytest.fixture
def sample_analytics():
    return [
        {
            "_id": "65a1234567890abcdef12345",
            "deviceId": 1,
            "timestamp": "2026-02-02T04:00:00.000Z",
            "metrics": {"onlineDevices": 45, "totalDevices": 50}
        }
    ]


class TestMongoAnalyticsRepository:
    def test_fetch_history_success(self, sample_analytics):
        with patch('dashboard.mongo.base._get_shared_client') as mock_get_client:
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

            repo = MongoAnalyticsRepository("mongodb://uri", "db", "collection")
            result = repo.fetch_data(limit=10)

            assert len(result) == 1
            assert result[0]["timestamp"] == "2026-02-02T04:00:00.000Z"

    def test_fetch_history_error(self):
        with patch('dashboard.mongo.base._get_shared_client') as mock_get_client:
            mock_get_client.side_effect = Exception("Connection failed")

            repo = MongoAnalyticsRepository("mongodb://uri", "db", "collection")
            result = repo.fetch_data(limit=10)

            assert result == []
