import logging
import sys
from typing import Optional


def get_logger(name: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Get a configured logger instance.

    Args:
        name (str, optional): Logger name. If None, uses the calling module's name.
        level (int, optional): Logging level. Defaults to logging.INFO.

    Returns:
        logging.Logger: Configured logger instance.
    """
    if name is None:
        # Get the calling module's name
        import inspect

        frame = inspect.currentframe()
        if frame is not None and frame.f_back is not None:
            name = frame.f_back.f_globals.get("__name__", "vaiae")
        else:
            name = "vaiae"

    logger = logging.getLogger(name)

    # Avoid adding multiple handlers if logger already exists
    if not logger.handlers:
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)
        logger.setLevel(level)

        # Prevent propagation to avoid duplicate logs
        logger.propagate = False

    return logger


def set_log_level(level: int) -> None:
    """Set the global log level for all vaiae loggers.

    Args:
        level (int): Logging level (e.g., logging.DEBUG, logging.INFO, etc.)
    """
    # Get the root vaiae logger
    vaiae_logger = logging.getLogger("vaiae")
    vaiae_logger.setLevel(level)

    # Update all handlers
    for handler in vaiae_logger.handlers:
        handler.setLevel(level)


def configure_debug_logging() -> None:
    """Configure debug-level logging for development."""
    set_log_level(logging.DEBUG)


def configure_quiet_logging() -> None:
    """Configure warning-level logging for quiet operation."""
    set_log_level(logging.WARNING)
