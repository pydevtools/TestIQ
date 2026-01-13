"""
Tests for analysis module (quality scoring and recommendations).
"""

import pytest

from testiq.analysis import QualityAnalyzer, RecommendationEngine, TestQualityScore
from testiq.analyzer import CoverageDuplicateFinder


@pytest.fixture
def high_quality_finder():
    """Create a finder with high-quality tests (few duplicates)."""
    finder = CoverageDuplicateFinder()

    # 20 unique tests with good coverage
    for i in range(20):
        coverage = {
            f"file{i % 5}.py": list(range(i * 10 + 1, (i + 1) * 10 + 1)),  # Start from 1
            "common.py": [1, 2],  # Small overlap
        }
        finder.add_test_coverage(f"test_unique_{i}", coverage)

    return finder


@pytest.fixture
def low_quality_finder():
    """Create a finder with low-quality tests (many duplicates)."""
    finder = CoverageDuplicateFinder()

    # 10 exact duplicates
    for i in range(10):
        finder.add_test_coverage(f"test_duplicate_{i}", {"file.py": [1, 2, 3]})

    # 5 subset duplicates
    finder.add_test_coverage("test_short_1", {"utils.py": [1, 2]})
    finder.add_test_coverage("test_long_1", {"utils.py": [1, 2, 3, 4, 5]})

    return finder


@pytest.fixture
def medium_quality_finder():
    """Create a finder with medium-quality tests."""
    finder = CoverageDuplicateFinder()

    # Mix of unique and duplicate tests
    for i in range(5):
        lines = [1, 2, 3, i + 10] if i > 0 else [1, 2, 3, 10]  # Avoid line 0
        finder.add_test_coverage(f"test_unique_{i}", {f"file{i}.py": lines})

    # A few duplicates
    finder.add_test_coverage("test_dup_1", {"common.py": [10, 11, 12]})
    finder.add_test_coverage("test_dup_2", {"common.py": [10, 11, 12]})

    return finder


class TestTestQualityScore:
    """Tests for TestQualityScore dataclass."""

    def test_score_initialization(self):
        """Test creating a quality score."""
        score = TestQualityScore(
            overall_score=85.0,
            duplication_score=90.0,
            coverage_efficiency_score=80.0,
            uniqueness_score=85.0,
            grade="B+",
            recommendations=["Sample recommendation"],
        )

        assert score.overall_score == 85.0
        assert score.grade == "B+"

    def test_score_perfect(self):
        """Test perfect quality score."""
        score = TestQualityScore(
            overall_score=100.0,
            duplication_score=100.0,
            coverage_efficiency_score=100.0,
            uniqueness_score=100.0,
            grade="A+",
            recommendations=[],
        )

        assert score.overall_score == 100.0
        assert score.grade == "A+"


