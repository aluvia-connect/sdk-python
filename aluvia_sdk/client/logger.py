"""Logging utilities for Aluvia SDK."""

from __future__ import annotations

import logging
from typing import Literal

LogLevel = Literal["silent", "info", "debug"]


class Logger:
    """Simple logger wrapper for the SDK."""

    def __init__(self, level: LogLevel = "info") -> None:
        """
        Initialize logger with specified level.

        Args:
            level: Logging level ('silent', 'info', or 'debug')
        """
        self.logger = logging.getLogger("aluvia_sdk")

        # Set level based on input
        if level == "silent":
            self.logger.setLevel(logging.CRITICAL + 1)  # Effectively silent
        elif level == "debug":
            self.logger.setLevel(logging.DEBUG)
        else:  # info
            self.logger.setLevel(logging.INFO)

        # Add handler if not already present
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)
