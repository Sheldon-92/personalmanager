"""JSON Structured Logging Module

Provides structured logging capabilities with JSON output format,
automatic context enrichment, and performance tracking.
"""

import json
import time
import threading
import traceback
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from enum import Enum


class LogLevel(Enum):
    """Log severity levels"""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


@dataclass
class LogContext:
    """Structured log context"""
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary, excluding None values"""
        return {k: v for k, v in asdict(self).items() if v is not None}


class StructuredLogger:
    """JSON structured logger with performance tracking"""

    def __init__(
        self,
        name: str,
        log_file: Optional[Path] = None,
        level: LogLevel = LogLevel.INFO,
        enable_console: bool = True,
        enable_file: bool = True,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        self.name = name
        self.level = level
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.max_file_size = max_file_size
        self.backup_count = backup_count

        # Thread-local storage for context
        self._context = threading.local()

        # Performance metrics
        self._metrics = {
            'logs_written': 0,
            'errors_logged': 0,
            'warnings_logged': 0,
            'bytes_written': 0
        }

        # Setup log file
        if log_file:
            self.log_file = log_file
        else:
            log_dir = Path.home() / '.pm' / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            self.log_file = log_dir / f'{name}.json'

        # Rotate if needed
        self._rotate_if_needed()

    def _rotate_if_needed(self):
        """Rotate log file if it exceeds max size"""
        if not self.log_file.exists():
            return

        if self.log_file.stat().st_size >= self.max_file_size:
            # Rotate existing logs
            for i in range(self.backup_count - 1, 0, -1):
                old_file = self.log_file.with_suffix(f'.json.{i}')
                new_file = self.log_file.with_suffix(f'.json.{i + 1}')
                if old_file.exists():
                    old_file.rename(new_file)

            # Move current to .1
            self.log_file.rename(self.log_file.with_suffix('.json.1'))

    def _get_context(self) -> Dict[str, Any]:
        """Get current thread context"""
        if hasattr(self._context, 'data'):
            return self._context.data.to_dict()
        return {}

    def set_context(self, **kwargs):
        """Set logging context for current thread"""
        if not hasattr(self._context, 'data'):
            self._context.data = LogContext()

        for key, value in kwargs.items():
            if hasattr(self._context.data, key):
                setattr(self._context.data, key, value)

    def clear_context(self):
        """Clear current thread context"""
        if hasattr(self._context, 'data'):
            del self._context.data

    @contextmanager
    def context(self, **kwargs):
        """Context manager for temporary context"""
        old_context = self._get_context().copy()
        self.set_context(**kwargs)
        try:
            yield
        finally:
            self.clear_context()
            if old_context:
                self.set_context(**old_context)

    def _format_log_entry(
        self,
        level: LogLevel,
        message: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Format a structured log entry"""
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': level.name,
            'logger': self.name,
            'message': message,
            'context': self._get_context(),
            'thread_id': threading.current_thread().ident,
            'thread_name': threading.current_thread().name
        }

        # Add extra fields
        if kwargs:
            entry['data'] = kwargs

        # Add exception info if present
        if 'exception' in kwargs:
            exc = kwargs.pop('exception')
            if isinstance(exc, Exception):
                entry['exception'] = {
                    'type': type(exc).__name__,
                    'message': str(exc),
                    'traceback': traceback.format_exception(
                        type(exc), exc, exc.__traceback__
                    )
                }

        return entry

    def _write_log(self, entry: Dict[str, Any]):
        """Write log entry to outputs"""
        json_str = json.dumps(entry, default=str) + '\n'

        # Update metrics
        self._metrics['logs_written'] += 1
        self._metrics['bytes_written'] += len(json_str)

        if entry['level'] == 'ERROR' or entry['level'] == 'CRITICAL':
            self._metrics['errors_logged'] += 1
        elif entry['level'] == 'WARNING':
            self._metrics['warnings_logged'] += 1

        # Console output
        if self.enable_console:
            print(json_str, end='')

        # File output
        if self.enable_file:
            self._rotate_if_needed()
            with open(self.log_file, 'a') as f:
                f.write(json_str)

    def log(self, level: LogLevel, message: str, **kwargs):
        """Log a message at specified level"""
        if level.value >= self.level.value:
            entry = self._format_log_entry(level, message, **kwargs)
            self._write_log(entry)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self.log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message"""
        if exception:
            kwargs['exception'] = exception
        self.log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log critical message"""
        if exception:
            kwargs['exception'] = exception
        self.log(LogLevel.CRITICAL, message, **kwargs)

    @contextmanager
    def timer(self, operation: str, **kwargs):
        """Context manager for timing operations"""
        start_time = time.time()
        self.info(f"Starting {operation}", operation=operation, **kwargs)

        try:
            yield
        except Exception as e:
            elapsed = time.time() - start_time
            self.error(
                f"Failed {operation}",
                exception=e,
                operation=operation,
                duration_ms=elapsed * 1000,
                **kwargs
            )
            raise
        else:
            elapsed = time.time() - start_time
            self.info(
                f"Completed {operation}",
                operation=operation,
                duration_ms=elapsed * 1000,
                **kwargs
            )

    def get_metrics(self) -> Dict[str, Any]:
        """Get logger metrics"""
        return self._metrics.copy()


class LoggerFactory:
    """Factory for creating and managing loggers"""

    _loggers: Dict[str, StructuredLogger] = {}
    _default_level = LogLevel.INFO
    _default_log_dir = Path.home() / '.pm' / 'logs'

    @classmethod
    def get_logger(
        cls,
        name: str,
        level: Optional[LogLevel] = None
    ) -> StructuredLogger:
        """Get or create a logger instance"""
        if name not in cls._loggers:
            cls._loggers[name] = StructuredLogger(
                name=name,
                level=level or cls._default_level
            )
        return cls._loggers[name]

    @classmethod
    def set_default_level(cls, level: LogLevel):
        """Set default log level for new loggers"""
        cls._default_level = level

    @classmethod
    def get_all_metrics(cls) -> Dict[str, Dict[str, Any]]:
        """Get metrics from all loggers"""
        return {
            name: logger.get_metrics()
            for name, logger in cls._loggers.items()
        }


# Convenience functions
def get_logger(name: str) -> StructuredLogger:
    """Get a logger instance"""
    return LoggerFactory.get_logger(name)


def log_performance(func):
    """Decorator for logging function performance"""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        with logger.timer(
            f"{func.__name__}",
            function=func.__name__,
            module=func.__module__
        ):
            return func(*args, **kwargs)
    return wrapper


def log_errors(func):
    """Decorator for logging function errors"""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(
                f"Error in {func.__name__}",
                exception=e,
                function=func.__name__,
                module=func.__module__
            )
            raise
    return wrapper


# Example usage and testing
if __name__ == "__main__":
    # Create logger
    logger = get_logger("pm.obs.test")

    # Basic logging
    logger.info("System started", version="0.1.0", environment="development")

    # With context
    logger.set_context(request_id="req-123", user_id="user-456")
    logger.info("Processing request", endpoint="/api/recommend")

    # Timer context
    with logger.timer("database_query", query="SELECT * FROM users"):
        time.sleep(0.1)  # Simulate work

    # Error logging
    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.error("Operation failed", exception=e, operation="test")

    # Get metrics
    print("\nLogger Metrics:")
    print(json.dumps(logger.get_metrics(), indent=2))