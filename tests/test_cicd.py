"""
Tests for CI/CD integration module (quality gates, baselines, trends).
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from testiq.analyzer import CoverageDuplicateFinder
from testiq.cicd import (
    AnalysisResult,
    BaselineManager,
    QualityGate,
    QualityGateChecker,
    TrendTracker,
    get_exit_code,
)


@pytest.fixture
def sample_finder():
    """Create a finder with sample test data."""
    finder = CoverageDuplicateFinder()

    # Add 10 tests with 2 exact duplicates
    for i in range(10):
        coverage = {"file.py": [1, 2, 3, i + 10]}  # Each test is unique
        finder.add_test_coverage(f"test_{i}", coverage)

    # Add exact duplicates (overwrite test_0 and test_1)
    finder.add_test_coverage("test_dup_0", {"file.py": [1, 2, 3, 100]})
    finder.add_test_coverage("test_dup_1", {"file.py": [1, 2, 3, 100]})

    return finder


@pytest.fixture
def sample_result():
    """Create a sample analysis result."""
    return AnalysisResult(
        timestamp=datetime.now().isoformat(),
        total_tests=100,
        exact_duplicates=10,
        duplicate_groups=5,
        subset_duplicates=8,
        similar_pairs=15,
        duplicate_percentage=10.0,
        threshold=0.9,
    )


class TestQualityGate:
    """Tests for QualityGate."""

    def test_default_gate(self):
        """Test default quality gate settings."""
        gate = QualityGate()
        assert gate.max_duplicates is None
        assert gate.max_duplicate_percentage is None
        assert gate.fail_on_increase is True  # Default is True

    def test_custom_gate(self):
        """Test custom quality gate settings."""
        gate = QualityGate(
            max_duplicates=5,
            max_duplicate_percentage=10.0,
            fail_on_increase=True,
        )
        assert gate.max_duplicates == 5
        assert gate.max_duplicate_percentage == pytest.approx(10.0)
        assert gate.fail_on_increase is True


class TestQualityGateChecker:
    """Tests for QualityGateChecker."""

    def test_quality_gate_scenarios(self, sample_finder, sample_result):
        """Test various quality gate pass/fail scenarios."""
        # Test passes with no limits set
        gate_no_limits = QualityGate()
        checker_no_limits = QualityGateChecker(gate_no_limits)
        passed, details = checker_no_limits.check(sample_finder, 0.9)
        assert passed is True
        assert details["passed"] is True
        assert len(details["failures"]) == 0
        
        # Test fails when exceeding max duplicates
        gate_fail_max = QualityGate(max_duplicates=0)
        checker_fail_max = QualityGateChecker(gate_fail_max)
        passed, details = checker_fail_max.check(sample_finder, 0.9)
        assert passed is False
        assert details["passed"] is False
        assert len(details["failures"]) > 0
        assert any("exact duplicates" in f.lower() for f in details["failures"])
        
        # Test passes when under max duplicates
        gate_pass_max = QualityGate(max_duplicates=10)
        checker_pass_max = QualityGateChecker(gate_pass_max)
        passed, _ = checker_pass_max.check(sample_finder, 0.9)
        assert passed is True
        
        # Test fails when exceeding max percentage
        gate_fail_pct = QualityGate(max_duplicate_percentage=5.0)  # 5%
        checker_fail_pct = QualityGateChecker(gate_fail_pct)
        passed, _ = checker_fail_pct.check(sample_finder, 0.9)
        # With 10 tests and 1 duplicate = 10%, should fail 5% limit
        assert passed is False

    def test_fails_on_increase(self, sample_finder, sample_result):
        """Test gate fails when duplicates increase from baseline."""
        # Baseline has 10 duplicates, current has more
        gate = QualityGate(fail_on_increase=True)
        checker = QualityGateChecker(gate)

        # Modify baseline to have fewer duplicates
        baseline = sample_result
        baseline.exact_duplicates = 0

        passed, details = checker.check(sample_finder, 0.9, baseline)

        assert passed is False
        assert any("increased" in f.lower() for f in details["failures"])


class TestBaselineManager:
    """Tests for BaselineManager."""

    def test_save_and_load_baseline(self, sample_result):
        """Test saving and loading a baseline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BaselineManager(Path(tmpdir))

            # Save baseline
            manager.save(sample_result, "test_baseline")

            # Load baseline
            loaded = manager.load("test_baseline")

            assert loaded is not None
            assert loaded.total_tests == sample_result.total_tests
            assert loaded.exact_duplicates == sample_result.exact_duplicates
            assert loaded.duplicate_percentage == sample_result.duplicate_percentage

    def test_load_nonexistent_baseline(self):
        """Test loading a baseline that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BaselineManager(Path(tmpdir))

            loaded = manager.load("nonexistent")
            assert loaded is None

    def test_list_baselines(self, sample_result):
        """Test listing all baselines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BaselineManager(Path(tmpdir))

            # Save multiple baselines
            manager.save(sample_result, "baseline1")
            manager.save(sample_result, "baseline2")

            # List baselines
            baselines = manager.list_baselines()

            assert len(baselines) == 2
            baseline_names = [b["name"] for b in baselines]
            assert "baseline1" in baseline_names
            assert "baseline2" in baseline_names
            # Verify structure includes result objects
            assert all("result" in b for b in baselines)
            assert all(isinstance(b["result"], AnalysisResult) for b in baselines)

    def test_baseline_file_format(self, sample_result):
        """Test that baseline is saved in correct JSON format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BaselineManager(Path(tmpdir))

            manager.save(sample_result, "test")

            # Read raw JSON file
            baseline_file = Path(tmpdir) / "test.json"
            with open(baseline_file) as f:
                data = json.load(f)

            assert "timestamp" in data
            assert "total_tests" in data
            assert "exact_duplicates" in data

    def test_creates_baseline_directory(self):
        """Test that baseline directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_dir = Path(tmpdir) / "new_dir"
            assert not baseline_dir.exists()

            _ = BaselineManager(baseline_dir)
            assert baseline_dir.exists()


