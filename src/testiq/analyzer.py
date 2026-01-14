"""
Coverage-based test duplicate detector.
Analyzes test coverage to find redundant tests.
"""

import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

from testiq.exceptions import AnalysisError, ValidationError
from testiq.logging_config import get_logger
from testiq.performance import (
    CacheManager,
    ParallelProcessor,
    ProgressTracker,
    compute_similarity,
)

logger = get_logger(__name__)

# Constants
NO_TESTS_WARNING = "No tests to analyze"


@dataclass
class CoverageData:
    """Represents coverage data for a single test."""

    test_name: str
    covered_lines: set[tuple[str, int]]  # (filename, line_number)

    def __hash__(self) -> int:
        return hash(self.test_name)


class CoverageDuplicateFinder:
    """Finds duplicate tests based on coverage analysis."""

    def __init__(
        self,
        enable_parallel: bool = True,
        max_workers: int = 4,
        enable_caching: bool = True,
        cache_dir: Optional[str] = None,
    ) -> None:
        """
        Initialize the duplicate finder.

        Args:
            enable_parallel: Enable parallel processing
            max_workers: Maximum number of parallel workers
            enable_caching: Enable result caching
            cache_dir: Directory for cache files
        """
        self.tests: list[CoverageData] = []
        self.parallel_processor = ParallelProcessor(
            max_workers=max_workers, enabled=enable_parallel
        )
        self.cache_manager = CacheManager(cache_dir=cache_dir, enabled=enable_caching)
        logger.info(
            f"Initialized CoverageDuplicateFinder (parallel={enable_parallel}, "
            f"caching={enable_caching})"
        )

    def add_test_coverage(self, test_name: str, coverage: dict[str, list[int]]) -> None:
        """
        Add coverage data for a test.

        Args:
            test_name: Name of the test
            coverage: Dict mapping filename -> list of covered line numbers

        Raises:
            ValidationError: If test_name is empty or coverage is invalid
        """
        if not test_name or not test_name.strip():
            raise ValidationError("Test name cannot be empty")

        if not isinstance(coverage, dict):
            raise ValidationError(f"Coverage must be a dict, got {type(coverage)}")

        try:
            covered_lines = set()
            for filename, lines in coverage.items():
                if not isinstance(lines, list):
                    raise ValidationError(
                        f"Coverage lines for '{filename}' must be a list, got {type(lines)}"
                    )
                for line in lines:
                    if not isinstance(line, int) or line < 1:
                        raise ValidationError(f"Invalid line number for '{filename}': {line}")
                    covered_lines.add((filename, line))

            self.tests.append(CoverageData(test_name, covered_lines))
            logger.debug(f"Added test '{test_name}' with {len(covered_lines)} covered lines")

        except Exception as e:
            logger.error(f"Error adding test coverage for '{test_name}': {e}")
            raise

    def find_exact_duplicates(self) -> list[list[str]]:
        """
        Find tests with identical coverage.

        Returns:
            List of test groups where each group has identical coverage

        Raises:
            AnalysisError: If analysis fails
        """
        if not self.tests:
            logger.warning(NO_TESTS_WARNING)
            return []

        logger.info(f"Finding exact duplicates among {len(self.tests)} tests")
        start_time = time.time()

        try:
            coverage_map: dict[frozenset, list[str]] = defaultdict(list)

            for test in self.tests:
                coverage_key = frozenset(test.covered_lines)
                coverage_map[coverage_key].append(test.test_name)

            # Only return groups with more than one test (duplicates)
            duplicates = [tests for tests in coverage_map.values() if len(tests) > 1]

            elapsed = time.time() - start_time
            logger.info(f"Found {len(duplicates)} duplicate groups in {elapsed:.2f}s")
            return duplicates

        except Exception as e:
            logger.error(f"Error finding exact duplicates: {e}")
            raise AnalysisError(f"Failed to find exact duplicates: {e}")

    def find_subset_duplicates(self) -> list[tuple[str, str, float]]:
        """
        Find tests where one is a subset of another.

        Returns:
            List of (subset_test, superset_test, coverage_ratio) tuples

        Raises:
            AnalysisError: If analysis fails
        """
        if not self.tests:
            logger.warning(NO_TESTS_WARNING)
            return []

        logger.info(f"Finding subset duplicates among {len(self.tests)} tests")
        start_time = time.time()

        try:
            subsets = []
            progress = ProgressTracker(len(self.tests), "Subset analysis")

            for i, test1 in enumerate(self.tests):
                for test2 in self.tests[i + 1 :]:
                    if test1.covered_lines == test2.covered_lines:
                        continue  # Skip exact duplicates (handled separately)

                    if test1.covered_lines.issubset(test2.covered_lines):
                        ratio = len(test1.covered_lines) / len(test2.covered_lines)
                        subsets.append((test1.test_name, test2.test_name, ratio))
                    elif test2.covered_lines.issubset(test1.covered_lines):
                        ratio = len(test2.covered_lines) / len(test1.covered_lines)
                        subsets.append((test2.test_name, test1.test_name, ratio))

                if i % 10 == 0:
                    progress.update(10)

            elapsed = time.time() - start_time
            logger.info(f"Found {len(subsets)} subset duplicates in {elapsed:.2f}s")
            return subsets

        except Exception as e:
            logger.error(f"Error finding subset duplicates: {e}")
            raise AnalysisError(f"Failed to find subset duplicates: {e}")

    def get_sorted_subset_duplicates(self) -> list[tuple[str, str, float]]:
        """
        Get subset duplicates sorted by coverage ratio (highest first).

        Returns:
            List of (subset_test, superset_test, coverage_ratio) tuples sorted by ratio
        """
        subsets = self.find_subset_duplicates()
        return sorted(subsets, key=lambda x: x[2], reverse=True)

    def get_duplicate_count(self) -> int:
        """
        Get the total number of duplicate tests that can be removed.

        Returns:
            Number of tests that are exact duplicates (excluding one to keep per group)
        """
        exact_dups = self.find_exact_duplicates()
        return sum(len(g) - 1 for g in exact_dups)

    def get_statistics(self, threshold: float = 0.3) -> dict:
        """
        Get comprehensive statistics about test duplication.

        Args:
            threshold: Similarity threshold for analysis (default: 0.3)

        Returns:
            Dictionary with all statistics
        """
        exact = self.find_exact_duplicates()
        subsets = self.find_subset_duplicates()
        similar = self.find_similar_coverage(threshold)

        return {
            'total_tests': len(self.tests),
            'exact_duplicate_groups': len(exact),
            'exact_duplicate_count': sum(len(g) - 1 for g in exact),
            'subset_duplicate_count': len(subsets),
            'similar_pair_count': len(similar),
            'total_removable_duplicates': sum(len(g) - 1 for g in exact) + len(subsets),
            'threshold': threshold
        }

    def find_similar_coverage(self, threshold: float = 0.8) -> list[tuple[str, str, float]]:
        """
        Find tests with similar (but not identical) coverage using Jaccard similarity.

        Args:
            threshold: Minimum similarity ratio (0.0 to 1.0)

        Returns:
            List of (test1, test2, similarity) tuples

        Raises:
            ValidationError: If threshold is invalid
            AnalysisError: If analysis fails
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValidationError(f"Threshold must be between 0.0 and 1.0, got {threshold}")

        if not self.tests:
            logger.warning(NO_TESTS_WARNING)
            return []

        logger.info(f"Finding similar tests (threshold={threshold}) among {len(self.tests)} tests")
        start_time = time.time()

        try:
            similar = []
            progress = ProgressTracker(len(self.tests), "Similarity analysis")

            for i, test1 in enumerate(self.tests):
                for test2 in self.tests[i + 1 :]:
                    # Use cached similarity computation
                    similarity = compute_similarity(
                        frozenset(test1.covered_lines), frozenset(test2.covered_lines)
                    )

                    if threshold <= similarity < 1.0:
                        similar.append((test1.test_name, test2.test_name, similarity))

                if i % 10 == 0:
                    progress.update(10)

            result = sorted(similar, key=lambda x: x[2], reverse=True)
            elapsed = time.time() - start_time
            logger.info(f"Found {len(result)} similar test pairs in {elapsed:.2f}s")
            return result

        except Exception as e:
            logger.error(f"Error finding similar coverage: {e}")
            raise AnalysisError(f"Failed to find similar coverage: {e}")

    def generate_report(self, threshold: float = 0.3) -> str:
        """
        Generate a comprehensive duplicate report.

        Args:
            threshold: Similarity threshold for analysis (default: 0.3 = 30%)

        Returns:
            Markdown formatted report
        """
        from testiq import __version__
        from datetime import datetime

        report_lines = ["# Test Duplication Report\n"]
        report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"**TestIQ Version:** {__version__}")
        report_lines.append(f"**Similarity Threshold:** {threshold:.1%}\n")

        # Exact duplicates
        exact_dups = self.find_exact_duplicates()
        duplicate_count = self.get_duplicate_count()
        report_lines.append("## Exact Duplicates (Identical Coverage)\n")
        report_lines.append(f"Found {len(exact_dups)} groups with {duplicate_count} duplicate tests:\n")

        for i, group in enumerate(exact_dups, 1):
            report_lines.append(f"\n### Group {i} ({len(group)} tests):")
            for test in group:
                report_lines.append(f"  - {test}")
            report_lines.append(
                f"\n  **Action**: Keep one test, remove {len(group) - 1} duplicates\n"
            )

        # Subset duplicates (sorted by coverage ratio)
        subsets = self.get_sorted_subset_duplicates()
        report_lines.append("\n## Subset Duplicates\n")
        report_lines.append(f"Found {len(subsets)} tests that are subsets of others (showing top 20 by coverage ratio):\n")

        for subset_test, superset_test, ratio in subsets[:20]:  # Top 20
            report_lines.append(
                f"\n  - `{subset_test}` is {ratio:.1%} covered by `{superset_test}`"
            )
            report_lines.append("    **Action**: Consider removing if no unique edge cases\n")

        if len(subsets) > 20:
            report_lines.append(f"\n  ... and {len(subsets) - 20} more subset duplicates\n")

        # Similar coverage
        similar = self.find_similar_coverage(threshold)
        report_lines.append(f"\n## Similar Tests (≥{threshold:.0%} overlap)\n")
        report_lines.append(f"Found {len(similar)} test pairs with ≥{threshold:.0%} similarity (showing top 20):\n")

        for test1, test2, similarity in similar[:20]:  # Top 20
            report_lines.append(f"\n  - `{test1}` ↔ `{test2}`: {similarity:.1%} similar")
            report_lines.append("    **Action**: Review for potential merge or refactoring\n")

        if len(similar) > 20:
            report_lines.append(f"\n  ... and {len(similar) - 20} more similar test pairs\n")

        # Summary statistics
        report_lines.append("\n## Summary\n")
        report_lines.append(f"- Total tests analyzed: {len(self.tests)}")
        report_lines.append(
            f"- Exact duplicates: {duplicate_count} tests can be removed"
        )
        report_lines.append(f"- Subset duplicates: {len(subsets)} tests may be redundant")
        report_lines.append(f"- Similar tests: {len(similar)} pairs need review")

        return "\n".join(report_lines)
