"""
Caching layer for performance optimization.

Provides:
- LRU cache for pattern validation results
- Compiled regex pattern cache
- Cache decorator for expensive operations
- Thread-safe cache management
"""

import re
from functools import wraps, lru_cache
from typing import Callable, Any, Dict, Optional
from collections import OrderedDict
import threading


class LRUCache:
    """Thread-safe LRU (Least Recently Used) cache implementation."""

    def __init__(self, max_size: int = 1000):
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of items to store
        """
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0

    def get(self, key: Any) -> Optional[Any]:
        """Get value from cache, moving to end (most recently used)."""
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None

            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]

    def put(self, key: Any, value: Any) -> None:
        """Put value in cache, evicting oldest if full."""
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value

            # Evict oldest if over capacity
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate_percent": hit_rate,
            }


# Global caches
_VALIDATION_CACHE = LRUCache(max_size=5000)
_PATTERN_MATCH_CACHE = LRUCache(max_size=1000)
_COMPILED_REGEX_CACHE: Dict[str, re.Pattern] = {}


def cache_validation(func: Callable) -> Callable:
    """
    Decorator to cache validation function results.

    Caches the result of expensive validation operations like Luhn checksum,
    IBAN validation, etc.

    Args:
        func: Function to cache (takes a single string argument)

    Returns:
        Wrapped function with caching
    """

    @wraps(func)
    def wrapper(value: str) -> Any:
        # Create cache key from function name and value
        cache_key = (func.__name__, value)

        # Check cache
        cached = _VALIDATION_CACHE.get(cache_key)
        if cached is not None:
            return cached

        # Compute result
        result = func(value)

        # Store in cache
        _VALIDATION_CACHE.put(cache_key, result)

        return result

    return wrapper


def cache_pattern_match(func: Callable) -> Callable:
    """
    Decorator to cache pattern matching results.

    Caches results of regex pattern matching operations. Useful for repeated
    scanning of similar text.

    Args:
        func: Function to cache (takes text and patterns as arguments)

    Returns:
        Wrapped function with caching
    """

    @wraps(func)
    def wrapper(text: str, *args, **kwargs) -> Any:
        # Create cache key from function name and text hash
        cache_key = (func.__name__, hash(text))

        # Check cache
        cached = _PATTERN_MATCH_CACHE.get(cache_key)
        if cached is not None:
            return cached

        # Compute result
        result = func(text, *args, **kwargs)

        # Store in cache
        _PATTERN_MATCH_CACHE.put(cache_key, result)

        return result

    return wrapper


def get_compiled_pattern(pattern: str, flags: int = 0) -> re.Pattern:
    """
    Get compiled regex pattern, using cache if available.

    Compiles and caches regex patterns to avoid recompilation overhead.

    Args:
        pattern: Regex pattern string
        flags: Regex compilation flags (re.IGNORECASE, re.UNICODE, etc.)

    Returns:
        Compiled regex pattern
    """
    # Create cache key from pattern and flags
    cache_key = (pattern, flags)

    # Check cache
    if cache_key not in _COMPILED_REGEX_CACHE:
        _COMPILED_REGEX_CACHE[cache_key] = re.compile(pattern, flags)

    return _COMPILED_REGEX_CACHE[cache_key]


def clear_all_caches() -> None:
    """Clear all caches."""
    _VALIDATION_CACHE.clear()
    _PATTERN_MATCH_CACHE.clear()
    _COMPILED_REGEX_CACHE.clear()


def get_cache_stats() -> Dict[str, Any]:
    """Get statistics for all caches."""
    return {
        "validation_cache": _VALIDATION_CACHE.stats(),
        "pattern_match_cache": _PATTERN_MATCH_CACHE.stats(),
        "compiled_regex_cache": len(_COMPILED_REGEX_CACHE),
    }


class SimpleLRUDecorator:
    """
    Simple LRU cache decorator for any function.

    Usage:
        @SimpleLRUDecorator(maxsize=128)
        def expensive_function(x, y):
            return x + y
    """

    def __init__(self, maxsize: int = 128):
        """Initialize decorator."""
        self.maxsize = maxsize

    def __call__(self, func: Callable) -> Callable:
        """Decorate function with LRU cache."""
        # Use functools.lru_cache for simplicity
        return lru_cache(maxsize=self.maxsize)(func)