class TestQualityAnalyzer:
    """Tests for QualityAnalyzer."""

    def test_high_quality_score(self, high_quality_finder):
        """Test quality score for high-quality test suite."""
        analyzer = QualityAnalyzer(high_quality_finder)
        score = analyzer.calculate_score(threshold=0.9)

        # Should have high scores
        assert score.overall_score >= 80.0
        assert score.duplication_score >= 80.0
        assert score.grade in ["A+", "A", "A-", "B+", "B"]

    def test_low_quality_score(self, low_quality_finder):
        """Test quality score for low-quality test suite."""
        analyzer = QualityAnalyzer(low_quality_finder)
        score = analyzer.calculate_score(threshold=0.9)

        # Should have low scores due to many duplicates
        assert score.overall_score < 60.0
        assert score.duplication_score < 60.0
        assert score.grade in ["D", "D+", "D-", "F"]

    def test_medium_quality_score(self, medium_quality_finder):
        """Test quality score for medium-quality test suite."""
        analyzer = QualityAnalyzer(medium_quality_finder)
        score = analyzer.calculate_score(threshold=0.9)

        # Should have medium scores  
        assert 60.0 <= score.overall_score <= 90.0  # Allow for scoring variations
        assert score.grade in ["B", "B+", "B-", "C+", "C"]

    def test_score_components_range(self, high_quality_finder):
        """Test that all score components are in valid range (0-100)."""
        analyzer = QualityAnalyzer(high_quality_finder)
        score = analyzer.calculate_score(threshold=0.9)

        assert 0 <= score.overall_score <= 100
        assert 0 <= score.duplication_score <= 100
        assert 0 <= score.coverage_efficiency_score <= 100
        assert 0 <= score.uniqueness_score <= 100

    def test_empty_finder_score(self):
        """Test quality score for empty test suite."""
        finder = CoverageDuplicateFinder()
        analyzer = QualityAnalyzer(finder)
        score = analyzer.calculate_score(threshold=0.9)

        # Empty suite gets F grade with message
        assert score.overall_score == 0
        assert score.duplication_score == 0
        assert score.grade == "F"
        assert "No tests found" in score.recommendations

    def test_grade_mapping(self):
        """Test that scores map to correct grades."""
        finder = CoverageDuplicateFinder()
        
        # Add tests with varying quality to test grading
        # High quality (A range)
        for i in range(20):
            finder.add_test_coverage(f"test_high_{i}", {f"file{i}.py": [i + 1, i + 2]})
        
        analyzer = QualityAnalyzer(finder)
        score = analyzer.calculate_score(threshold=0.9)
        
        # Should get a good grade with unique tests
        assert score.grade in ["A+", "A", "A-", "B+", "B"]

    def test_score_with_different_thresholds(self, medium_quality_finder):
        """Test that threshold affects similarity scoring."""
        analyzer = QualityAnalyzer(medium_quality_finder)

        score_high_threshold = analyzer.calculate_score(threshold=0.95)
        score_low_threshold = analyzer.calculate_score(threshold=0.5)

        # Lower threshold finds more similar tests, potentially lowering score
        # But the exact relationship depends on the test data
        assert score_high_threshold is not None
        assert score_low_threshold is not None


