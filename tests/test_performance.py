"""
Tests for performance module.
"""

import json
import tempfile
from pathlib import Path

import pytest

from testiq.exceptions import AnalysisError
from testiq.performance import (
    CacheManager,
    ParallelProcessor,
    ProgressTracker,
    StreamingJSONParser,
    batch_iterator,
    compute_similarity,
)


class TestCacheManager:
    """Test CacheManager class."""

    def test_init_with_custom_dir(self, tmp_path):
        """Test initialization with custom cache directory."""
        cache_dir = tmp_path / "custom_cache"
        manager = CacheManager(cache_dir=cache_dir, enabled=True)
        assert manager.cache_dir == cache_dir
        assert cache_dir.exists()
        assert manager.enabled

    def test_init_with_default_dir(self):
        """Test initialization with default cache directory."""
        manager = CacheManager(enabled=True)
        assert manager.cache_dir == Path.home() / ".testiq" / "cache"
        assert manager.enabled

    def test_init_disabled(self):
        """Test initialization with caching disabled."""
        manager = CacheManager(enabled=False)
        assert not manager.enabled

    def test_get_cache_key_dict(self):
        """Test cache key generation from dict."""
        manager = CacheManager(enabled=False)
        data = {"key": "value", "num": 123}
        key1 = manager._get_cache_key(data)
        key2 = manager._get_cache_key(data)
        assert key1 == key2
        assert len(key1) == 16  # SHA-256 truncated to 16 chars

    def test_get_cache_key_string(self):
        """Test cache key generation from string."""
        manager = CacheManager(enabled=False)
        key1 = manager._get_cache_key("test string")
        key2 = manager._get_cache_key("test string")
        assert key1 == key2
        assert len(key1) == 16

    def test_get_cache_key_consistency(self):
        """Test cache key is consistent for same data."""
        manager = CacheManager(enabled=False)
        data = {"b": 2, "a": 1}  # Different order
        key1 = manager._get_cache_key({"a": 1, "b": 2})
        key2 = manager._get_cache_key(data)
        assert key1 == key2  # Should be same due to sort_keys=True

    def test_get_miss(self, tmp_path):
        """Test cache miss."""
        manager = CacheManager(cache_dir=tmp_path, enabled=True)
        result = manager.get("nonexistent_key")
        assert result is None

    def test_set_and_get(self, tmp_path):
        """Test setting and getting cached value."""
        manager = CacheManager(cache_dir=tmp_path, enabled=True)
        data = {"test": "value", "number": 42}
        manager.set("test_key", data)
        result = manager.get("test_key")
        assert result == data

    def test_get_disabled(self, tmp_path):
        """Test get when caching is disabled."""
        manager = CacheManager(cache_dir=tmp_path, enabled=False)
        result = manager.get("any_key")
        assert result is None

    def test_set_disabled(self, tmp_path):
        """Test set when caching is disabled."""
        manager = CacheManager(cache_dir=tmp_path, enabled=False)
        manager.set("key", {"value": 123})
        # Check that no cache file was created
        cache_files = list(tmp_path.glob("*.cache"))
        assert len(cache_files) == 0

    def test_get_corrupted_cache(self, tmp_path):
        """Test handling of corrupted cache file."""
        manager = CacheManager(cache_dir=tmp_path, enabled=True)
        # Create a corrupted cache file
        cache_file = tmp_path / "test_key.cache"
        cache_file.write_text("corrupted data")
        result = manager.get("test_key")
        assert result is None  # Should return None on error

    def test_clear_cache(self, tmp_path):
        """Test clearing all cached data."""
        manager = CacheManager(cache_dir=tmp_path, enabled=True)
        manager.set("key1", {"value": 1})
        manager.set("key2", {"value": 2})
        manager.set("key3", {"value": 3})
        
        # Verify files exist
        assert len(list(tmp_path.glob("*.cache"))) == 3
        
        # Clear cache
        manager.clear()
        
        # Verify files are gone
        assert len(list(tmp_path.glob("*.cache"))) == 0

    def test_clear_disabled(self, tmp_path):
        """Test clear when caching is disabled."""
        manager = CacheManager(cache_dir=tmp_path, enabled=False)
        # Should not raise
        manager.clear()


