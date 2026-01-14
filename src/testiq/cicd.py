"""
CI/CD integration features for TestIQ.
Provides quality gates, baseline comparison, and trend tracking.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from testiq.analyzer import CoverageDuplicateFinder
from testiq.exceptions import ValidationError
from testiq.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class QualityGate:
    """Define quality gate thresholds for CI/CD."""

    max_duplicates: Optional[int] = None
    max_duplicate_percentage: Optional[float] = None
    max_subset_duplicates: Optional[int] = None
    max_similar_pairs: Optional[int] = None
    fail_on_increase: bool = True

    def __post_init__(self) -> None:
        """Validate quality gate configuration."""
        if self.max_duplicate_percentage is not None:
            if not 0.0 <= self.max_duplicate_percentage <= 100.0:
                raise ValidationError(
                    f"max_duplicate_percentage must be 0-100, got {self.max_duplicate_percentage}"
                )


@dataclass
class AnalysisResult:
    """Results from TestIQ analysis."""

    timestamp: str
    total_tests: int
    exact_duplicates: int
    duplicate_groups: int
    subset_duplicates: int
    similar_pairs: int
    duplicate_percentage: float
    threshold: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "total_tests": self.total_tests,
            "exact_duplicates": self.exact_duplicates,
            "duplicate_groups": self.duplicate_groups,
            "subset_duplicates": self.subset_duplicates,
            "similar_pairs": self.similar_pairs,
            "duplicate_percentage": self.duplicate_percentage,
            "threshold": self.threshold,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnalysisResult":
        """Create from dictionary."""
        return cls(
            timestamp=data["timestamp"],
            total_tests=data["total_tests"],
            exact_duplicates=data["exact_duplicates"],
            duplicate_groups=data["duplicate_groups"],
            subset_duplicates=data["subset_duplicates"],
            similar_pairs=data["similar_pairs"],
            duplicate_percentage=data["duplicate_percentage"],
            threshold=data["threshold"],
            metadata=data.get("metadata", {}),
        )


class QualityGateChecker:
    """Check if analysis results pass quality gates."""

    def __init__(self, gate: QualityGate) -> None:
        """Initialize quality gate checker."""
        self.gate = gate
        logger.info(f"Initialized quality gate: {gate}")

    def check(
        self,
        finder: CoverageDuplicateFinder,
        threshold: float = 0.3,
        baseline: Optional[AnalysisResult] = None,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Check if analysis passes quality gates.

        Args:
            finder: CoverageDuplicateFinder instance
            threshold: Similarity threshold
            baseline: Optional baseline results for comparison

        Returns:
            (passed, details) tuple where passed is bool and details contains information
        """
        logger.info("Checking quality gates")

        exact_dups = finder.find_exact_duplicates()
        subset_dups = finder.find_subset_duplicates()
        similar = finder.find_similar_coverage(threshold)

        total_tests = len(finder.tests)
        duplicate_count = sum(len(g) - 1 for g in exact_dups)
        duplicate_percentage = (
            (duplicate_count / total_tests * 100) if total_tests > 0 else 0
        )

        current = AnalysisResult(
            timestamp=datetime.now().isoformat(),
            total_tests=total_tests,
            exact_duplicates=duplicate_count,
            duplicate_groups=len(exact_dups),
            subset_duplicates=len(subset_dups),
            similar_pairs=len(similar),
            duplicate_percentage=duplicate_percentage,
            threshold=threshold,
        )

        failures = []
        passed = True

        # Check absolute thresholds
        if (
            self.gate.max_duplicates is not None
            and duplicate_count > self.gate.max_duplicates
        ):
            failures.append(
                f"Exact duplicates ({duplicate_count}) exceeds limit ({self.gate.max_duplicates})"
            )
            passed = False

        if (
            self.gate.max_duplicate_percentage is not None
            and duplicate_percentage > self.gate.max_duplicate_percentage
        ):
            failures.append(
                f"Duplicate percentage ({duplicate_percentage:.1f}%) exceeds limit ({self.gate.max_duplicate_percentage:.1f}%)"
            )
            passed = False

        if (
            self.gate.max_subset_duplicates is not None
            and len(subset_dups) > self.gate.max_subset_duplicates
        ):
            failures.append(
                f"Subset duplicates ({len(subset_dups)}) exceeds limit ({self.gate.max_subset_duplicates})"
            )
            passed = False

        if (
            self.gate.max_similar_pairs is not None
            and len(similar) > self.gate.max_similar_pairs
        ):
            failures.append(
                f"Similar pairs ({len(similar)}) exceeds limit ({self.gate.max_similar_pairs})"
            )
            passed = False

        # Check against baseline
        if baseline and self.gate.fail_on_increase:
            if current.exact_duplicates > baseline.exact_duplicates:
                failures.append(
                    f"Exact duplicates increased from {baseline.exact_duplicates} to {current.exact_duplicates}"
                )
                passed = False

            if current.subset_duplicates > baseline.subset_duplicates:
                failures.append(
                    f"Subset duplicates increased from {baseline.subset_duplicates} to {current.subset_duplicates}"
                )
                passed = False

        details = {
            "passed": passed,
            "current": current.to_dict(),
            "baseline": baseline.to_dict() if baseline else None,
            "failures": failures,
            "gate_config": {
                "max_duplicates": self.gate.max_duplicates,
                "max_duplicate_percentage": self.gate.max_duplicate_percentage,
                "max_subset_duplicates": self.gate.max_subset_duplicates,
                "max_similar_pairs": self.gate.max_similar_pairs,
                "fail_on_increase": self.gate.fail_on_increase,
            },
        }

        if passed:
            logger.info("✓ Quality gates passed")
        else:
            logger.warning(f"✗ Quality gates failed: {failures}")

        return passed, details


