import pytest
from unittest.mock import MagicMock, patch
from dashboard.services.simulator_service import SimulatorService
from dashboard.services.analytics_service import AnalyticsService
from dashboard.services.alerts_service import AlertsService
from dashboard.core.client import ApiClient

@pytest.fixture
def mock_client():
    return MagicMock(spec=ApiClient)

class TestSimulatorService:
    def test_get_status(self, mock_client):
        mock_client.get.return_value = {"running": True}
        service = SimulatorService(mock_client)
        
        status = service.get_status()
        
        assert status == {"running": True}
        mock_client.get.assert_called_once_with("/api/simulator/status")

    def test_toggle_simulator(self, mock_client):
        mock_client.post.return_value = True
        service = SimulatorService(mock_client)
        
        result = service.toggle_simulator(False)
        
        assert result is True
        mock_client.post.assert_called_once_with("/api/simulator/start")

    def test_update_config(self, mock_client):
        mock_client.post.return_value = True
        service = SimulatorService(mock_client)
        
        service.update_config(10, 5)
        
        mock_client.post.assert_called_once_with(
            "/api/simulator/config", 
            params={"deviceCount": 10, "messagesPerSecond": 5}
        )

class TestAnalyticsService:
    def test_get_status(self, mock_client):
        mock_client.get.return_value = {"method": "Flowable"}
        # Pass None for repo as it's not used in this test
        service = AnalyticsService(mock_client, MagicMock())
        
        status = service.get_status()
        
        assert status == {"method": "Flowable"}

    def test_update_config(self, mock_client):
        mock_client.post.return_value = True
        service = AnalyticsService(mock_client, MagicMock())
        
        service.update_config("Flowable", 100)
        
        mock_client.post.assert_called_once_with(
            "/api/analytics/config",
            params={"method": "Flowable", "batchSize": 100}
        )

    def test_get_history(self, mock_client):
        mock_repo = MagicMock()
        mock_repo.fetch_data.return_value = [{"id": 1}]
        
        service = AnalyticsService(mock_client, mock_repo)
        
        history = service.get_history(limit=10)
        
        assert history == [{"id": 1}]
        mock_repo.fetch_data.assert_called_once_with(10)

class TestAlertsService:
    def test_get_alerts(self):
        mock_repo = MagicMock()
        mock_repo.fetch_data.return_value = [{"id": "a1"}]
        
        service = AlertsService(mock_repo)
        
        alerts = service.get_alerts(limit=5)
        
        assert alerts == [{"id": "a1"}]
        mock_repo.fetch_data.assert_called_once_with(5)
