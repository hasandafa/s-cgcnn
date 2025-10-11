"""
Logging Configuration for s-CGCNN v0.1.1

Provides flexible logging setup with console and file output.

Author: Abdullah Hasan Dafa
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Union


# ============================================================================
# COLOR CODES FOR CONSOLE OUTPUT
# ============================================================================

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}"
                f"{record.levelname:8}"
                f"{self.COLORS['RESET']}"
            )
        return super().format(record)


# ============================================================================
# LOGGER SETUP FUNCTIONS
# ============================================================================

def setup_logger(
    name: str,
    log_file: Optional[Union[str, Path]] = None,
    level: str = "INFO",
    console: bool = True,
    file_mode: str = 'a',
    use_colors: bool = False  # Disabled by default for Windows compatibility
) -> logging.Logger:
    """
    Setup logger with console and/or file output.
    
    Args:
        name: Logger name
        log_file: Path to log file (None = no file logging)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console: Enable console output
        file_mode: File mode ('a' = append, 'w' = overwrite)
        use_colors: Use colored output in console
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = setup_logger("MyModule", "logs/my.log", "DEBUG")
        >>> logger.info("This is an info message")
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []
    
    # Define format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        
        if use_colors and sys.stdout.isatty():
            # Use colored formatter for terminal
            formatter = ColoredFormatter(log_format, datefmt=date_format)
        else:
            # Plain formatter for redirected output
            formatter = logging.Formatter(log_format, datefmt=date_format)
        
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, mode=file_mode)
        file_handler.setLevel(getattr(logging, level.upper()))
        
        # File always uses plain formatter (no colors)
        formatter = logging.Formatter(log_format, datefmt=date_format)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get existing logger by name.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance (creates new if doesn't exist)
    """
    return logging.getLogger(name)


def configure_root_logger(
    level: str = "INFO",
    log_file: Optional[Union[str, Path]] = None
):
    """
    Configure the root logger (affects all loggers).
    
    Args:
        level: Log level
        log_file: Path to log file
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )


def create_timestamped_log(
    base_name: str,
    log_dir: Union[str, Path] = "logs",
    level: str = "INFO"
) -> logging.Logger:
    """
    Create logger with timestamped log file.
    
    Args:
        base_name: Base name for logger and file
        log_dir: Directory for log files
        level: Log level
    
    Returns:
        Logger with timestamped file
    
    Example:
        >>> logger = create_timestamped_log("pipeline")
        >>> # Creates: logs/pipeline_20250411_143022.log
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = Path(log_dir) / f"{base_name}_{timestamp}.log"
    
    return setup_logger(
        name=base_name,
        log_file=log_file,
        level=level
    )


def set_logger_level(logger: logging.Logger, level: str):
    """
    Change log level for existing logger.
    
    Args:
        logger: Logger instance
        level: New log level
    """
    logger.setLevel(getattr(logging, level.upper()))
    for handler in logger.handlers:
        handler.setLevel(getattr(logging, level.upper()))


def add_file_handler(
    logger: logging.Logger,
    log_file: Union[str, Path],
    level: Optional[str] = None
):
    """
    Add file handler to existing logger.
    
    Args:
        logger: Logger instance
        log_file: Path to log file
        level: Log level (None = use logger's level)
    """
    log_file = Path(log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file)
    
    if level:
        file_handler.setLevel(getattr(logging, level.upper()))
    else:
        file_handler.setLevel(logger.level)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


# ============================================================================
# CONTEXT MANAGERS
# ============================================================================

class LoggerContext:
    """Context manager for temporary logger configuration"""
    
    def __init__(self, logger: logging.Logger, level: str):
        self.logger = logger
        self.new_level = level
        self.old_level = None
    
    def __enter__(self):
        self.old_level = self.logger.level
        set_logger_level(self.logger, self.new_level)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.old_level)


def temporary_log_level(logger: logging.Logger, level: str):
    """
    Context manager for temporary log level change.
    
    Example:
        >>> logger = setup_logger("test")
        >>> with temporary_log_level(logger, "DEBUG"):
        ...     logger.debug("This will show")
        >>> logger.debug("This won't show if level was INFO")
    """
    return LoggerContext(logger, level)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def disable_logger(name: str):
    """Disable a specific logger"""
    logger = logging.getLogger(name)
    logger.disabled = True


def enable_logger(name: str):
    """Enable a previously disabled logger"""
    logger = logging.getLogger(name)
    logger.disabled = False


def list_active_loggers() -> list:
    """Get list of all active logger names"""
    return [name for name in logging.Logger.manager.loggerDict.keys()]


def close_all_handlers():
    """Close all logging handlers (call before program exit)"""
    for logger_name in list_active_loggers():
        logger = logging.getLogger(logger_name)
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)


# ============================================================================
# DEFAULT LOGGER FOR PACKAGE
# ============================================================================

# Package default logger
package_logger = setup_logger(
    name="s-cgcnn",
    level="INFO",
    console=True,
    use_colors=True
)


# ============================================================================
# MODULE METADATA
# ============================================================================

__version__ = "0.1.1"
__author__ = "Abdullah Hasan Dafa"

__all__ = [
    "setup_logger",
    "get_logger",
    "configure_root_logger",
    "create_timestamped_log",
    "set_logger_level",
    "add_file_handler",
    "temporary_log_level",
    "disable_logger",
    "enable_logger",
    "list_active_loggers",
    "close_all_handlers",
    "package_logger",
]