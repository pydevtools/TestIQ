"""Tests for TestIQ analyzer module."""

import pytest

from testiq.analyzer import CoverageDuplicateFinder, TestCoverage


class TestCoverageDuplicateFinder:
    """Test suite for CoverageDuplicateFinder class."""

    def test_add_test_coverage(self):
        """Test adding coverage data including single and multiple files."""
        finder = CoverageDuplicateFinder()

        # Test with multiple files
        finder.add_test_coverage("test_1", {"file1.py": [1, 2, 3], "file2.py": [10, 20]})

        assert len(finder.tests) == 1
        assert finder.tests[0].test_name == "test_1"
        assert ("file1.py", 1) in finder.tests[0].covered_lines
        assert ("file2.py", 10) in finder.tests[0].covered_lines
        
        # Test with many files spanning different modules
        finder.add_test_coverage(
            "test_multifile", {"auth.py": [10, 11, 12], "user.py": [5, 6, 7], "db.py": [100, 101]}
        )
        
        assert len(finder.tests) == 2
        assert finder.tests[1].test_name == "test_multifile"
        assert len(finder.tests[1].covered_lines) == 8  # 3 + 3 + 2 lines

    def test_find_exact_duplicates(self):
        """Test finding tests with identical coverage."""
        finder = CoverageDuplicateFinder()

        # Add three tests with identical coverage
        for i in range(1, 4):
            finder.add_test_coverage(f"test_{i}", {"file.py": [1, 2, 3]})

        # Add one different test
        finder.add_test_coverage("test_different", {"file.py": [10, 20]})

        duplicates = finder.find_exact_duplicates()

        assert len(duplicates) == 1
        assert len(duplicates[0]) == 3
        assert set(duplicates[0]) == {"test_1", "test_2", "test_3"}

    def test_find_exact_duplicates_no_duplicates(self):
        """Test when there are no exact duplicates."""
        finder = CoverageDuplicateFinder()

        finder.add_test_coverage("test_1", {"file.py": [1, 2]})
        finder.add_test_coverage("test_2", {"file.py": [3, 4]})

        duplicates = finder.find_exact_duplicates()

        assert len(duplicates) == 0

    def test_find_subset_duplicates(self):
        """Test finding tests where one is a subset of another."""
        finder = CoverageDuplicateFinder()

        finder.add_test_coverage("test_minimal", {"file.py": [1, 2, 3]})

        finder.add_test_coverage("test_complete", {"file.py": [1, 2, 3, 4, 5, 6, 7, 8, 9]})

        subsets = finder.find_subset_duplicates()

        assert len(subsets) == 1
        assert subsets[0][0] == "test_minimal"
        assert subsets[0][1] == "test_complete"
        assert subsets[0][2] == pytest.approx(0.333, rel=0.01)

    def test_find_subset_duplicates_no_subsets(self):
        """Test when there are no subset relationships."""
        finder = CoverageDuplicateFinder()

        finder.add_test_coverage("test_1", {"file.py": [1, 2]})
        finder.add_test_coverage("test_2", {"file.py": [3, 4]})

        subsets = finder.find_subset_duplicates()

        assert len(subsets) == 0

    def test_find_similar_coverage(self):
        """Test finding and sorting tests with similar coverage."""
        finder = CoverageDuplicateFinder()

        # Test with ~67% similarity
        finder.add_test_coverage("test_a", {"file.py": [1, 2, 3, 4, 5]})
        finder.add_test_coverage("test_b", {"file.py": [1, 2, 3, 4, 10]})

        # Test with ~82% similarity (higher)
        finder.add_test_coverage("test_c", {"file.py": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})
        finder.add_test_coverage("test_d", {"file.py": [1, 2, 3, 4, 5, 6, 7, 8, 9, 20]})

        similar = finder.find_similar_coverage(threshold=0.5)

        # Should find both pairs
        assert len(similar) >= 2
        
        # Results should be sorted by similarity (descending)
        if len(similar) >= 2:
            assert similar[0][2] >= similar[1][2]
            # Highest similarity should be ~82%
            assert similar[0][2] > 0.8


    def test_generate_report(self):
        """Test report generation."""
        finder = CoverageDuplicateFinder()

        finder.add_test_coverage("test_1", {"file.py": [1, 2, 3]})
        finder.add_test_coverage("test_2", {"file.py": [1, 2, 3]})

        report = finder.generate_report()

        assert "Test Duplication Report" in report
        assert "Exact Duplicates" in report
        assert "test_1" in report
        assert "test_2" in report
        assert "Summary" in report

    def test_empty_finder(self):
        """Test finder with no tests added."""
        finder = CoverageDuplicateFinder()

        assert len(finder.tests) == 0
        assert finder.find_exact_duplicates() == []
        assert finder.find_subset_duplicates() == []
        assert finder.find_similar_coverage() == []

    def test_similarity_with_threshold(self):
        """Test similarity detection with different threshold values."""
        finder = CoverageDuplicateFinder()

        finder.add_test_coverage("test_1", {"file.py": [1, 2, 3, 4, 5]})
        finder.add_test_coverage("test_2", {"file.py": [1, 2, 3, 4, 10]})

        # With high threshold, should not match (similarity ~67%)
        similar = finder.find_similar_coverage(threshold=0.8)
        assert len(similar) == 0

        # With matching threshold, should find them
        similar = finder.find_similar_coverage(threshold=0.6)
        assert len(similar) == 1
        assert similar[0][2] == pytest.approx(0.667, rel=0.01)


class TestTestCoverage:
    """Test suite for TestCoverage class."""

    def test_test_coverage_creation(self):
        """Test creating a TestCoverage instance."""
        coverage = TestCoverage(
            test_name="test_example", covered_lines={("file.py", 1), ("file.py", 2)}
        )

        assert coverage.test_name == "test_example"
        assert len(coverage.covered_lines) == 2
        assert ("file.py", 1) in coverage.covered_lines

    def test_test_coverage_hash(self):
        """Test that TestCoverage instances are hashable."""
        coverage1 = TestCoverage("test_1", {("file.py", 1)})
        coverage2 = TestCoverage("test_2", {("file.py", 2)})

        # Should be able to add to set
        coverage_set = {coverage1, coverage2}
        assert len(coverage_set) == 2
