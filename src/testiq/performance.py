"""
Performance optimization utilities for TestIQ.
Provides parallel processing, caching, and streaming capabilities.
"""

import hashlib
import json
import pickle
from collections.abc import Iterator
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Optional

from testiq.exceptions import AnalysisError
from testiq.logging_config import get_logger

logger = get_logger(__name__)


class CacheManager:
    """Manages caching of analysis results."""

    def __init__(self, cache_dir: Optional[Path] = None, enabled: bool = True) -> None:
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory for cache files (default: ~/.testiq/cache)
            enabled: Whether caching is enabled
        """
        self.enabled = enabled
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / ".testiq" / "cache"

        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Cache directory: {self.cache_dir}")

    def _get_cache_key(self, data: Any) -> str:
        """Generate cache key from data."""
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]

    def get(self, key: str) -> Optional[Any]:
        """
        Get cached result.

        Args:
            key: Cache key

        Returns:
            Cached data or None if not found
        """
        if not self.enabled:
            return None

        cache_file = self.cache_dir / f"{key}.cache"
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    logger.debug(f"Cache hit: {key}")
                    return pickle.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache {key}: {e}")
                return None
        return None

    def set(self, key: str, value: Any) -> None:
        """
        Store result in cache.

        Args:
            key: Cache key
            value: Data to cache
        """
        if not self.enabled:
            return

        cache_file = self.cache_dir / f"{key}.cache"
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(value, f)
            logger.debug(f"Cached result: {key}")
        except Exception as e:
            logger.warning(f"Failed to save cache {key}: {e}")

    def clear(self) -> None:
        """Clear all cached data."""
        if not self.enabled:
            return

        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()
            logger.info("Cache cleared")
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")


class StreamingJSONParser:
    """Parse large JSON files in streaming fashion."""

    @staticmethod
    def parse_coverage_file(file_path: Path, chunk_size: int = 1024) -> Iterator[tuple[str, dict]]:
        """
        Parse coverage JSON file in chunks.

        Args:
            file_path: Path to JSON file
            chunk_size: Number of tests to yield at once

        Yields:
            (test_name, coverage_data) tuples
        """
        try:
            with open(file_path) as f:
                data = json.load(f)

            if not isinstance(data, dict):
                raise AnalysisError("Coverage file must contain a dictionary")

            items = list(data.items())
            for i in range(0, len(items), chunk_size):
                chunk = items[i : i + chunk_size]
                yield from chunk

        except json.JSONDecodeError as e:
            raise AnalysisError(f"Invalid JSON in coverage file: {e}")
        except Exception as e:
            raise AnalysisError(f"Error reading coverage file: {e}")


class ParallelProcessor:
    """Process tests in parallel for better performance."""

    def __init__(
        self, max_workers: int = 4, use_processes: bool = False, enabled: bool = True
    ) -> None:
        """
        Initialize parallel processor.

        Args:
            max_workers: Maximum number of parallel workers
            use_processes: Use ProcessPoolExecutor instead of ThreadPoolExecutor
            enabled: Whether parallel processing is enabled
        """
        self.max_workers = max_workers
        self.use_processes = use_processes
        self.enabled = enabled
        logger.debug(
            f"Parallel processing: enabled={enabled}, workers={max_workers}, "
            f"processes={use_processes}"
        )

    def map(self, func: Callable, items: list[Any], desc: str = "Processing") -> list[Any]:
        """
        Map function over items in parallel.

        Args:
            func: Function to apply to each item
            items: List of items to process
            desc: Description for logging

        Returns:
            List of results
        """
        if not self.enabled or len(items) < 2:
            logger.debug(f"Sequential processing: {len(items)} items")
            return [func(item) for item in items]

        logger.info(f"{desc}: {len(items)} items with {self.max_workers} workers")

        executor_class = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor

        try:
            with executor_class(max_workers=self.max_workers) as executor:
                futures = {executor.submit(func, item): i for i, item in enumerate(items)}
                results = [None] * len(items)

                for future in as_completed(futures):
                    idx = futures[future]
                    try:
                        results[idx] = future.result()
                    except Exception as e:
                        logger.error(f"Error processing item {idx}: {e}")
                        results[idx] = None

                return results

        except Exception as e:
            logger.error(f"Parallel processing failed: {e}. Falling back to sequential.")
            return [func(item) for item in items]


@lru_cache(maxsize=1024)
def compute_similarity(lines1_frozen: frozenset, lines2_frozen: frozenset) -> float:
    """
    Compute Jaccard similarity between two sets of lines (cached).

    Args:
        lines1_frozen: First set of lines (frozenset for hashability)
        lines2_frozen: Second set of lines

    Returns:
        Similarity score (0.0 to 1.0)
    """
    lines1 = set(lines1_frozen)
    lines2 = set(lines2_frozen)

    intersection = lines1 & lines2
    union = lines1 | lines2

    if len(union) == 0:
        return 0.0

    return len(intersection) / len(union)


class ProgressTracker:
    """Track progress of long-running operations."""

    def __init__(self, total: int, desc: str = "Processing") -> None:
        """
        Initialize progress tracker.

        Args:
            total: Total number of items
            desc: Description of operation
        """
        self.total = total
        self.current = 0
        self.desc = desc
        self.last_logged_percent = -1

    def update(self, n: int = 1) -> None:
        """
        Update progress.

        Args:
            n: Number of items processed
        """
        self.current += n
        percent = int((self.current / self.total) * 100)

        # Log at 0%, 25%, 50%, 75%, 100%
        if percent >= self.last_logged_percent + 25 or percent == 100:
            logger.info(f"{self.desc}: {percent}% ({self.current}/{self.total})")
            self.last_logged_percent = percent


def batch_iterator(items: list[Any], batch_size: int) -> Iterator[list[Any]]:
    """
    Iterate over items in batches.

    Args:
        items: List of items
        batch_size: Size of each batch

    Yields:
        Batches of items
    """
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]
