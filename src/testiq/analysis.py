"""
Advanced analysis features for TestIQ.
Provides test quality scoring and intelligent recommendations.
"""

from dataclasses import dataclass
from typing import Any, Optional

from testiq.analyzer import CoverageDuplicateFinder
from testiq.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class QualityScore:
    """Quality score for test suite."""

    overall_score: float  # 0-100
    duplication_score: float  # 0-100 (100 = no duplicates)
    coverage_efficiency_score: float  # 0-100
    uniqueness_score: float  # 0-100
    grade: str  # A+, A, B, C, D, F
    recommendations: list[str]

    def __str__(self) -> str:
        """String representation."""
        return f"Quality Score: {self.overall_score:.1f}/100 (Grade: {self.grade})"


class QualityAnalyzer:
    """
    Analyze test suite quality and calculate quality scores.
    
    Responsibilities:
    - Calculate quality metrics (duplication, efficiency, uniqueness)
    - Assign letter grades (A+ to F)
    - Generate text recommendations
    
    For structured action items and detailed reports, use RecommendationEngine.
    """

    def __init__(self, finder: CoverageDuplicateFinder) -> None:
        """Initialize quality analyzer."""
        self.finder = finder

    def calculate_score(self, threshold: float = 0.3) -> QualityScore:
        """
        Calculate comprehensive quality score.

        Args:
            threshold: Similarity threshold for analysis

        Returns:
            QualityScore with detailed metrics
        """
        logger.info("Calculating test quality score")

        exact_dups = self.finder.find_exact_duplicates()
        subset_dups = self.finder.find_subset_duplicates()
        similar = self.finder.find_similar_coverage(threshold)

        total_tests = len(self.finder.tests)
        if total_tests == 0:
            return QualityScore(
                overall_score=0,
                duplication_score=0,
                coverage_efficiency_score=0,
                uniqueness_score=0,
                grade="F",
                recommendations=["No tests found"],
            )

        duplicate_count = sum(len(g) - 1 for g in exact_dups)

        # Calculate duplication score (100 = no duplicates)
        duplicate_percentage = (duplicate_count / total_tests) * 100
        duplication_score = max(0, 100 - (duplicate_percentage * 2))

        # Calculate coverage efficiency score (penalize subsets)
        subset_percentage = (len(subset_dups) / total_tests) * 100 if total_tests > 0 else 0
        coverage_efficiency_score = max(0, 100 - subset_percentage)

        # Calculate uniqueness score (penalize similar tests)
        similar_percentage = (len(similar) / (total_tests * (total_tests - 1) / 2)) * 100 if total_tests > 1 else 0
        uniqueness_score = max(0, 100 - (similar_percentage * 0.5))

        # Overall score (weighted average)
        overall_score = (
            duplication_score * 0.5
            + coverage_efficiency_score * 0.3
            + uniqueness_score * 0.2
        )

        # Determine grade
        if overall_score >= 95:
            grade = "A+"
        elif overall_score >= 90:
            grade = "A"
        elif overall_score >= 80:
            grade = "B"
        elif overall_score >= 70:
            grade = "C"
        elif overall_score >= 60:
            grade = "D"
        else:
            grade = "F"

        # Generate recommendations
        recommendations = self._generate_recommendations(
            duplicate_count, len(subset_dups), len(similar), total_tests
        )

        score = QualityScore(
            overall_score=overall_score,
            duplication_score=duplication_score,
            coverage_efficiency_score=coverage_efficiency_score,
            uniqueness_score=uniqueness_score,
            grade=grade,
            recommendations=recommendations,
        )

        logger.info(f"Quality score: {score.overall_score:.1f}/100 (Grade: {grade})")
        return score

    def _add_duplicate_recommendations(
        self, recommendations: list[str], duplicate_count: int, total_tests: int
    ) -> None:
        """Add recommendations for exact duplicates."""
        if duplicate_count <= 0:
            return
        
        percentage = (duplicate_count / total_tests) * 100
        if percentage > 20:
            recommendations.append(
                f"⚠️ CRITICAL: Remove {duplicate_count} exact duplicate tests ({percentage:.1f}% of total)"
            )
        elif percentage > 10:
            recommendations.append(
                f"⚠️ HIGH: Remove {duplicate_count} exact duplicate tests ({percentage:.1f}% of total)"
            )
        else:
            recommendations.append(
                f"📋 Remove {duplicate_count} exact duplicate tests to improve maintainability"
            )

    def _add_subset_recommendations(
        self, recommendations: list[str], subset_count: int, total_tests: int
    ) -> None:
        """Add recommendations for subset duplicates."""
        if subset_count <= 0:
            return
        
        percentage = (subset_count / total_tests) * 100
        if percentage > 15:
            recommendations.append(
                f"⚠️ Review {subset_count} subset duplicates - many tests may be redundant"
            )
        else:
            recommendations.append(
                f"📋 Review {subset_count} subset duplicates for potential consolidation"
            )

    def _add_similar_recommendations(
        self, recommendations: list[str], similar_count: int, total_tests: int
    ) -> None:
        """Add recommendations for similar tests."""
        if similar_count <= 0:
            return
        
        if similar_count > total_tests:
            recommendations.append(
                f"⚠️ Consider refactoring {similar_count} similar test pairs - high overlap detected"
            )
        elif similar_count > total_tests // 2:
            recommendations.append(
                f"📋 Review {similar_count} similar test pairs for possible merging"
            )

    def _add_best_practice_recommendations(
        self, recommendations: list[str], duplicate_count: int, subset_count: int, 
        similar_count: int, total_tests: int
    ) -> None:
        """Add best practice recommendations."""
        # Positive feedback
        if not recommendations:
            recommendations.append("✅ Excellent! No significant test duplication detected")
            recommendations.append("💡 Continue maintaining this high quality standard")

        # Best practices
        if total_tests > 100 and duplicate_count == 0:
            recommendations.append("🌟 Great job maintaining a large test suite without duplicates!")

        if subset_count > 10:
            recommendations.append(
                "💡 Consider using test parametrization to reduce subset duplicates"
            )

        if similar_count > 20:
            recommendations.append(
                "💡 Use shared test fixtures and helper functions to reduce code duplication"
            )

    def _generate_recommendations(
        self,
        duplicate_count: int,
        subset_count: int,
        similar_count: int,
        total_tests: int,
    ) -> list[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []

        # Add all recommendation types
        self._add_duplicate_recommendations(recommendations, duplicate_count, total_tests)
        self._add_subset_recommendations(recommendations, subset_count, total_tests)
        self._add_similar_recommendations(recommendations, similar_count, total_tests)
        self._add_best_practice_recommendations(
            recommendations, duplicate_count, subset_count, similar_count, total_tests
        )

        return recommendations


class RecommendationEngine:
    """
    Generate intelligent, actionable recommendations for test improvement.
    
    Responsibilities:
    - Create priority-based action items (high/medium/low)
    - Generate structured reports with statistics
    - Provide specific remediation steps
    
    Uses QualityAnalyzer internally for score calculation.
    """

    def __init__(self, finder: CoverageDuplicateFinder) -> None:
        """Initialize recommendation engine."""
        self.finder = finder
        self.quality_analyzer = QualityAnalyzer(finder)

    def generate_report(self, threshold: float = 0.3) -> dict[str, Any]:
        """
        Generate comprehensive recommendation report.

        Args:
            threshold: Similarity threshold

        Returns:
            Dictionary with score, recommendations, and action items
        """
        logger.info("Generating recommendations report")

        score = self.quality_analyzer.calculate_score(threshold)
        exact_dups = self.finder.find_exact_duplicates()
        subset_dups = self.finder.find_subset_duplicates()
        similar = self.finder.find_similar_coverage(threshold)
        total_tests = len(self.finder.tests)

        # Priority action items
        action_items = []

        # High priority: exact duplicates
        if exact_dups:
            for i, group in enumerate(exact_dups[:5], 1):
                action_items.append(
                    {
                        "priority": "high",
                        "type": "remove_duplicate",
                        "description": f"Remove duplicate tests in group {i}",
                        "message": f"Remove duplicate tests in group {i}",
                        "tests": group,
                        "impact": f"Reduce test count by {len(group) - 1}",
                    }
                )

        # Medium priority: subset duplicates
        if subset_dups:
            for subset_test, superset_test, ratio in subset_dups[:5]:
                action_items.append(
                    {
                        "priority": "medium",
                        "type": "review_subset",
                        "description": f"Review if '{subset_test}' is needed",
                        "message": f"Review if '{subset_test}' is needed",
                        "tests": [subset_test, superset_test],
                        "details": f"{ratio:.1%} covered by superset",
                    }
                )

        # Low priority: similar tests
        if similar and len(similar) > total_tests // 2:
            action_items.append(
                {
                    "priority": "low",
                    "type": "refactor_similar",
                    "description": "Consider refactoring similar test pairs",
                    "message": "Consider refactoring similar test pairs",
                    "count": len(similar),
                    "suggestion": "Use test parametrization or shared fixtures",
                }
            )

        return {
            "quality_score": {
                "overall": score.overall_score,
                "duplication": score.duplication_score,
                "efficiency": score.coverage_efficiency_score,
                "uniqueness": score.uniqueness_score,
                "grade": score.grade,
            },
            "recommendations": action_items,  # Priority-based action items
            "suggestions": score.recommendations,  # Text recommendations
            "action_items": action_items,  # Keep for backward compatibility
            "statistics": {
                "total_tests": len(self.finder.tests),
                "exact_duplicates": sum(len(g) - 1 for g in exact_dups),
                "subset_duplicates": len(subset_dups),
                "similar_pairs": len(similar),
            },
        }
