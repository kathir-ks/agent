"""Centralized logging configuration for the personal agent."""

import logging
import sys
from typing import Optional


class CleanFormatter(logging.Formatter):
    """A clean formatter that only shows essential information."""

    # Color codes for terminal output
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m',      # Reset
    }

    def __init__(self, use_colors: bool = True, verbose: bool = False):
        """Initialize the formatter.

        Args:
            use_colors: Whether to use color codes
            verbose: Whether to show verbose output (module names, timestamps)
        """
        self.use_colors = use_colors and sys.stderr.isatty()
        self.verbose = verbose

        if verbose:
            fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        else:
            fmt = '%(message)s'

        super().__init__(fmt, datefmt='%H:%M:%S')

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record.

        Args:
            record: Log record to format

        Returns:
            Formatted string
        """
        # Store original levelname
        orig_levelname = record.levelname

        if self.use_colors and not self.verbose:
            # Add color to level name for non-verbose output
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"

        # Format the record
        result = super().format(record)

        # Restore original
        record.levelname = orig_levelname

        return result


def setup_logging(
    level: str = "WARNING",
    verbose: bool = False,
    log_file: Optional[str] = None
) -> None:
    """Setup centralized logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        verbose: Whether to show verbose output with timestamps and module names
        log_file: Optional file path to write logs to
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.WARNING)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove any existing handlers
    root_logger.handlers.clear()

    # Console handler with clean formatting
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(CleanFormatter(use_colors=True, verbose=verbose))
    root_logger.addHandler(console_handler)

    # Optional file handler with full details
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('google').setLevel(logging.WARNING)
    logging.getLogger('google.generativeai').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('websockets').setLevel(logging.WARNING)

    # Set our application loggers to appropriate levels
    logging.getLogger('src.agent').setLevel(max(numeric_level, logging.WARNING))
    logging.getLogger('src.llm').setLevel(max(numeric_level, logging.WARNING))
    logging.getLogger('src.terminal').setLevel(max(numeric_level, logging.WARNING))
    logging.getLogger('src.web').setLevel(max(numeric_level, logging.WARNING))
    logging.getLogger('src.daemon').setLevel(max(numeric_level, logging.WARNING))


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
