"""Tests for configuration loading module."""

import tempfile
from pathlib import Path

import pytest
import yaml

from dashboard.config import (
    _resolve_env_placeholder,
    _resolve_env_in_dict,
    _load_yaml_config,
    load_config
)


class TestEnvPlaceholderResolution:
    """Test environment variable placeholder resolution."""

    def test_resolve_simple_placeholder(self, monkeypatch):
        """Test resolving ${VAR} format."""
        monkeypatch.setenv("TEST_VAR", "test_value")
        result = _resolve_env_placeholder("${TEST_VAR}")
        assert result == "test_value"

    def test_resolve_placeholder_with_default(self, monkeypatch):
        """Test resolving ${VAR:default} format."""
        monkeypatch.delenv("MISSING_VAR", raising=False)
        result = _resolve_env_placeholder("${MISSING_VAR:default_value}")
        assert result == "default_value"

    def test_resolve_placeholder_without_default(self, monkeypatch):
        """Test resolving ${VAR} when a variable is missing."""
        monkeypatch.delenv("MISSING_VAR", raising=False)
        result = _resolve_env_placeholder("${MISSING_VAR}")
        assert result == ""

    def test_resolve_mixed_string(self, monkeypatch):
        """Test resolving string with multiple placeholders."""
        monkeypatch.setenv("HOST", "localhost")
        monkeypatch.setenv("PORT", "8080")
        result = _resolve_env_placeholder("http://${HOST}:${PORT}/api")
        assert result == "http://localhost:8080/api"

    def test_non_string_passthrough(self):
        """Test that non-string values pass through unchanged."""
        assert _resolve_env_placeholder(123) == 123
        assert _resolve_env_placeholder(None) is None


class TestDictResolution:
    """Test recursive dictionary resolution."""

    def test_resolve_nested_dict(self, monkeypatch):
        """Test resolving nested dictionary with placeholders."""
        monkeypatch.setenv("DB_HOST", "mongodb")
        monkeypatch.setenv("DB_PORT", "27017")

        data = {
            'database': {
                'host': '${DB_HOST}',
                'port': '${DB_PORT:27017}',
                'name': 'test_db'
            }
        }

        result = _resolve_env_in_dict(data)
        assert result['database']['host'] == 'mongodb'
        assert result['database']['port'] == '27017'
        assert result['database']['name'] == 'test_db'


class TestYAMLLoading:
    """Test YAML configuration file loading."""

    def test_load_existing_yaml(self, mock_config_data):
        """Test loading valid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(mock_config_data, f)
            temp_path = f.name

        try:
            result = _load_yaml_config(temp_path)
            assert result == mock_config_data
        finally:
            Path(temp_path).unlink()

    def test_load_nonexistent_yaml(self):
        """Test loading non-existent file returns empty dict."""
        result = _load_yaml_config("nonexistent.yml")
        assert result == {}

    def test_load_invalid_yaml(self):
        """Test loading invalid YAML returns empty dict."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name

        try:
            result = _load_yaml_config(temp_path)
            assert result == {}
        finally:
            Path(temp_path).unlink()