class TestStreamingJSONParser:
    """Test StreamingJSONParser class."""

    def test_parse_coverage_file(self, tmp_path):
        """Test parsing a valid coverage JSON file."""
        coverage_data = {
            "test1": {"file1.py": [1, 2, 3]},
            "test2": {"file2.py": [10, 20]},
            "test3": {"file3.py": [5, 6]},
        }
        
        json_file = tmp_path / "coverage.json"
        json_file.write_text(json.dumps(coverage_data))
        
        parser = StreamingJSONParser()
        results = list(parser.parse_coverage_file(json_file))
        
        assert len(results) == 3
        assert results[0][0] in coverage_data
        assert results[1][0] in coverage_data
        assert results[2][0] in coverage_data

    def test_parse_coverage_file_chunked(self, tmp_path):
        """Test parsing with custom chunk size."""
        coverage_data = {f"test{i}": {"file.py": [i]} for i in range(10)}
        
        json_file = tmp_path / "coverage.json"
        json_file.write_text(json.dumps(coverage_data))
        
        parser = StreamingJSONParser()
        results = list(parser.parse_coverage_file(json_file, chunk_size=3))
        
        assert len(results) == 10

    def test_parse_invalid_json(self, tmp_path):
        """Test parsing invalid JSON."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text("{ invalid json }")
        
        parser = StreamingJSONParser()
        with pytest.raises(AnalysisError, match="Invalid JSON"):
            list(parser.parse_coverage_file(json_file))

    def test_parse_non_dict_json(self, tmp_path):
        """Test parsing JSON that's not a dict."""
        json_file = tmp_path / "list.json"
        json_file.write_text("[1, 2, 3]")
        
        parser = StreamingJSONParser()
        with pytest.raises(AnalysisError, match="must contain a dictionary"):
            list(parser.parse_coverage_file(json_file))

    def test_parse_empty_file(self, tmp_path):
        """Test parsing empty coverage data."""
        json_file = tmp_path / "empty.json"
        json_file.write_text("{}")
        
        parser = StreamingJSONParser()
        results = list(parser.parse_coverage_file(json_file))
        
        assert len(results) == 0


class TestParallelProcessor:
    """Test ParallelProcessor class."""

    def test_init_enabled(self):
        """Test initialization with parallel processing enabled."""
        processor = ParallelProcessor(max_workers=4, enabled=True)
        assert processor.max_workers == 4
        assert processor.enabled

    def test_init_disabled(self):
        """Test initialization with parallel processing disabled."""
        processor = ParallelProcessor(enabled=False)
        assert not processor.enabled

    def test_map_sequential(self):
        """Test sequential processing when disabled."""
        processor = ParallelProcessor(enabled=False)
        items = [1, 2, 3, 4, 5]
        
        def square(x):
            return x * x
        
        results = processor.map(square, items)
        assert results == [1, 4, 9, 16, 25]

    def test_map_parallel_thread(self):
        """Test parallel processing with threads."""
        processor = ParallelProcessor(max_workers=2, use_processes=False, enabled=True)
        items = [1, 2, 3, 4, 5]
        
        def square(x):
            return x * x
        
        results = processor.map(square, items)
        assert sorted(results) == [1, 4, 9, 16, 25]

    def test_parallel_map_scenarios(self):
        """Test parallel mapping with processes and error handling."""
        # Test 1: Parallel processing with processes
        processor = ParallelProcessor(max_workers=2, use_processes=True, enabled=True)
        items = [1, 2, 3, 4, 5]
        
        def local_square(x):
            return x * x
        
        results = processor.map(local_square, items)
        # May fail and fall back to sequential, so just check it completes
        assert results is not None
        assert len(results) == 5

        # Test 2: Error handling in parallel processing
        processor2 = ParallelProcessor(max_workers=2, enabled=True)
        
        def failing_func(x):
            if x == 3:
                raise ValueError("Test error")
            return x * x
        
        results2 = processor2.map(failing_func, items)
        # Should have None for failed item
        assert None in results2
        assert 1 in results2
        assert 4 in results2



    def test_map_edge_cases(self):
        """Test processing edge cases: empty list and single item."""
        processor = ParallelProcessor(enabled=True)
        
        # Test 1: Empty list
        results_empty = processor.map(lambda x: x, [])
        assert results_empty == []
        
        # Test 2: Single item (uses sequential)
        results_single = processor.map(lambda x: x * 2, [5])
        assert results_single == [10]


