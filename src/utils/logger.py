"""
Logging configuration for S-CGCNN project.

Provides centralized logging setup with configurable levels and formatting.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any


class Logger:
    """Centralized logging configuration for the project."""

    _instance: Optional['Logger'] = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls) -> 'Logger':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is None:
            self._setup_logger()

    def _setup_logger(self) -> None:
        """Set up the logger with proper configuration."""
        self._logger = logging.getLogger('s_cgcnn')
        self._logger.setLevel(logging.DEBUG)

        # Remove any existing handlers
        self._logger.handlers.clear()

        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        self._logger.addHandler(console_handler)

        # File handler (rotating)
        log_file = Path('logs/s-cgcnn.log')
        log_file.parent.mkdir(exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        self._logger.addHandler(file_handler)

    def get_logger(self, name: str = 's_cgcnn') -> logging.Logger:
        """Get a logger instance with the specified name."""
        if name == 's_cgcnn':
            return self._logger
        else:
            return logging.getLogger(f's_cgcnn.{name}')

    def set_level(self, level: str) -> None:
        """Set the logging level for all handlers."""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }

        log_level = level_map.get(level.upper(), logging.INFO)
        self._logger.setLevel(log_level)

        for handler in self._logger.handlers:
            handler.setLevel(log_level)


# Global logger instance
logger = Logger().get_logger()


def get_logger(name: str = 's_cgcnn') -> logging.Logger:
    """Convenience function to get a logger instance."""
    return Logger().get_logger(name)


def setup_logging(config: Optional[Dict[str, Any]] = None) -> None:
    """Set up logging based on configuration."""
    if config and 'logging' in config:
        log_config = config['logging']
        level = log_config.get('level', 'INFO')
        Logger().set_level(level)

        # Additional setup can be added here
        if log_config.get('file_enabled', True):
            # File logging is already set up
            pass