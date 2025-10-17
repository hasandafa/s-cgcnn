"""
Configuration loader for the AlGaAs pipeline.

This module provides functionality to load and validate configuration
from config.yaml file.
"""

import os
import yaml
from typing import Dict, Any
from pathlib import Path

from .logger import get_logger

logger = get_logger(__name__)


class ConfigLoader:
    """Handles loading and validation of configuration files."""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the config loader.

        Args:
            config_path: Path to the configuration file
        """
        self.config_path = Path(config_path)
        self.config = {}

    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.

        Returns:
            Dictionary containing configuration parameters

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is malformed
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing configuration file: {e}")

        self._validate_config()
        return self.config

    def _validate_config(self):
        """Validate the loaded configuration."""
        required_keys = ['paths', 'system', 'hyperparameters']

        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Required configuration key missing: {key}")

        # Validate paths exist
        paths = self.config['paths']
        for path_key, path_value in paths.items():
            path_obj = Path(path_value)
            if not path_obj.exists():
                logger.warning(f"Path {path_value} does not exist. Creating...")
                path_obj.mkdir(parents=True, exist_ok=True)

        # Validate system configuration
        system = self.config['system']
        if 'binary_compounds' not in system:
            raise ValueError("System configuration must include binary_compounds")

        if len(system['binary_compounds']) != 2:
            raise ValueError("Exactly 2 binary compounds required for interpolation")

        # Validate compositions
        if 'compositions' not in system or 'x_values' not in system['compositions']:
            raise ValueError("Compositions with x_values must be specified")

    def get(self, key: str, default=None) -> Any:
        """
        Get a configuration value by key.

        Args:
            key: Dot-separated key path (e.g., 'paths.data_dir')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def update_config(self, updates: Dict[str, Any]):
        """
        Update configuration with new values.

        Args:
            updates: Dictionary of updates to apply
        """
        def deep_update(base_dict, update_dict):
            for key, value in update_dict.items():
                if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value

        deep_update(self.config, updates)

    def save_config(self, output_path: str = None):
        """
        Save current configuration to file.

        Args:
            output_path: Path to save config (default: original path)
        """
        save_path = Path(output_path) if output_path else self.config_path

        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)


# Global config instance
_config_loader = None

def get_config() -> ConfigLoader:
    """Get the global configuration loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
        _config_loader.load_config()
    return _config_loader

def load_config() -> Dict[str, Any]:
    """Load configuration and return config dictionary."""
    return get_config().load_config()