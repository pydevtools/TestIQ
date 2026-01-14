"""Tests for coverage converter module."""

import json
import tempfile
from pathlib import Path

import pytest

from testiq.coverage_converter import (
    convert_pytest_contexts,
    convert_pytest_coverage,
)


class TestConvertPytestCoverage:
    """Tests for convert_pytest_coverage function."""

    def test_basic_conversion(self):
        """Test basic conversion of pytest coverage format."""
        coverage_data = {
            "files": {
                "src/module.py": {
                    "executed_lines": [1, 2, 3, 5, 10]
                },
                "src/other.py": {
                    "executed_lines": [1, 4, 7]
                }
            }
        }
        
        result = convert_pytest_coverage(coverage_data)
        
        assert "all_tests_aggregated" in result
        assert len(result["all_tests_aggregated"]) == 2
        assert sorted(result["all_tests_aggregated"]["src/module.py"]) == [1, 2, 3, 5, 10]
        assert sorted(result["all_tests_aggregated"]["src/other.py"]) == [1, 4, 7]

    def test_missing_files_key(self):
        """Test error handling for missing 'files' key."""
        coverage_data = {}
        
        with pytest.raises(ValueError, match="missing 'files' key"):
            convert_pytest_coverage(coverage_data)

    def test_missing_executed_lines(self):
        """Test handling of files without executed_lines."""
        coverage_data = {
            "files": {
                "src/module.py": {
                    "something_else": [1, 2, 3]
                }
            }
        }
        
        result = convert_pytest_coverage(coverage_data)
        assert result == {}

    def test_invalid_executed_lines_type(self):
        """Test handling of non-list executed_lines."""
        coverage_data = {
            "files": {
                "src/module.py": {
                    "executed_lines": "not a list"
                }
            }
        }
        
        result = convert_pytest_coverage(coverage_data)
        assert result == {}

    def test_empty_coverage(self):
        """Test handling of empty coverage data."""
        coverage_data = {"files": {}}
        
        result = convert_pytest_coverage(coverage_data)
        assert result == {}

    def test_line_sorting(self):
        """Test that lines are sorted in output."""
        coverage_data = {
            "files": {
                "src/module.py": {
                    "executed_lines": [10, 5, 1, 3, 2]
                }
            }
        }
        
        result = convert_pytest_coverage(coverage_data)
        assert result["all_tests_aggregated"]["src/module.py"] == [1, 2, 3, 5, 10]


class TestConvertPytestContexts:
    """Tests for convert_pytest_contexts function."""

    def test_with_contexts(self):
        """Test conversion with test contexts available."""
        coverage_data = {
            "meta": {
                "show_contexts": True
            },
            "files": {
                "src/module.py": {
                    "contexts": {
                        "test_foo": [1, 2, 3],
                        "test_bar": [4, 5, 6]
                    }
                }
            }
        }
        
        result = convert_pytest_contexts(coverage_data)
        
        assert "test_foo" in result
        assert "test_bar" in result
        assert result["test_foo"]["src/module.py"] == [1, 2, 3]
        assert result["test_bar"]["src/module.py"] == [4, 5, 6]

    def test_without_contexts(self):
        """Test fallback to aggregated format when no contexts."""
        coverage_data = {
            "meta": {
                "show_contexts": False
            },
            "files": {
                "src/module.py": {
                    "executed_lines": [1, 2, 3]
                }
            }
        }
        
        result = convert_pytest_contexts(coverage_data)
        
        # Should fall back to aggregated format
        assert "all_tests_aggregated" in result

    def test_empty_context_name(self):
        """Test handling of empty context names."""
        coverage_data = {
            "meta": {
                "show_contexts": True
            },
            "files": {
                "src/module.py": {
                    "contexts": {
                        "": [1, 2, 3],
                        "test_foo": [4, 5]
                    }
                }
            }
        }
        
        result = convert_pytest_contexts(coverage_data)
        
        # Empty context should be skipped
        assert "" not in result
        assert "test_foo" in result

    def test_no_contexts_field(self):
        """Test fallback when contexts field is missing."""
        coverage_data = {
            "meta": {
                "show_contexts": True
            },
            "files": {
                "src/module.py": {
                    "executed_lines": [1, 2, 3]
                }
            }
        }
        
        result = convert_pytest_contexts(coverage_data)
        
        # Should fall back to aggregated format
        assert "all_tests_aggregated" in result


class TestCLI:
    """Tests for coverage_converter CLI."""

    def test_basic_conversion_cli(self, tmp_path):
        """Test CLI basic conversion."""
        # Create test coverage file
        coverage_file = tmp_path / "coverage.json"
        coverage_data = {
            "files": {
                "src/module.py": {
                    "executed_lines": [1, 2, 3]
                }
            }
        }
        coverage_file.write_text(json.dumps(coverage_data))
        
        # Import and run CLI
        from testiq.coverage_converter import main
        from click.testing import CliRunner
        
        runner = CliRunner()
        output_file = tmp_path / "output.json"
        result = runner.invoke(main, [str(coverage_file), "-o", str(output_file)])
        
        assert result.exit_code == 0
        assert output_file.exists()
        
        # Verify output
        output_data = json.loads(output_file.read_text())
        assert "all_tests_aggregated" in output_data

    def test_with_contexts_flag(self, tmp_path):
        """Test CLI with --with-contexts flag."""
        # Create test coverage file with contexts
        coverage_file = tmp_path / "coverage.json"
        coverage_data = {
            "meta": {"show_contexts": True},
            "files": {
                "src/module.py": {
                    "contexts": {
                        "test_foo": [1, 2, 3]
                    }
                }
            }
        }
        coverage_file.write_text(json.dumps(coverage_data))
        
        from testiq.coverage_converter import main
        from click.testing import CliRunner
        
        runner = CliRunner()
        output_file = tmp_path / "output.json"
        result = runner.invoke(
            main,
            [str(coverage_file), "-o", str(output_file), "--with-contexts"]
        )
        
        assert result.exit_code == 0
        assert output_file.exists()
        
        # Verify output has contexts
        output_data = json.loads(output_file.read_text())
        assert "test_foo" in output_data

    def test_default_output_filename(self, tmp_path, monkeypatch):
        """Test CLI uses default output filename."""
        # Create test coverage file
        coverage_file = tmp_path / "coverage.json"
        coverage_data = {
            "files": {
                "src/module.py": {
                    "executed_lines": [1, 2, 3]
                }
            }
        }
        coverage_file.write_text(json.dumps(coverage_data))
        
        # Change to tmp directory
        monkeypatch.chdir(tmp_path)
        
        from testiq.coverage_converter import main
        from click.testing import CliRunner
        
        runner = CliRunner()
        result = runner.invoke(main, [str(coverage_file)])
        
        assert result.exit_code == 0
        assert (tmp_path / "testiq_coverage.json").exists()

    def test_invalid_json(self, tmp_path):
        """Test CLI handles invalid JSON."""
        coverage_file = tmp_path / "invalid.json"
        coverage_file.write_text("not valid json")
        
        from testiq.coverage_converter import main
        from click.testing import CliRunner
        
        runner = CliRunner()
        result = runner.invoke(main, [str(coverage_file)])
        
        assert result.exit_code == 1
        assert "Error" in result.output
