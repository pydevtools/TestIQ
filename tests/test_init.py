"""Tests for main package __init__.py."""

import testiq


class TestPackageInit:
    """Tests for package initialization."""

    def test_version_exists(self):
        """Test that __version__ is defined."""
        assert hasattr(testiq, "__version__")
        assert isinstance(testiq.__version__, str)

    def test_version_format(self):
        """Test version follows semantic versioning format."""
        version = testiq.__version__
        parts = version.split(".")
        assert len(parts) >= 2  # At least major.minor
        assert parts[0].isdigit()
        assert parts[1].isdigit()

    def test_exports_coverage_duplicate_finder(self):
        """Test that CoverageDuplicateFinder is exported."""
        assert hasattr(testiq, "CoverageDuplicateFinder")
        assert "CoverageDuplicateFinder" in testiq.__all__

    def test_exports_test_coverage(self):
        """Test that TestCoverage is exported."""
        assert hasattr(testiq, "TestCoverage")
        assert "TestCoverage" in testiq.__all__

    def test_all_list_complete(self):
        """Test that __all__ contains expected exports."""
        expected = {"CoverageDuplicateFinder", "TestCoverage", "__version__"}
        actual = set(testiq.__all__)
        assert expected == actual

    def test_can_instantiate_finder(self):
        """Test that we can instantiate CoverageDuplicateFinder from package."""
        finder = testiq.CoverageDuplicateFinder()
        assert finder is not None

    def test_can_instantiate_test_coverage(self):
        """Test that we can instantiate TestCoverage from package."""
        test_cov = testiq.TestCoverage(
            test_name="test_example",
            covered_lines={"file.py": [1, 2, 3]}
        )
        assert test_cov is not None
        assert test_cov.test_name == "test_example"