class TestTrendTracker:
    """Tests for TrendTracker."""

    def test_add_and_get_history(self, sample_result):
        """Test adding results and getting history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "history.json"
            tracker = TrendTracker(history_file)

            # Add multiple results
            tracker.add_result(sample_result)

            result2 = AnalysisResult(
                timestamp=datetime.now().isoformat(),
                total_tests=110,
                exact_duplicates=8,
                duplicate_groups=4,
                subset_duplicates=6,
                similar_pairs=12,
                duplicate_percentage=7.3,
                threshold=0.9,
            )
            tracker.add_result(result2)

            # Get history
            history = tracker.load_history()

            assert len(history) == 2
            assert history[0]["total_tests"] == 100
            assert history[1]["total_tests"] == 110

    def test_calculate_trend_improving(self):
        """Test trend calculation shows improvement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "history.json"
            tracker = TrendTracker(history_file)

            # Add results showing improvement (fewer duplicates)
            result1 = AnalysisResult(
                timestamp=datetime.now().isoformat(),
                total_tests=100,
                exact_duplicates=20,
                duplicate_groups=10,
                subset_duplicates=15,
                similar_pairs=25,
                duplicate_percentage=20.0,
                threshold=0.9,
            )

            result2 = AnalysisResult(
                timestamp=datetime.now().isoformat(),
                total_tests=100,
                exact_duplicates=10,
                duplicate_groups=5,
                subset_duplicates=8,
                similar_pairs=15,
                duplicate_percentage=10.0,
                threshold=0.9,
            )

            tracker.add_result(result1)
            tracker.add_result(result2)

            # Check if improving
            assert tracker.is_improving("exact_duplicates") is True

    def test_calculate_trend_worsening(self):
        """Test trend calculation shows worsening."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "history.json"
            tracker = TrendTracker(history_file)

            # Add results showing worsening (more duplicates)
            result1 = AnalysisResult(
                timestamp=datetime.now().isoformat(),
                total_tests=100,
                exact_duplicates=5,
                duplicate_groups=3,
                subset_duplicates=4,
                similar_pairs=8,
                duplicate_percentage=5.0,
                threshold=0.9,
            )

            result2 = AnalysisResult(
                timestamp=datetime.now().isoformat(),
                total_tests=100,
                exact_duplicates=15,
                duplicate_groups=8,
                subset_duplicates=12,
                similar_pairs=20,
                duplicate_percentage=15.0,
                threshold=0.9,
            )

            tracker.add_result(result1)
            tracker.add_result(result2)

            # Check if worsening (not improving)
            assert tracker.is_improving("exact_duplicates") is False

    def test_trend_with_insufficient_data(self):
        """Test trend calculation with insufficient data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "history.json"
            tracker = TrendTracker(history_file)

            # Empty history should return True (improving)
            assert tracker.is_improving() is True


class TestGetExitCode:
    """Tests for get_exit_code helper function."""

    def test_exit_code_success(self):
        """Test exit code for successful run with no duplicates."""
        # Success: no duplicates, gate passed
        assert get_exit_code(passed=True, duplicate_count=0, _total_tests=10) == 0

    def test_exit_code_duplicates_found(self):
        """Test exit code when duplicates are found."""
        # Duplicates found but gate passed
        assert get_exit_code(passed=True, duplicate_count=5, _total_tests=10) == 1

    def test_exit_code_gate_failed(self):
        """Test exit code when quality gate fails."""
        # Gate failed
        assert get_exit_code(passed=False, duplicate_count=10, _total_tests=10) == 2

    def test_exit_code_gate_failed_priority(self):
        """Test that gate failure takes priority over duplicates."""
        # Gate failure (2) should override duplicates found (1)
        assert get_exit_code(passed=False, duplicate_count=5, _total_tests=10) == 2
        assert get_exit_code(passed=False, duplicate_count=0, _total_tests=10) == 2
