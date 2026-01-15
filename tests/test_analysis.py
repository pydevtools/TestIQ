"""
Tests for analysis module (quality scoring and recommendations).
"""

import pytest

from testiq.analysis import QualityAnalyzer, RecommendationEngine, QualityScore
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


class TestQualityScoreClass:
    """Tests for QualityScore dataclass."""

    def test_score_initialization(self):
        """Test creating a quality score."""
        score = QualityScore(
            overall_score=85.0,
            duplication_score=90.0,
            coverage_efficiency_score=80.0,
            uniqueness_score=85.0,
            grade="B+",
            recommendations=["Sample recommendation"],
        )

        assert score.overall_score == pytest.approx(85.0)
        assert score.grade == "B+"

    def test_score_perfect(self):
        """Test perfect quality score."""
        score = QualityScore(
            overall_score=100.0,
            duplication_score=100.0,
            coverage_efficiency_score=100.0,
            uniqueness_score=100.0,
            grade="A+",
            recommendations=[],
        )

        assert score.overall_score == pytest.approx(100.0)
        assert score.grade == "A+"


class TestQualityAnalyzer:
    """Tests for QualityAnalyzer."""

    def test_quality_scores_across_all_grades(self, high_quality_finder, low_quality_finder, medium_quality_finder):
        """Test quality scoring across high, medium, and low quality test suites with component validation."""
        # High quality tests
        high_analyzer = QualityAnalyzer(high_quality_finder)
        high_score = high_analyzer.calculate_score(threshold=0.9)
        assert high_score.overall_score >= 80.0
        assert high_score.duplication_score >= 80.0
        assert high_score.grade in ["A+", "A", "A-", "B+", "B"]
        assert 0 <= high_score.overall_score <= 100
        assert 0 <= high_score.duplication_score <= 100
        assert 0 <= high_score.coverage_efficiency_score <= 100
        assert 0 <= high_score.uniqueness_score <= 100
        
        # Low quality tests
        low_analyzer = QualityAnalyzer(low_quality_finder)
        low_score = low_analyzer.calculate_score(threshold=0.9)
        assert low_score.overall_score < 60.0
        assert low_score.duplication_score < 60.0
        assert low_score.grade in ["D", "D+", "D-", "F"]
        
        # Medium quality with threshold variations
        med_analyzer = QualityAnalyzer(medium_quality_finder)
        med_score = med_analyzer.calculate_score(threshold=0.9)
        assert 60.0 <= med_score.overall_score <= 90.0
        assert med_score.grade in ["B", "B+", "B-", "C+", "C"]
        score_high_threshold = med_analyzer.calculate_score(threshold=0.95)
        score_low_threshold = med_analyzer.calculate_score(threshold=0.5)
        assert score_high_threshold is not None
        assert score_low_threshold is not None
        
        # Verify score ordering
        assert high_score.overall_score > med_score.overall_score > low_score.overall_score

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


class TestRecommendationEngine:
    """Tests for RecommendationEngine."""

    def test_recommendation_engine_scenarios(self, low_quality_finder):
        """Test comprehensive recommendation generation across quality scenarios."""
        # Test 1: Low quality test suite with duplicates
        engine = RecommendationEngine(low_quality_finder)
        report = engine.generate_report(threshold=0.9)

        # Should have recommendations
        assert len(report["recommendations"]) > 0

        # Should have high-priority recommendations due to low quality
        priorities = [r["priority"] for r in report["recommendations"]]
        assert "high" in priorities
        
        # All recommendations should have valid priorities
        for rec in report["recommendations"]:
            assert rec["priority"] in ["high", "medium", "low"]
            assert "message" in rec
        
        # Should recommend removing duplicates
        messages = [r["message"].lower() for r in report["recommendations"]]
        assert any("duplicate" in msg for msg in messages)

        # Test 2: Mixed quality scenarios
        finder_mixed = CoverageDuplicateFinder()
        finder_mixed.add_test_coverage("test_unique_1", {"file1.py": [1, 2, 3]})
        finder_mixed.add_test_coverage("test_unique_2", {"file2.py": [5, 6, 7]})
        finder_mixed.add_test_coverage("test_dup_1", {"common.py": [10, 11]})
        finder_mixed.add_test_coverage("test_dup_2", {"common.py": [10, 11]})
        
        engine_mixed = RecommendationEngine(finder_mixed)
        report_mixed = engine_mixed.generate_report(threshold=0.9)
        
        assert "recommendations" in report_mixed
        assert "statistics" in report_mixed
        assert len(report_mixed["recommendations"]) > 0

    def test_comprehensive_recommendation_workflow(self, high_quality_finder, medium_quality_finder):
        """Test complete recommendation engine workflow including quality scoring, statistics, and priority handling."""
        # Test 1: High quality suite with minimal recommendations
        finder = CoverageDuplicateFinder()
        for i in range(10):
            finder.add_test_coverage(
                f"test_{i}",
                {f"file{i}.py": list(range(i * 100 + 1, (i + 1) * 100 + 1))},
            )
        analyzer = QualityAnalyzer(finder)
        score = analyzer.calculate_score(threshold=0.9)
        engine = RecommendationEngine(finder)
        report = engine.generate_report(threshold=0.9)
        assert len(report["recommendations"]) <= 1
        for rec in report["recommendations"]:
            assert rec["priority"] == "low"
        
        # Test 2: Medium quality workflow with statistics
        analyzer2 = QualityAnalyzer(medium_quality_finder)
        score2 = analyzer2.calculate_score(threshold=0.9)
        assert score2 is not None
        assert 0 <= score2.overall_score <= 100
        engine2 = RecommendationEngine(medium_quality_finder)
        report2 = engine2.generate_report(threshold=0.9)
        assert "recommendations" in report2
        assert "statistics" in report2
        stats = report2["statistics"]
        assert stats["total_tests"] == len(medium_quality_finder.tests)
        exact_dups = medium_quality_finder.find_exact_duplicates()
        expected_dup_count = sum(len(g) - 1 for g in exact_dups)
        assert stats["exact_duplicates"] == expected_dup_count
        for rec in report2["recommendations"]:
            assert "priority" in rec
            assert "message" in rec
            assert len(rec["message"]) > 0
        
        # Test 3: Score influences recommendation priorities
        high_finder = CoverageDuplicateFinder()
        for i in range(10):
            high_finder.add_test_coverage(f"test_high_{i}", {f"file{i}.py": [i + 1, i + 2, i + 3]})
        high_engine = RecommendationEngine(high_finder)
        high_report = high_engine.generate_report(threshold=0.9)
        
        low_finder = CoverageDuplicateFinder()
        for i in range(10):
            low_finder.add_test_coverage(f"test_low_{i}", {"file.py": [1, 2, 3]})
        low_engine = RecommendationEngine(low_finder)
        low_report = low_engine.generate_report(threshold=0.9)
        assert len(low_report["recommendations"]) >= len(high_report["recommendations"])

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