class BaselineManager:
    """Manage baseline results for comparison."""

    def __init__(self, baseline_dir: Path) -> None:
        """Initialize baseline manager."""
        self.baseline_dir = baseline_dir
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Baseline directory: {baseline_dir}")

    def save(self, result: AnalysisResult, name: str = "baseline") -> Path:
        """Save analysis result as baseline."""
        baseline_file = self.baseline_dir / f"{name}.json"

        with open(baseline_file, "w") as f:
            json.dump(result.to_dict(), f, indent=2)

        logger.info(f"Baseline saved: {baseline_file}")
        return baseline_file

    def load(self, name: str = "baseline") -> Optional[AnalysisResult]:
        """Load baseline result."""
        baseline_file = self.baseline_dir / f"{name}.json"

        if not baseline_file.exists():
            logger.warning(f"Baseline not found: {baseline_file}")
            return None

        with open(baseline_file) as f:
            data = json.load(f)

        logger.info(f"Baseline loaded: {baseline_file}")
        return AnalysisResult.from_dict(data)

    def list_baselines(self) -> list[dict[str, Any]]:
        """List available baselines with their details."""
        baselines = []
        for baseline_file in self.baseline_dir.glob("*.json"):
            try:
                result = self.load(baseline_file.stem)
                if result:
                    baselines.append({
                        "name": baseline_file.stem,
                        "result": result,
                    })
            except Exception as e:
                logger.warning(f"Failed to load baseline {baseline_file.stem}: {e}")
        
        logger.debug(f"Available baselines: {[b['name'] for b in baselines]}")
        return baselines


class TrendTracker:
    """Track test duplicate trends over time."""

    def __init__(self, history_file: Path) -> None:
        """Initialize trend tracker."""
        self.history_file = history_file
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

    def add_result(self, result: AnalysisResult) -> None:
        """Add analysis result to history."""
        history = self.load_history()
        history.append(result.to_dict())

        with open(self.history_file, "w") as f:
            json.dump(history, f, indent=2)

        logger.info(f"Result added to trend history: {self.history_file}")

    def load_history(self) -> list[dict[str, Any]]:
        """Load historical results."""
        if not self.history_file.exists():
            return []

        with open(self.history_file) as f:
            return json.load(f)

    def get_trend(self, metric: str, limit: int = 10) -> list[float]:
        """
        Get trend for specific metric.

        Args:
            metric: Metric name (e.g., 'exact_duplicates', 'duplicate_percentage')
            limit: Number of recent results to return

        Returns:
            List of metric values over time
        """
        history = self.load_history()
        recent = history[-limit:] if len(history) > limit else history
        return [r.get(metric, 0) for r in recent]

    def is_improving(self, metric: str = "exact_duplicates") -> bool:
        """Check if trend is improving (decreasing for duplicates)."""
        trend = self.get_trend(metric, limit=5)
        if len(trend) < 2:
            return True  # Not enough data

        # Check if generally decreasing
        improvements = sum(
            1 for i in range(1, len(trend)) if trend[i] <= trend[i - 1]
        )
        return improvements >= len(trend) // 2


def get_exit_code(
    passed: bool, duplicate_count: int, _total_tests: int
) -> int:
    """
    Get appropriate exit code for CI/CD.

    Args:
        passed: Whether quality gates passed
        duplicate_count: Number of duplicates found
        _total_tests: Total number of tests (reserved for future use)

    Returns:
        Exit code (0=success, 1=duplicates found, 2=quality gate failed)
    """
    if not passed:
        return 2  # Quality gate failed

    if duplicate_count > 0:
        return 1  # Duplicates found but within limits

    return 0  # All good