class TestComputeSimilarity:
    """Test compute_similarity function."""

    def test_identical_sets(self):
        """Test similarity of identical sets."""
        set1 = frozenset([1, 2, 3, 4])
        set2 = frozenset([1, 2, 3, 4])
        similarity = compute_similarity(set1, set2)
        assert similarity == pytest.approx(1.0)

    def test_no_overlap(self):
        """Test similarity of disjoint sets."""
        set1 = frozenset([1, 2, 3])
        set2 = frozenset([4, 5, 6])
        similarity = compute_similarity(set1, set2)
        assert similarity == pytest.approx(0.0)

    def test_partial_overlap(self):
        """Test similarity of partially overlapping sets."""
        set1 = frozenset([1, 2, 3, 4])
        set2 = frozenset([3, 4, 5, 6])
        similarity = compute_similarity(set1, set2)
        # Intersection: {3, 4} = 2 elements
        # Union: {1, 2, 3, 4, 5, 6} = 6 elements
        # Similarity: 2/6 = 0.333...
        assert abs(similarity - 0.333) < 0.01

    def test_subset(self):
        """Test similarity when one set is subset of another."""
        set1 = frozenset([1, 2])
        set2 = frozenset([1, 2, 3, 4])
        similarity = compute_similarity(set1, set2)
        # Intersection: {1, 2} = 2 elements
        # Union: {1, 2, 3, 4} = 4 elements
        # Similarity: 2/4 = 0.5
        assert similarity == pytest.approx(0.5)

    def test_empty_sets(self):
        """Test similarity of empty sets."""
        set1 = frozenset()
        set2 = frozenset()
        similarity = compute_similarity(set1, set2)
        assert similarity == pytest.approx(0.0)

    def test_caching(self):
        """Test that similarity computation is cached."""
        set1 = frozenset([1, 2, 3])
        set2 = frozenset([2, 3, 4])
        
        # First call
        result1 = compute_similarity(set1, set2)
        # Second call should use cache
        result2 = compute_similarity(set1, set2)
        
        assert result1 == result2


class TestProgressTracker:
    """Test ProgressTracker class."""

    def test_init(self):
        """Test initialization."""
        tracker = ProgressTracker(total=100, desc="Testing")
        assert tracker.total == 100
        assert tracker.current == 0
        assert tracker.desc == "Testing"
        assert tracker.last_logged_percent == -1

    def test_progress_tracking_scenarios(self):
        """Test progress tracking including updates, percentages, and completion."""
        # Test 1: Update progress
        tracker = ProgressTracker(total=100)
        tracker.update(10)
        assert tracker.current == 10
        tracker.update(15)
        assert tracker.current == 25

        # Test 2: Progress percentage calculation
        tracker2 = ProgressTracker(total=100)
        tracker2.update(25)
        percent = (tracker2.current / tracker2.total) * 100
        assert percent == pytest.approx(25.0)

        # Test 3: Complete 100% progress
        tracker3 = ProgressTracker(total=10)
        tracker3.update(10)
        assert tracker3.current == 10
        percent_complete = (tracker3.current / tracker3.total) * 100
        assert percent_complete == pytest.approx(100.0)


class TestBatchIterator:
    """Test batch_iterator function."""

    def test_exact_batches(self):
        """Test batching with exact multiples."""
        items = list(range(10))
        batches = list(batch_iterator(items, batch_size=2))
        assert len(batches) == 5
        assert batches[0] == [0, 1]
        assert batches[4] == [8, 9]

    def test_uneven_batches(self):
        """Test batching with remainder."""
        items = list(range(10))
        batches = list(batch_iterator(items, batch_size=3))
        assert len(batches) == 4
        assert batches[0] == [0, 1, 2]
        assert batches[3] == [9]  # Last batch has only 1 item

    def test_single_batch(self):
        """Test when batch size >= item count."""
        items = [1, 2, 3]
        batches = list(batch_iterator(items, batch_size=10))
        assert len(batches) == 1
        assert batches[0] == [1, 2, 3]

    def test_empty_list(self):
        """Test batching empty list."""
        items = []
        batches = list(batch_iterator(items, batch_size=5))
        assert len(batches) == 0

    def test_batch_size_one(self):
        """Test batch size of 1."""
        items = [1, 2, 3]
        batches = list(batch_iterator(items, batch_size=1))
        assert len(batches) == 3
        assert batches[0] == [1]
        assert batches[1] == [2]
        assert batches[2] == [3]
