import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from dashboard.mock import is_mock_mode, get_mock_config


@dataclass
class DashboardConfig:
    """Dashboard configuration with all service endpoints and settings."""
    mock_mode: bool
    simulator_api_url: str
    analytics_api_url: str
    mongo_uri: str
    mongo_db: str
    mongo_alerts_collection: str
    mongo_analytics_collection: str
    refresh_seconds_default: int
    alerts_limit_default: int
    analytics_limit_default: int


def _resolve_env_placeholder(value: str) -> str:
    """
    Resolve environment variable placeholders in format ${VAR_NAME: default_value}.
    
    Args:
        value: String that may contain placeholders
        
    Returns:
        Resolved string with environment variables substituted
    """
    if not isinstance(value, str):
        return value
    
    # Pattern: ${VAR_NAME:default_value} or ${VAR_NAME}
    pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
    
    def replacer(match):
        var_name = match.group(1)
        default_value = match.group(2) if match.group(2) is not None else ""
        return os.getenv(var_name, default_value)
    
    return re.sub(pattern, replacer, value)


def _resolve_env_in_dict(data: dict) -> dict:
    """
    Recursively resolve environment variable placeholders in a dictionary.
    
    Args:
        data: Dictionary potentially containing placeholders
        
    Returns:
        Dictionary with all placeholders resolved
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = _resolve_env_in_dict(value)
        elif isinstance(value, str):
            result[key] = _resolve_env_placeholder(value)
        else:
            result[key] = value
    return result


def _load_yaml_config(config_path: str) -> dict[str, Any]:
    """
    Load and parse YAML configuration file.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Parsed configuration dictionary, empty dict if the file doesn't exist
    """
    path = Path(config_path)
    if not path.exists():
        return {}
    
    try:
        with path.open('r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if not isinstance(data, dict):
                return {}
            return data
    except Exception:
        return {}


def load_config(config_path: str = "application.yml") -> DashboardConfig:
    """
    Load dashboard configuration from the YAML file with environment variable support.
    In mock mode, uses predefined mock configuration if the file is missing.
    
    Configuration priority:
    1. Mock configuration (if MOCK_MODE=true)
    2. YAML file with default values
    3. Environment variable placeholders in YAML (${VAR:default})
    4. Environment variables override everything
    
    Args:
        config_path: Path to YAML configuration file (default: application.yml)
        
    Returns:
        DashboardConfig instance with all settings
        
    Raises:
        ValueError: If the configuration file is missing or invalid (and not in mock mode)
        KeyError: If required configuration keys are missing
    """
    # Load YAML configuration
    if is_mock_mode():
        raw_data = get_mock_config()
    else:
        raw_data = _load_yaml_config(config_path)
    
    if not raw_data:
        raise ValueError(
            f"Configuration file '{config_path}' is missing or invalid. "
            f"Please ensure application.yml exists and is properly formatted."
        )
    
    # Resolve environment variable placeholders
    data = _resolve_env_in_dict(raw_data)
    
    # Extract dashboard configuration section
    dashboard = data.get('dashboard')
    if not dashboard:
        raise KeyError(
            "Missing 'dashboard' section in configuration. "
            "Please check your application.yml structure."
        )
    
    # Mock mode configuration
    mock_mode = str(dashboard.get('mock-mode', 'false')).lower() in ('true', '1', 'yes')
    
    # Services configuration
    services = dashboard.get('services', {})
    if not services and not mock_mode:
        raise KeyError("Missing 'dashboard.services' section in configuration")
    
    simulator_api_url = services.get('simulator', {}).get('url')
    analytics_api_url = services.get('analytics', {}).get('url')
    
    if not mock_mode and not all([simulator_api_url, analytics_api_url]):
        raise KeyError(
            "Missing service URLs in configuration. Required: "
            "dashboard.services.simulator.url, dashboard.services.analytics.url"
        )
    
    # MongoDB configuration
    mongodb = dashboard.get('mongodb', {})
    if not mongodb and not mock_mode:
        raise KeyError("Missing 'dashboard.mongodb' section in configuration")
    
    mongo_uri = mongodb.get('uri')
    mongo_db = mongodb.get('database')
    mongo_alerts_collection = mongodb.get('collections', {}).get('alerts')
    mongo_analytics_collection = mongodb.get('collections', {}).get('analytics')
    
    if not mock_mode and not all([mongo_uri, mongo_db, mongo_alerts_collection, mongo_analytics_collection]):
        raise KeyError(
            "Missing MongoDB configuration. Required: "
            "dashboard.mongodb.uri, dashboard.mongodb.database, "
            "dashboard.mongodb.collections.alerts, "
            "dashboard.mongodb.collections.analytics"
        )
    
    # UI configuration
    ui = dashboard.get('ui', {})
    if not ui:
        raise KeyError("Missing 'dashboard.ui' section in configuration")
    
    try:
        refresh_seconds_default = int(ui.get('refresh-seconds-default', 5))
        alerts_limit_default = int(ui.get('alerts-limit-default', 50))
        analytics_limit_default = int(ui.get('analytics-limit-default', 100))
    except (TypeError, ValueError) as e:
        raise ValueError(
            f"Invalid UI configuration values: {e}. "
            "refresh-seconds-default, alerts-limit-default and analytics-limit-default must be integers."
        )
    
    return DashboardConfig(
        mock_mode=mock_mode,
        simulator_api_url=simulator_api_url or "",
        analytics_api_url=analytics_api_url or "",
        mongo_uri=mongo_uri or "",
        mongo_db=mongo_db or "",
        mongo_alerts_collection=mongo_alerts_collection or "",
        mongo_analytics_collection=mongo_analytics_collection or "",
        refresh_seconds_default=refresh_seconds_default,
        alerts_limit_default=alerts_limit_default,
        analytics_limit_default=analytics_limit_default,
    )
