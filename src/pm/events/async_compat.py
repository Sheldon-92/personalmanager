"""Async Compatibility Layer for Event System

Provides seamless async/sync interoperability without breaking existing code.
"""

import asyncio
import threading
from typing import Callable, Any, Optional, Coroutine
from concurrent.futures import ThreadPoolExecutor
import functools


class AsyncCompatibilityBridge:
    """Bridge for handling async operations in both sync and async contexts"""

    _executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="async_compat")
    _event_loops = {}  # Thread ID -> Event Loop mapping

    @classmethod
    def get_or_create_loop(cls) -> asyncio.AbstractEventLoop:
        """Get existing loop or create a new one for the current thread"""
        thread_id = threading.current_thread().ident

        try:
            # Try to get the running loop
            loop = asyncio.get_running_loop()
            return loop
        except RuntimeError:
            # No loop running, check if we have one for this thread
            if thread_id in cls._event_loops:
                loop = cls._event_loops[thread_id]
                if not loop.is_closed():
                    return loop

            # Create new loop for this thread
            loop = asyncio.new_event_loop()
            cls._event_loops[thread_id] = loop
            asyncio.set_event_loop(loop)
            return loop

    @classmethod
    async def run_async_safe(cls, coro: Coroutine) -> Any:
        """Run a coroutine safely in any context"""
        try:
            # Check if we're already in an async context
            loop = asyncio.get_running_loop()
            # We're in an async context, just await the coroutine
            return await coro
        except RuntimeError:
            # We're in a sync context, need to run in event loop
            loop = cls.get_or_create_loop()
            return loop.run_until_complete(coro)

    @classmethod
    def run_sync_safe(cls, func: Callable, *args, **kwargs) -> Any:
        """Run a sync function safely from async context"""
        try:
            loop = asyncio.get_running_loop()
            # We're in async context, run in executor
            return loop.run_in_executor(cls._executor, func, *args, **kwargs)
        except RuntimeError:
            # We're in sync context, just call directly
            return func(*args, **kwargs)

    @classmethod
    def ensure_async(cls, func: Callable) -> Callable:
        """Decorator to ensure a function can be called from any context"""
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                return asyncio.run(func(*args, **kwargs))

            # Return appropriate wrapper based on context
            def context_wrapper(*args, **kwargs):
                try:
                    asyncio.get_running_loop()
                    # In async context
                    return async_wrapper(*args, **kwargs)
                except RuntimeError:
                    # In sync context
                    return sync_wrapper(*args, **kwargs)

            return context_wrapper
        else:
            # Already sync function
            return func

    @classmethod
    def create_task_safe(cls, coro: Coroutine) -> Optional[asyncio.Task]:
        """Create a task safely in any context"""
        try:
            loop = asyncio.get_running_loop()
            return loop.create_task(coro)
        except RuntimeError:
            # No running loop, schedule for later execution
            loop = cls.get_or_create_loop()

            def run_in_thread():
                asyncio.set_event_loop(loop)
                loop.run_until_complete(coro)

            thread = threading.Thread(target=run_in_thread, daemon=True)
            thread.start()
            return None


class EventLoopManager:
    """Manages event loops across different execution contexts"""

    def __init__(self):
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread_loops: dict = {}
        self._lock = threading.Lock()

    def get_loop(self) -> asyncio.AbstractEventLoop:
        """Get appropriate event loop for current context"""
        try:
            # Try to get running loop
            return asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, get or create one
            with self._lock:
                thread_id = threading.current_thread().ident

                if thread_id in self._thread_loops:
                    loop = self._thread_loops[thread_id]
                    if not loop.is_closed():
                        return loop

                # Create new loop for this thread
                loop = asyncio.new_event_loop()
                self._thread_loops[thread_id] = loop

                # Set as current loop for thread
                asyncio.set_event_loop(loop)

                # Start loop in background thread if not main thread
                if threading.current_thread() != threading.main_thread():
                    def run_loop():
                        asyncio.set_event_loop(loop)
                        loop.run_forever()

                    thread = threading.Thread(target=run_loop, daemon=True)
                    thread.start()

                return loop

    def cleanup(self):
        """Clean up all event loops"""
        with self._lock:
            for loop in self._thread_loops.values():
                if not loop.is_closed():
                    loop.call_soon_threadsafe(loop.stop)
                    loop.close()
            self._thread_loops.clear()


# Global instance
_loop_manager = EventLoopManager()


def get_event_loop_safe() -> asyncio.AbstractEventLoop:
    """Get event loop safely in any context"""
    return _loop_manager.get_loop()


def run_async_from_sync(coro: Coroutine) -> Any:
    """Run async code from sync context without conflicts"""
    try:
        # Check if there's already a running loop
        loop = asyncio.get_running_loop()
        # If we're here, we're in async context
        # Create a task and return a future
        task = loop.create_task(coro)
        return task
    except RuntimeError:
        # No running loop, safe to use asyncio.run
        try:
            return asyncio.run(coro)
        except RuntimeError as e:
            if "already running" in str(e):
                # Fallback: run in thread
                result = [None]
                exception = [None]

                def run_in_thread():
                    try:
                        result[0] = asyncio.run(coro)
                    except Exception as e:
                        exception[0] = e

                thread = threading.Thread(target=run_in_thread)
                thread.start()
                thread.join()

                if exception[0]:
                    raise exception[0]
                return result[0]
            raise