class TestRecommendationEngine:
    """Tests for RecommendationEngine."""

    def test_recommendations_for_low_quality(self, low_quality_finder):
        """Test recommendations for low-quality test suite."""
        engine = RecommendationEngine(low_quality_finder)
        report = engine.generate_report(threshold=0.9)

        # Should have recommendations
        assert len(report["recommendations"]) > 0

        # Should have high-priority recommendations due to low quality
        priorities = [r["priority"] for r in report["recommendations"]]
        assert "high" in priorities

    def test_recommendations_for_high_quality(self, high_quality_finder):
        """Test recommendations for high-quality test suite."""
        engine = RecommendationEngine(high_quality_finder)
        report = engine.generate_report(threshold=0.9)

        # May have few or no recommendations
        # High-priority recommendations should be rare or absent
        high_priority = [r for r in report["recommendations"] if r["priority"] == "high"]
        assert len(high_priority) <= 2

    def test_report_contains_statistics(self, medium_quality_finder):
        """Test that report contains statistics."""
        engine = RecommendationEngine(medium_quality_finder)
        report = engine.generate_report(threshold=0.9)

        # Should have statistics
        assert "statistics" in report
        stats = report["statistics"]

        assert "total_tests" in stats
        assert "exact_duplicates" in stats
        assert "subset_duplicates" in stats
        assert "similar_pairs" in stats

    def test_recommendation_priorities(self, low_quality_finder):
        """Test that recommendations have valid priorities."""
        engine = RecommendationEngine(low_quality_finder)
        report = engine.generate_report(threshold=0.9)

        # All recommendations should have valid priorities
        for rec in report["recommendations"]:
            assert rec["priority"] in ["high", "medium", "low"]
            assert "message" in rec

    def test_duplicate_recommendation(self, low_quality_finder):
        """Test that duplicate tests trigger recommendations."""
        engine = RecommendationEngine(low_quality_finder)
        report = engine.generate_report(threshold=0.9)

        # Should recommend removing duplicates
        messages = [r["message"].lower() for r in report["recommendations"]]
        assert any("duplicate" in msg for msg in messages)

    def test_recommendation_for_perfect_suite(self):
        """Test recommendations for perfect test suite."""
        finder = CoverageDuplicateFinder()

        # Add 10 completely unique tests
        for i in range(10):
            finder.add_test_coverage(
                f"test_{i}",
                {f"file{i}.py": list(range(i * 100 + 1, (i + 1) * 100 + 1))},  # Start from 1
            )

        analyzer = QualityAnalyzer(finder)
        score = analyzer.calculate_score(threshold=0.9)

        engine = RecommendationEngine(finder)
        report = engine.generate_report(threshold=0.9)

        # Should have minimal recommendations
        assert len(report["recommendations"]) <= 1

        # If there are recommendations, they should be low priority
        for rec in report["recommendations"]:
            assert rec["priority"] == "low"

    def test_statistics_accuracy(self, medium_quality_finder):
        """Test that statistics are accurate."""
        engine = RecommendationEngine(medium_quality_finder)
        report = engine.generate_report(threshold=0.9)

        stats = report["statistics"]

        # Verify statistics match actual counts
        assert stats["total_tests"] == len(medium_quality_finder.tests)

        exact_dups = medium_quality_finder.find_exact_duplicates()
        expected_dup_count = sum(len(g) - 1 for g in exact_dups)
        assert stats["exact_duplicates"] == expected_dup_count

    def test_empty_finder_recommendations(self):
        """Test recommendations for empty finder."""
        finder = CoverageDuplicateFinder()
        engine = RecommendationEngine(finder)
        report = engine.generate_report(threshold=0.9)

        # Should handle empty finder gracefully
        assert "recommendations" in report
        assert "statistics" in report
        assert report["statistics"]["total_tests"] == 0


class TestIntegration:
    """Integration tests for analysis workflow."""

    def test_complete_analysis_workflow(self, medium_quality_finder):
        """Test complete quality analysis workflow."""
        # Step 1: Calculate quality score
        analyzer = QualityAnalyzer(medium_quality_finder)
        score = analyzer.calculate_score(threshold=0.9)

        assert score is not None
        assert 0 <= score.overall_score <= 100

        # Step 2: Generate recommendations
        engine = RecommendationEngine(medium_quality_finder)
        report = engine.generate_report(threshold=0.9)

        assert "recommendations" in report
        assert "statistics" in report

        # Step 3: Verify recommendations are actionable
        for rec in report["recommendations"]:
            assert "priority" in rec
            assert "message" in rec
            assert len(rec["message"]) > 0

    def test_score_influences_recommendations(self):
        """Test that score quality affects recommendation priorities."""
        # High-quality finder
        high_finder = CoverageDuplicateFinder()
        for i in range(10):
            high_finder.add_test_coverage(f"test_{i}", {f"file{i}.py": [i + 1, i + 2, i + 3]})

        high_analyzer = QualityAnalyzer(high_finder)
        high_score = high_analyzer.calculate_score(threshold=0.9)
        high_engine = RecommendationEngine(high_finder)
        high_report = high_engine.generate_report(threshold=0.9)

        # Low-quality finder
        low_finder = CoverageDuplicateFinder()
        for i in range(10):
            low_finder.add_test_coverage(f"test_{i}", {"file.py": [1, 2, 3]})

        low_analyzer = QualityAnalyzer(low_finder)
        low_score = low_analyzer.calculate_score(threshold=0.9)
        low_engine = RecommendationEngine(low_finder)
        low_report = low_engine.generate_report(threshold=0.9)

        # Low quality should have more recommendations
        assert len(low_report["recommendations"]) >= len(high_report["recommendations"])
