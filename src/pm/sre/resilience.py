"""SRE Resilience Strategies Implementation

This module implements comprehensive resilience patterns for the PM system:
- Circuit Breaker: Prevents cascading failures by failing fast
- Retry Policy: Implements exponential backoff with jitter
- Rate Limiter: Token bucket algorithm for request throttling
- Error Budget Monitor: Tracks reliability metrics and SLO adherence

Design Goals:
- Fault tolerance with graceful degradation
- No cascading failures
- Recovery time < 30s
- E2E test success ≥95% under fault injection
"""

import asyncio
import time
import random
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
import structlog
from collections import defaultdict, deque
import json

logger = structlog.get_logger()

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing fast, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class RetryableError(Exception):
    """Exception that should trigger retry logic"""
    pass


class NonRetryableError(Exception):
    """Exception that should NOT trigger retry logic"""
    pass


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 3  # Successes needed to close from half-open
    timeout_seconds: float = 60  # How long to stay open
    expected_exception: type = Exception


@dataclass
class RetryConfig:
    """Configuration for retry policy"""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple = (RetryableError, ConnectionError, TimeoutError)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiter"""
    requests_per_second: float = 10.0
    bucket_capacity: int = 20
    refill_period: float = 1.0


@dataclass
class ErrorBudgetConfig:
    """Configuration for error budget monitoring"""
    window_size_minutes: int = 60  # Rolling window size
    slo_target: float = 0.95  # 95% success rate target
    alert_threshold: float = 0.5  # Alert when 50% of budget consumed


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance

    Prevents cascading failures by failing fast when error rate exceeds threshold.
    Automatically attempts recovery after timeout period.
    """

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.lock = threading.RLock()

        logger.info("Circuit breaker initialized",
                   failure_threshold=config.failure_threshold,
                   timeout_seconds=config.timeout_seconds)

    def _can_attempt(self) -> bool:
        """Check if request can be attempted based on current state"""
        with self.lock:
            if self.state == CircuitState.CLOSED:
                return True
            elif self.state == CircuitState.OPEN:
                # Check if timeout has elapsed
                if time.time() - self.last_failure_time >= self.config.timeout_seconds:
                    logger.info("Circuit breaker transitioning to half-open")
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    return True
                return False
            elif self.state == CircuitState.HALF_OPEN:
                return True
            return False

    def _record_success(self):
        """Record successful operation"""
        with self.lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    logger.info("Circuit breaker closing after successful recovery")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
            elif self.state == CircuitState.CLOSED:
                self.failure_count = max(0, self.failure_count - 1)

    def _record_failure(self, exception: Exception):
        """Record failed operation"""
        with self.lock:
            if isinstance(exception, self.config.expected_exception):
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.state == CircuitState.CLOSED:
                    if self.failure_count >= self.config.failure_threshold:
                        logger.warning("Circuit breaker opening due to failures",
                                     failure_count=self.failure_count)
                        self.state = CircuitState.OPEN
                elif self.state == CircuitState.HALF_OPEN:
                    logger.info("Circuit breaker re-opening after failed recovery attempt")
                    self.state = CircuitState.OPEN
                    self.success_count = 0

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection"""
        if not self._can_attempt():
            raise NonRetryableError(f"Circuit breaker is {self.state.value}")

        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure(e)
            raise

    def get_state(self) -> dict:
        """Get current circuit breaker state"""
        with self.lock:
            return {
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "last_failure_time": self.last_failure_time
            }


class RetryPolicy:
    """Retry policy with exponential backoff and jitter

    Implements intelligent retry logic with:
    - Exponential backoff to avoid overwhelming failing services
    - Jitter to prevent thundering herd effect
    - Configurable retry conditions
    """

    def __init__(self, config: RetryConfig):
        self.config = config
        logger.info("Retry policy initialized",
                   max_attempts=config.max_attempts,
                   initial_delay=config.initial_delay,
                   backoff_multiplier=config.backoff_multiplier)

    def _should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if exception should trigger retry"""
        if attempt >= self.config.max_attempts:
            return False

        return isinstance(exception, self.config.retryable_exceptions)

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay before next retry attempt"""
        base_delay = self.config.initial_delay * (self.config.backoff_multiplier ** attempt)
        delay = min(base_delay, self.config.max_delay)

        if self.config.jitter:
            # Add ±25% jitter
            jitter = delay * 0.25 * (2 * random.random() - 1)
            delay = max(0, delay + jitter)

        return delay

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with retry logic"""
        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                result = func(*args, **kwargs)
                if attempt > 0:
                    logger.info("Retry successful", attempt=attempt + 1)
                return result

            except Exception as e:
                last_exception = e

                if not self._should_retry(e, attempt):
                    logger.info("Not retrying exception",
                               exception_type=type(e).__name__,
                               attempt=attempt + 1)
                    break

                if attempt < self.config.max_attempts - 1:
                    delay = self._calculate_delay(attempt)
                    logger.warning("Retrying after failure",
                                 exception_type=type(e).__name__,
                                 attempt=attempt + 1,
                                 delay=delay)
                    time.sleep(delay)

        logger.error("All retry attempts failed",
                    attempts=self.config.max_attempts,
                    final_exception=str(last_exception))
        raise last_exception


