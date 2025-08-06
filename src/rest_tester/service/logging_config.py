"""
Centralized Logging Configuration

This module provides comprehensive logging infrastructure for the REST Tester
application, including both console and GUI logging with consistent formatting
and level management across all components.

Key Features:
    - Unified logging format across all application components
    - GUI integration through Qt signals for tab-specific logging
    - Multi-line message formatting with consistent prefixes
    - Millisecond precision timestamps
    - Instance-specific loggers for server/client instances
    - Graceful shutdown and resource cleanup

Architecture:
    - LogSignalHandler: Bridges Python logging to Qt signals
    - MultiLineFormatter: Ensures consistent formatting for complex messages
    - Centralized logger factory with standard configuration
    - Prevents duplicate logging through proper propagation control

Design Pattern:
    Implements the Observer pattern for GUI logging integration
    with Factory pattern for logger creation.
"""

import logging
import sys
from typing import Optional, Callable
from PySide6.QtCore import QObject, Signal


class LogSignalHandler(QObject, logging.Handler):
    """
    Qt-integrated logging handler that emits signals for GUI consumption.
    
    This handler bridges Python's logging system with Qt's signal-slot
    mechanism, enabling real-time log display in GUI components while
    maintaining proper separation between logging and UI concerns.
    
    Features:
        - Emits Qt signals for each log message
        - Instance-specific message filtering
        - Consistent timestamp formatting
        - Preserves log formatting while adapting for GUI display
        
    Signals:
        log_message(str, str, str): Emitted for each log entry
            - timestamp: Formatted timestamp string
            - level: Log level (INFO, WARNING, ERROR, etc.)
            - message: Formatted message content
    """
    log_message = Signal(str, str, str)  # timestamp, level, message
    
    def __init__(self, instance_name: str):
        """
        Initialize signal handler for specific instance.
        
        Args:
            instance_name: Identifier for the logging instance (e.g., "localhost:8080")
        """
        QObject.__init__(self)
        logging.Handler.__init__(self)
        self.instance_name = instance_name
        
        # Configure formatter for consistent timestamp format
        formatter = logging.Formatter(
            '%(asctime)s|%(levelname)s|%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Override formatTime to include milliseconds precision
        def formatTime(self, record, datefmt=None):
            import datetime
            ct = datetime.datetime.fromtimestamp(record.created)
            if datefmt:
                s = ct.strftime(datefmt)
                return f"{s},{int(record.msecs):03d}"
            else:
                return ct.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
        
        formatter.formatTime = formatTime.__get__(formatter, logging.Formatter)
        self.setFormatter(formatter)
    
    def emit(self, record):
        """
        Process log record and emit Qt signal.
        
        Formats the log record for GUI display while preserving the
        structure and information from the console formatter.
        
        Args:
            record: Python logging.LogRecord instance
        """
        try:
            # Use console formatter for complete message formatting
            console_formatter = MultiLineFormatter(
                '[%(asctime)s][%(name)s][%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # Generate fully formatted message for consistency
            full_formatted_message = console_formatter.format(record)
            
            # Create GUI-compatible timestamp
            import datetime
            ct = datetime.datetime.fromtimestamp(record.created)
            timestamp = f"{ct.strftime('%Y-%m-%d %H:%M:%S')},{int(record.msecs):03d}"
            level = record.levelname
            
            # Extract message content while preserving multi-line structure
            import re
            pattern = r'^\[([^\]]+)\]\[([^\]]+)\]\[([^\]]+)\] (.*)$'
            
            lines = full_formatted_message.split('\n')
            gui_formatted_lines = []
            
            for line in lines:
                match = re.match(pattern, line)
                if match:
                    # Extract clean message content for GUI display
                    message_content = match.group(4)
                    gui_formatted_lines.append(f"[{timestamp}][{level}] {message_content}")
                else:
                    # Fallback for non-standard line formats
                    gui_formatted_lines.append(f"[{timestamp}][{level}] {line}")
            
            gui_formatted_message = '\n'.join(gui_formatted_lines)
            
            # Emit signal for GUI consumption
            self.log_message.emit(timestamp, level, gui_formatted_message)
            
        except Exception:
            # Handle errors gracefully to prevent logging system failure
            self.handleError(record)


class MultiLineFormatter(logging.Formatter):
    """
    Enhanced formatter for multi-line log messages with consistent prefixes.
    
    This formatter ensures that each line of a multi-line log message
    receives the complete logging prefix (timestamp, instance name, level),
    improving readability for complex log entries like stack traces or
    formatted data structures.
    
    Features:
        - Preserves original message structure
        - Adds consistent prefixes to continuation lines
        - Handles edge cases gracefully
        - Maintains compatibility with standard formatters
    """
    
    def format(self, record):
        """
        Format log record with consistent multi-line handling.
        
        Ensures each line of a multi-line message gets the full
        logging prefix for improved readability and parsing.
        
        Args:
            record: Python logging.LogRecord instance
            
        Returns:
            str: Formatted log message with consistent line prefixes
        """
        # Generate base formatted message
        original_message = super().format(record)
        
        # Handle single-line messages efficiently
        lines = original_message.split('\n')
        if len(lines) <= 1:
            return original_message
            
        # Extract prefix from the first line
        message_start = original_message.find(record.getMessage())
        if message_start == -1:
            return original_message
            
        prefix = original_message[:message_start]
        
        # Apply prefix to each line of the actual message
        formatted_lines = []
        for line in record.getMessage().split('\n'):
            formatted_lines.append(f"{prefix}{line}")
            
        return '\n'.join(formatted_lines)


def setup_logger(name: str, level: int = logging.INFO, signal_handler: Optional[LogSignalHandler] = None) -> logging.Logger:
    """
    Create and configure a logger with standardized formatting and handlers.
    
    This factory function creates loggers with consistent configuration
    across the application, ensuring uniform log format and behavior.
    Prevents duplicate handler registration and configures appropriate
    output destinations.
    
    Args:
        name: Logger instance identifier (e.g., "ConfigLocator", "localhost:8080")
        level: Minimum logging level (default: logging.INFO)
        signal_handler: Optional Qt signal handler for GUI integration
        
    Returns:
        logging.Logger: Fully configured logger instance
        
    Features:
        - Consistent formatting across all loggers
        - Millisecond precision timestamps
        - Prevents duplicate handler registration
        - Optional GUI integration through signal handlers
        - Proper propagation control to avoid duplicate messages
    """
    logger = logging.getLogger(name)
    
    # Prevent duplicate handler registration
    if logger.handlers:
        return logger
        
    logger.setLevel(level)
    
    # Configure console output handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Create standardized formatter
    # Format: [timestamp][instance_name][level] message
    formatter = MultiLineFormatter(
        '[%(asctime)s][%(name)s][%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Enhance formatter with millisecond precision
    def formatTime(self, record, datefmt=None):
        """Enhanced timestamp formatting with millisecond precision."""
        import datetime
        ct = datetime.datetime.fromtimestamp(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
            return f"{s},{int(record.msecs):03d}"
        else:
            return ct.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    
    formatter.formatTime = formatTime.__get__(formatter, MultiLineFormatter)
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Add GUI integration if requested
    if signal_handler:
        signal_handler.setLevel(level)
        logger.addHandler(signal_handler)
    
    # Prevent propagation to avoid duplicate console output
    logger.propagate = False
    
    return logger


def get_logger(name: str, signal_handler: Optional[LogSignalHandler] = None) -> logging.Logger:
    """
    Retrieve existing logger or create new one with standard configuration.
    
    This convenience function provides a simple interface for obtaining
    properly configured loggers throughout the application.
    
    Args:
        name: Logger instance identifier
        signal_handler: Optional Qt signal handler for GUI integration
        
    Returns:
        logging.Logger: Configured logger instance
        
    Note:
        This function will reuse existing loggers if they have already
        been configured, preventing duplicate handler registration.
    """
    return setup_logger(name, signal_handler=signal_handler)


def add_signal_handler_to_existing_logger(logger_name: str, signal_handler: LogSignalHandler) -> bool:
    """
    Add GUI signal handler to an already existing logger.
    
    This function is useful when GUI components are created after loggers
    have already been instantiated (e.g., during dynamic tab creation).
    It ensures proper configuration even for pre-existing loggers.
    
    Args:
        logger_name: Name of the existing logger
        signal_handler: Qt signal handler to add
        
    Returns:
        bool: True if handler was successfully added, False otherwise
        
    Features:
        - Configures incomplete loggers if necessary
        - Adds console handler if missing
        - Sets up proper formatting and levels
        - Prevents duplicate handler registration
    """
    logger = logging.getLogger(logger_name)
    
    if logger and signal_handler:
        # Ensure logger is properly configured
        if logger.level == 0 or not logger.handlers:
            # Configure incomplete logger
            logger.setLevel(logging.INFO)
            logger.propagate = False
            
            # Add console handler if missing
            if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
                handler = logging.StreamHandler(sys.stdout)
                handler.setLevel(logging.INFO)
                
                # Apply standard formatter
                formatter = MultiLineFormatter(
                    '[%(asctime)s][%(name)s][%(levelname)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                
                # Add millisecond precision
                def formatTime(self, record, datefmt=None):
                    import datetime
                    ct = datetime.datetime.fromtimestamp(record.created)
                    if datefmt:
                        s = ct.strftime(datefmt)
                        return f"{s},{int(record.msecs):03d}"
                    else:
                        return ct.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
                
                formatter.formatTime = formatTime.__get__(formatter, MultiLineFormatter)
                handler.setFormatter(formatter)
                logger.addHandler(handler)
        
        # Add signal handler for GUI integration
        signal_handler.setLevel(logging.INFO)
        logger.addHandler(signal_handler)
        return True
    return False


def shutdown_logging():
    """
    Perform clean shutdown of the logging system.
    
    Ensures all log handlers are properly closed and resources are
    released. Should be called during application shutdown to prevent
    resource leaks and ensure all pending log messages are flushed.
    """
    logging.shutdown()
