"""Tests for MongoDB alerts module."""

import pytest
from unittest.mock import MagicMock, patch
from pymongo.errors import ConnectionFailure

from dashboard.mongo.alerts import get_mongo_client, fetch_alerts, close_mongo_client


class TestMongoClient:
    """Test MongoDB client management."""
    
    def test_get_mongo_client_creates_new(self):
        """Test creating a new MongoDB client."""
        with patch('dashboard.mongo.alerts.MongoClient') as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance
            
            client = get_mongo_client("mongodb://localhost:27017")
            
            mock_client_class.assert_called_once_with(
                "mongodb://localhost:27017",
                serverSelectionTimeoutMS=3000
            )
            assert client == mock_instance
    
    def test_get_mongo_client_reuses_existing(self):
        """Test reusing existing MongoDB client."""
        with patch('dashboard.mongo.alerts.MongoClient') as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance
            
            # The first call creates the client
            client1 = get_mongo_client("mongodb://localhost:27017")
            # Second call with same URI reuses client
            client2 = get_mongo_client("mongodb://localhost:27017")
            
            # Should only create once
            assert mock_client_class.call_count == 1
            assert client1 == client2
    
    def test_get_mongo_client_recreates_on_uri_change(self):
        """Test recreating client when URI changes."""
        with patch('dashboard.mongo.alerts.MongoClient') as mock_client_class:
            mock_instance1 = MagicMock()
            mock_instance2 = MagicMock()
            mock_client_class.side_effect = [mock_instance1, mock_instance2]
            
            # First call
            client1 = get_mongo_client("mongodb://localhost:27017")
            # Second call with a different URI
            client2 = get_mongo_client("mongodb://other:27017")
            
            # Should create twice and close first
            assert mock_client_class.call_count == 2
            mock_instance1.close.assert_called_once()
    
    def test_close_mongo_client(self):
        """Test closing MongoDB client."""
        with patch('dashboard.mongo.alerts.MongoClient') as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance
            
            get_mongo_client("mongodb://localhost:27017")
            close_mongo_client()
            
            mock_instance.close.assert_called_once()


class TestFetchAlerts:
    """Test fetching alerts from MongoDB."""
    
    def test_fetch_alerts_success(self, sample_alerts):
        """Test successfully fetching alerts."""
        with patch('dashboard.mongo.alerts.get_mongo_client') as mock_get_client:
            mock_client = MagicMock()
            mock_db = MagicMock()
            mock_collection = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.__getitem__.return_value = mock_db
            mock_db.__getitem__.return_value = mock_collection
            
            # Setup collection mock
            mock_collection.estimated_document_count.return_value = 2
            mock_collection.find_one.return_value = sample_alerts[0]
            
            mock_cursor = MagicMock()
            mock_cursor.__iter__.return_value = iter(sample_alerts)
            mock_collection.find.return_value.sort.return_value = mock_cursor
            
            # Fetch alerts
            result = fetch_alerts(
                "mongodb://localhost:27017",
                "test_db",
                "alerts",
                10
            )
            
            assert len(result) == 2
            assert all(isinstance(alert['_id'], str) for alert in result)
    
    def test_fetch_alerts_empty_collection(self):
        """Test fetching from an empty collection."""
        with patch('dashboard.mongo.alerts.get_mongo_client') as mock_get_client:
            mock_client = MagicMock()
            mock_db = MagicMock()
            mock_collection = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.__getitem__.return_value = mock_db
            mock_db.__getitem__.return_value = mock_collection
            
            mock_collection.estimated_document_count.return_value = 0
            mock_cursor = MagicMock()
            mock_cursor.__iter__.return_value = iter([])
            mock_collection.find.return_value.sort.return_value = mock_cursor
            
            result = fetch_alerts(
                "mongodb://localhost:27017",
                "test_db",
                "alerts",
                10
            )
            
            assert result == []
    
    def test_fetch_alerts_connection_failure(self):
        """Test handling connection failure."""
        with patch('dashboard.mongo.alerts.get_mongo_client') as mock_get_client:
            mock_get_client.side_effect = ConnectionFailure("Connection failed")
            
            with pytest.raises(ConnectionFailure):
                fetch_alerts(
                    "mongodb://localhost:27017",
                    "test_db",
                    "alerts",
                    10
                )
    
    def test_fetch_alerts_auto_detect_sort_field(self, sample_alerts):
        """Test automatic sort field detection."""
        with patch('dashboard.mongo.alerts.get_mongo_client') as mock_get_client:
            mock_client = MagicMock()
            mock_db = MagicMock()
            mock_collection = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.__getitem__.return_value = mock_db
            mock_db.__getitem__.return_value = mock_collection
            
            # Sample without receivedAt should use alertTimestamp
            sample_without_received = {
                '_id': '123',
                'alertTimestamp': '2026-01-12T12:00:00Z',
                'ruleId': 'TEST'
            }
            
            mock_collection.estimated_document_count.return_value = 1
            mock_collection.find_one.return_value = sample_without_received
            
            mock_cursor = MagicMock()
            mock_cursor.__iter__.return_value = iter([sample_without_received])
            mock_find = mock_collection.find.return_value
            mock_find.sort.return_value = mock_cursor
            
            result = fetch_alerts(
                "mongodb://localhost:27017",
                "test_db",
                "alerts",
                10
            )
            
            # Verify sort was called (field detection happened)
            mock_find.sort.assert_called_once()