class RateLimiter:
    """Token bucket rate limiter

    Implements token bucket algorithm for request throttling:
    - Fixed rate of token generation
    - Configurable bucket capacity for burst handling
    - Thread-safe operation
    """

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.tokens = float(config.bucket_capacity)
        self.last_refill = time.time()
        self.lock = threading.RLock()

        logger.info("Rate limiter initialized",
                   requests_per_second=config.requests_per_second,
                   bucket_capacity=config.bucket_capacity)

    def _refill_tokens(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill

        if elapsed >= self.config.refill_period:
            tokens_to_add = elapsed * self.config.requests_per_second
            self.tokens = min(self.config.bucket_capacity,
                            self.tokens + tokens_to_add)
            self.last_refill = now

    def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens from bucket"""
        with self.lock:
            self._refill_tokens()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with rate limiting"""
        if not self.acquire():
            raise NonRetryableError("Rate limit exceeded")

        return func(*args, **kwargs)

    def get_state(self) -> dict:
        """Get current rate limiter state"""
        with self.lock:
            self._refill_tokens()
            return {
                "available_tokens": self.tokens,
                "capacity": self.config.bucket_capacity,
                "requests_per_second": self.config.requests_per_second
            }


class ErrorBudgetMonitor:
    """Error budget monitoring for SLO tracking

    Tracks reliability metrics over rolling time windows:
    - Success/failure rates
    - SLO adherence
    - Error budget consumption
    - Alerting thresholds
    """

    def __init__(self, config: ErrorBudgetConfig):
        self.config = config
        self.requests: deque = deque()  # (timestamp, success)
        self.lock = threading.RLock()

        logger.info("Error budget monitor initialized",
                   window_size_minutes=config.window_size_minutes,
                   slo_target=config.slo_target)

    def _cleanup_old_requests(self):
        """Remove requests outside the rolling window"""
        cutoff_time = time.time() - (self.config.window_size_minutes * 60)
        while self.requests and self.requests[0][0] < cutoff_time:
            self.requests.popleft()

    def record_request(self, success: bool):
        """Record a request outcome"""
        with self.lock:
            self.requests.append((time.time(), success))
            self._cleanup_old_requests()

    def get_metrics(self) -> dict:
        """Get current reliability metrics"""
        with self.lock:
            self._cleanup_old_requests()

            if not self.requests:
                return {
                    "total_requests": 0,
                    "success_rate": 1.0,
                    "error_rate": 0.0,
                    "slo_compliance": True,
                    "error_budget_consumed": 0.0
                }

            total_requests = len(self.requests)
            successful_requests = sum(1 for _, success in self.requests if success)
            success_rate = successful_requests / total_requests
            error_rate = 1 - success_rate

            # Calculate error budget consumption
            max_allowed_errors = total_requests * (1 - self.config.slo_target)
            actual_errors = total_requests - successful_requests
            error_budget_consumed = actual_errors / max_allowed_errors if max_allowed_errors > 0 else 0

            slo_compliance = success_rate >= self.config.slo_target

            return {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "success_rate": success_rate,
                "error_rate": error_rate,
                "slo_compliance": slo_compliance,
                "slo_target": self.config.slo_target,
                "error_budget_consumed": min(1.0, error_budget_consumed),
                "should_alert": error_budget_consumed >= self.config.alert_threshold
            }


# Global instances for easy access
_circuit_breakers: Dict[str, CircuitBreaker] = {}
_retry_policies: Dict[str, RetryPolicy] = {}
_rate_limiters: Dict[str, RateLimiter] = {}
_error_budget_monitors: Dict[str, ErrorBudgetMonitor] = {}
_global_lock = threading.RLock()


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Get or create circuit breaker instance"""
    with _global_lock:
        if name not in _circuit_breakers:
            if config is None:
                config = CircuitBreakerConfig()
            _circuit_breakers[name] = CircuitBreaker(config)
        return _circuit_breakers[name]


def get_retry_policy(name: str, config: Optional[RetryConfig] = None) -> RetryPolicy:
    """Get or create retry policy instance"""
    with _global_lock:
        if name not in _retry_policies:
            if config is None:
                config = RetryConfig()
            _retry_policies[name] = RetryPolicy(config)
        return _retry_policies[name]


def get_rate_limiter(name: str, config: Optional[RateLimitConfig] = None) -> RateLimiter:
    """Get or create rate limiter instance"""
    with _global_lock:
        if name not in _rate_limiters:
            if config is None:
                config = RateLimitConfig()
            _rate_limiters[name] = RateLimiter(config)
        return _rate_limiters[name]


def get_error_budget_monitor(name: str, config: Optional[ErrorBudgetConfig] = None) -> ErrorBudgetMonitor:
    """Get or create error budget monitor instance"""
    with _global_lock:
        if name not in _error_budget_monitors:
            if config is None:
                config = ErrorBudgetConfig()
            _error_budget_monitors[name] = ErrorBudgetMonitor(config)
        return _error_budget_monitors[name]


def resilient_call(
    func: Callable[..., T],
    circuit_breaker_name: Optional[str] = None,
    retry_policy_name: Optional[str] = None,
    rate_limiter_name: Optional[str] = None,
    error_budget_name: Optional[str] = None,
    *args,
    **kwargs
) -> T:
    """Execute function with full resilience patterns applied

    Args:
        func: Function to execute
        circuit_breaker_name: Name of circuit breaker to use
        retry_policy_name: Name of retry policy to use
        rate_limiter_name: Name of rate limiter to use
        error_budget_name: Name of error budget monitor to use

    Returns:
        Function result

    Raises:
        Various exceptions based on resilience policies
    """

    def wrapped_call():
        success = True
        start_time = time.time()

        try:
            # Apply rate limiting
            if rate_limiter_name:
                rate_limiter = get_rate_limiter(rate_limiter_name)
                result = rate_limiter.call(func, *args, **kwargs)
            else:
                result = func(*args, **kwargs)

            return result

        except Exception as e:
            success = False
            raise
        finally:
            # Record metrics
            if error_budget_name:
                monitor = get_error_budget_monitor(error_budget_name)
                monitor.record_request(success)

            if success:
                duration = time.time() - start_time
                logger.info("Resilient call succeeded",
                          function=func.__name__,
                          duration=duration)
            else:
                logger.warning("Resilient call failed",
                             function=func.__name__)

    # Apply circuit breaker
    if circuit_breaker_name:
        circuit_breaker = get_circuit_breaker(circuit_breaker_name)
        wrapped_call = lambda: circuit_breaker.call(wrapped_call)

    # Apply retry policy
    if retry_policy_name:
        retry_policy = get_retry_policy(retry_policy_name)
        wrapped_call = lambda: retry_policy.call(wrapped_call)

    return wrapped_call()


# Decorator functions for easy integration

def with_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None
):
    """Decorator to apply circuit breaker pattern"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cb = get_circuit_breaker(name, config)
            return cb.call(func, *args, **kwargs)
        return wrapper
    return decorator


def with_retry(
    name: str,
    config: Optional[RetryConfig] = None
):
    """Decorator to apply retry pattern"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry = get_retry_policy(name, config)
            return retry.call(func, *args, **kwargs)
        return wrapper
    return decorator


def with_rate_limit(
    name: str,
    config: Optional[RateLimitConfig] = None
):
    """Decorator to apply rate limiting"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter = get_rate_limiter(name, config)
            return limiter.call(func, *args, **kwargs)
        return wrapper
    return decorator


def get_all_metrics() -> dict:
    """Get metrics from all resilience components"""
    metrics = {
        "circuit_breakers": {},
        "rate_limiters": {},
        "error_budgets": {},
        "timestamp": time.time()
    }

    # Circuit breaker states
    for name, cb in _circuit_breakers.items():
        metrics["circuit_breakers"][name] = cb.get_state()

    # Rate limiter states
    for name, rl in _rate_limiters.items():
        metrics["rate_limiters"][name] = rl.get_state()

    # Error budget metrics
    for name, monitor in _error_budget_monitors.items():
        metrics["error_budgets"][name] = monitor.get_metrics()

    return metrics


def reset_all_metrics():
    """Reset all resilience component metrics (for testing)"""
    global _circuit_breakers, _retry_policies, _rate_limiters, _error_budget_monitors

    with _global_lock:
        _circuit_breakers.clear()
        _retry_policies.clear()
        _rate_limiters.clear()
        _error_budget_monitors.clear()

        logger.info("All resilience metrics reset")