class TestConfigLoading:
    """Test full configuration loading."""

    def test_load_config_with_defaults(self, mock_config_data):
        """Test loading configuration with default values."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(mock_config_data, f)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert config.mock_mode is False
            assert config.simulator_api_url == 'http://test-simulator:8080'
            assert config.analytics_api_url == 'http://test-analytics:8081'
            assert config.controller_api_url == 'http://test-controller:8082'
            assert config.mongo_uri == 'mongodb://test:test@localhost:27017/test_db'
            assert config.mongo_db == 'test_db'
            assert config.mongo_alerts_collection == 'test_alerts'
            assert config.refresh_seconds_default == 5
            assert config.alerts_limit_default == 100
        finally:
            Path(temp_path).unlink()

    def test_load_config_with_env_override(self, mock_config_data, monkeypatch):
        """Test environment variables override YAML values."""
        monkeypatch.setenv("SIMULATOR_API_URL", "http://override:9999")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            # Add a placeholder to YAML
            mock_config_data['dashboard']['services']['simulator']['url'] = '${SIMULATOR_API_URL:http://default:8080}'
            yaml.dump(mock_config_data, f)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert config.simulator_api_url == 'http://override:9999'
        finally:
            Path(temp_path).unlink()

    def test_load_config_missing_file_raises_error(self):
        """Test loading with a missing file raises ValueError."""
        with pytest.raises(ValueError, match="Configuration file .* is missing or invalid"):
            load_config("nonexistent.yml")

    def test_load_config_missing_dashboard_section(self):
        """Test loading with a missing dashboard section raises KeyError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump({'other': 'data'}, f)
            temp_path = f.name

        try:
            with pytest.raises(KeyError, match="Missing 'dashboard' section"):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_config_missing_services_section(self):
        """Test loading with a missing services section raises KeyError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump({'dashboard': {'mongodb': {}, 'ui': {}}}, f)
            temp_path = f.name

        try:
            with pytest.raises(KeyError, match="Missing 'dashboard.services' section"):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_config_missing_service_url(self):
        """Test loading with a missing service URL raises KeyError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            config_data = {
                'dashboard': {
                    'services': {
                        'simulator': {'url': 'http://test:8080'},
                        'analytics': {},  # Missing URL
                        'controller': {'url': 'http://test:8082'}
                    },
                    'mongodb': {
                        'uri': 'mongodb://test',
                        'database': 'test_db',
                        'collections': {'alerts': 'alerts'}
                    },
                    'ui': {
                        'refresh-seconds-default': 2,
                        'alerts-limit-default': 50
                    }
                }
            }
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            with pytest.raises(KeyError, match="Missing service URLs"):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_config_missing_mongodb_config(self):
        """Test loading with a missing MongoDB configuration raises KeyError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            config_data = {
                'dashboard': {
                    'services': {
                        'simulator': {'url': 'http://test:8080'},
                        'analytics': {'url': 'http://test:8081'},
                        'controller': {'url': 'http://test:8082'}
                    },
                    'mongodb': {
                        'uri': 'mongodb://test',
                        # Missing database and collections
                    },
                    'ui': {
                        'refresh-seconds-default': 2,
                        'alerts-limit-default': 50
                    }
                }
            }
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            with pytest.raises(KeyError, match="Missing MongoDB configuration"):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_config_invalid_ui_values(self):
        """Test loading with invalid UI configuration values raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            config_data = {
                'dashboard': {
                    'services': {
                        'simulator': {'url': 'http://test:8080'},
                        'analytics': {'url': 'http://test:8081'},
                        'controller': {'url': 'http://test:8082'}
                    },
                    'mongodb': {
                        'uri': 'mongodb://test',
                        'database': 'test_db',
                        'collections': {'alerts': 'alerts'}
                    },
                    'ui': {
                        'refresh-seconds-default': 'not_a_number',  # Invalid
                        'alerts-limit-default': 50
                    }
                }
            }
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid UI configuration values"):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_config_mock_mode_enabled(self):
        """Test loading configuration with mock mode enabled."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump({
                'dashboard': {
                    'mock-mode': True,
                    'services': {},  # Can be empty in mock mode
                    'mongodb': {},
                    'ui': {'refresh-seconds-default': 5, 'alerts-limit-default': 10}
                }
            }, f)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert config.mock_mode is True
            # Should not raise error for missing services
        finally:
            Path(temp_path).unlink()

    def test_mock_mode_env_var_priority(self, monkeypatch):
        """Test environment variable overrides config for mock mode (indirectly via is_mock_mode logic)."""
        # Note: load_config uses is_mock_mode() internally which checks finding MOCK_MODE env var
        # If MOCK_MODE env is set, load_config calls get_mock_config() directly
        monkeypatch.setenv("MOCK_MODE", "true")

        # Even with missing/invalid file, should succeed because it switches to mock config
        config = load_config("nonexistent.yml")
        assert config.mock_mode is True
        assert config.simulator_api_url == 'http://mock-simulator:8080'
