"""Unit tests for dashboard.mock module."""

import os
from unittest.mock import patch

from dashboard.mock import is_mock_mode, MockHTTPClient, set_mock_mode


class TestMockMode:
    """Tests for mock mode detection logic."""

    def test_mock_mode_env_var(self):
        """Test is_mock_mode returns True when env var is set."""
        with patch.dict(os.environ, {"MOCK_MODE": "true"}):
            assert is_mock_mode() is True

        with patch.dict(os.environ, {"MOCK_MODE": "1"}):
            assert is_mock_mode() is True

        with patch.dict(os.environ, {"MOCK_MODE": "yes"}):
            assert is_mock_mode() is True

    def test_mock_mode_env_var_false(self):
        """Test is_mock_mode returns False when env var is false/unset."""
        with patch.dict(os.environ, {"MOCK_MODE": "false"}):
            # Ensure global state is also false
            set_mock_mode(False)
            assert is_mock_mode() is False

        with patch.dict(os.environ, {}, clear=True):
            set_mock_mode(False)
            assert is_mock_mode() is False

    def test_mock_mode_global_state(self):
        """Test is_mock_mode checks global state when env var is unset."""
        with patch.dict(os.environ, {}, clear=True):
            set_mock_mode(True)
            assert is_mock_mode() is True

            set_mock_mode(False)
            assert is_mock_mode() is False


class TestMockHTTPClient:
    """Tests for MockHTTPClient logic."""

    def test_parse_params_from_kwargs(self):
        """Test parsing parameters from kwargs."""
        url = "http://test/api/config"
        kwargs = {"params": {"key": "value", "num": 123}}

        params = MockHTTPClient._parse_params(url, kwargs)
        assert params["key"] == "value"
        assert params["num"] == 123

    def test_parse_params_from_url(self):
        """Test parsing parameters from URL query string."""
        url = "http://test/api/config?key=value&num=123"
        kwargs = {}

        params = MockHTTPClient._parse_params(url, kwargs)
        assert params["key"] == "value"
        # Note: parse_qs returns strings
        assert params["num"] == "123"

    def test_parse_params_mixed(self):
        """Test parsing parameters from both URL and kwargs (kwargs check first - but logic copies params then adds from URL, so URL might overwrite if keys clash, let's check impl)."""
        # Implementation: params = kwargs... then for a key in url_params: params[key] = val
        # So URL params overwrite kwargs params in the current implementation

        url = "http://test/api/config?url_param=abc&shared=url_value"
        kwargs = {"params": {"kwargs_param": 123, "shared": "kwargs_value"}}

        params = MockHTTPClient._parse_params(url, kwargs)
        assert params["kwargs_param"] == 123
        assert params["url_param"] == "abc"
        assert params["shared"] == "url_value"

    def test_simulator_config_update(self):
        """Test simulator config update via URL params."""
        # Reset state
        MockHTTPClient._simulator_config = {"deviceCount": 10, "messagesPerSecond": 5}

        url = "http://test/api/simulator/config?deviceCount=50&messagesPerSecond=20"
        response = MockHTTPClient.request("POST", url)

        assert response["status"] == 200
        assert MockHTTPClient._simulator_config["deviceCount"] == 50
        assert MockHTTPClient._simulator_config["messagesPerSecond"] == 20

    def test_analytics_config_update(self):
        """Test analytics config update via URL params."""
        # Reset state
        MockHTTPClient._analytics_config = {"method": "SEQUENTIAL", "batchSize": 100}

        url = "http://test/api/analytics/config?method=BATCH&batchSize=500"
        response = MockHTTPClient.request("POST", url)

        assert response["status"] == 200
        assert MockHTTPClient._analytics_config["method"] == "BATCH"
        assert MockHTTPClient._analytics_config["batchSize"] == 500
