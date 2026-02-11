"""Tests for MongoDB alerts repository."""

import pytest
from pymongo import MongoClient
from unittest.mock import MagicMock, patch
from dashboard.mongo.alerts import MongoAlertsRepository


@pytest.fixture
def sample_alerts():
    return [
        {"_id": "1", "receivedAt": "2023-01-01", "message": "Alert 1"},
        {"_id": "2", "receivedAt": "2023-01-02", "message": "Alert 2"}
    ]


class TestMongoAlertsRepository:
    def test_fetch_alerts_success(self, sample_alerts):
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()

        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection

        mock_cursor = MagicMock()
        mock_cursor.__iter__.return_value = iter(sample_alerts)
        mock_collection.find.return_value.sort.return_value = mock_cursor

        repo = MongoAlertsRepository(mock_client, "db", "collection")
        result = repo.fetch_data(limit=10)

        assert len(result) == 2
        assert all(isinstance(alert['_id'], str) for alert in result)

    def test_fetch_alerts_error(self):
        mock_client = MagicMock()
        # Simulate error when accessing collection or finding
        mock_client.__getitem__.side_effect = Exception("Connection failed")

        repo = MongoAlertsRepository(mock_client, "db", "collection")
        result = repo.fetch_data(limit=10)

        assert result == []
