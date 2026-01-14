"""
Tests for reporting module (HTML and CSV generators).
"""

import json
import tempfile
from pathlib import Path

import pytest

from testiq.analyzer import CoverageDuplicateFinder
from testiq.reporting import CSVReportGenerator, HTMLReportGenerator


@pytest.fixture
def sample_finder():
    """Create a finder with sample test data."""
    finder = CoverageDuplicateFinder()

    # Exact duplicates
    finder.add_test_coverage("test_login_1", {"auth.py": [1, 2, 3], "user.py": [10, 11]})
    finder.add_test_coverage("test_login_2", {"auth.py": [1, 2, 3], "user.py": [10, 11]})

    # Subset duplicates
    finder.add_test_coverage("test_short", {"utils.py": [5, 6]})
    finder.add_test_coverage("test_long", {"utils.py": [5, 6, 7, 8, 9]})

    # Similar tests
    finder.add_test_coverage("test_similar_1", {"main.py": [1, 2, 3, 4, 5]})
    finder.add_test_coverage("test_similar_2", {"main.py": [1, 2, 3, 4, 10]})

    # Unique test
    finder.add_test_coverage("test_unique", {"other.py": [100, 101, 102]})

    return finder


class TestHTMLReportGenerator:
    """Tests for HTMLReportGenerator."""

    def test_generate_html_report(self, sample_finder):
        """Test generating HTML report with statistics cards."""
        generator = HTMLReportGenerator(sample_finder)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            output_path = Path(f.name)

        try:
            generator.generate(output_path, threshold=0.8)

            # Verify file exists and has content
            assert output_path.exists()
            content = output_path.read_text()

            # Check for key HTML elements
            assert "<!DOCTYPE html>" in content
            assert "<html" in content
            assert "TestIQ Analysis Report" in content
            assert "</html>" in content

            # Check for CSS styling
            assert "<style>" in content
            assert "background:" in content
            assert "gradient" in content.lower()

            # Check for data sections
            assert "Exact Duplicates" in content
            assert "Subset Duplicates" in content
            assert "Similar Tests" in content

            # Check for test names
            assert "test_login_1" in content
            assert "test_login_2" in content
            
            # Check for stats cards structure
            assert "class=\"stats\"" in content
            assert "class=\"stat-card" in content

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_html_report_empty_finder(self):
        """Test HTML report generation with no tests."""
        finder = CoverageDuplicateFinder()
        generator = HTMLReportGenerator(finder)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            output_path = Path(f.name)

        try:
            generator.generate(output_path)

            assert output_path.exists()
            content = output_path.read_text()
            # Check that it shows 0 tests in stats
            assert "<div class=\"stat-value\">0</div>" in content
            assert "No exact duplicates found" in content

        finally:
            if output_path.exists():
                output_path.unlink()


class TestCSVReportGenerator:
    """Tests for CSVReportGenerator."""

    def test_generate_exact_duplicates_csv(self, sample_finder):
        """Test generating CSV for exact duplicates."""
        generator = CSVReportGenerator(sample_finder)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            generator.generate_exact_duplicates(output_path)

            assert output_path.exists()
            content = output_path.read_text()

            # Check CSV headers
            assert "Group" in content
            assert "Test Name" in content

            # Check data
            assert "test_login_1" in content
            assert "test_login_2" in content

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_generate_subset_duplicates_csv(self, sample_finder):
        """Test generating CSV for subset duplicates."""
        generator = CSVReportGenerator(sample_finder)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            generator.generate_subset_duplicates(output_path)

            assert output_path.exists()
            content = output_path.read_text()

            # Check CSV headers
            assert "Subset Test" in content
            assert "Superset Test" in content
            assert "Coverage Ratio" in content

            # Check data
            assert "test_short" in content
            assert "test_long" in content

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_generate_similar_tests_csv(self, sample_finder):
        """Test generating CSV for similar tests."""
        generator = CSVReportGenerator(sample_finder)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            generator.generate_similar_tests(output_path, threshold=0.5)

            assert output_path.exists()
            content = output_path.read_text()

            # Check CSV headers
            assert "Test 1" in content
            assert "Test 2" in content
            assert "Similarity" in content

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_generate_summary_csv(self, sample_finder):
        """Test generating summary CSV."""
        generator = CSVReportGenerator(sample_finder)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            generator.generate_summary(output_path, threshold=0.8)

            assert output_path.exists()
            content = output_path.read_text()

            # Check for summary sections
            assert "Total Tests" in content
            assert "Exact Duplicates" in content
            assert "Subset Duplicates" in content

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_csv_report_empty_finder(self):
        """Test CSV report generation with no tests."""
        finder = CoverageDuplicateFinder()
        generator = CSVReportGenerator(finder)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            generator.generate_summary(output_path)

            assert output_path.exists()
            content = output_path.read_text()
            assert "0" in content  # Should show 0 tests

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_csv_valid_format(self, sample_finder):
        """Test that CSV output is valid and parseable."""
        import csv

        generator = CSVReportGenerator(sample_finder)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            generator.generate_exact_duplicates(output_path)

            # Try to parse the CSV
            with open(output_path, newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)

                # Should have at least one row
                assert len(rows) > 0

                # Check that expected columns exist
                assert "Group" in rows[0]
                assert "Test Name" in rows[0]

        finally:
            if output_path.exists():
                output_path.unlink()
