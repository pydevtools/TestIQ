"""Tests for enterprise features: security, logging, config, exceptions."""

from pathlib import Path

import pytest

from testiq.config import TestIQConfig, load_config, load_config_from_env
from testiq.exceptions import (
    AnalysisError,
    ConfigurationError,
    SecurityError,
    ValidationError,
)
from testiq.security import (
    check_file_size,
    sanitize_output_path,
    validate_coverage_data,
    validate_file_path,
)


class TestExceptions:
    """Test custom exceptions."""

    def test_testiq_error(self):
        """Test base TestIQ error."""
        error = ValidationError("Test message")
        assert "VALIDATION_ERROR" in str(error)
        assert "Test message" in str(error)

    def test_error_codes(self):
        """Test different error codes."""
        errors = [
            (ConfigurationError("test"), "CONFIG_ERROR"),
            (ValidationError("test"), "VALIDATION_ERROR"),
            (SecurityError("test"), "SECURITY_ERROR"),
            (AnalysisError("test"), "ANALYSIS_ERROR"),
        ]

        for error, expected_code in errors:
            assert error.error_code == expected_code
            assert expected_code in str(error)


class TestSecurity:
    """Test security features."""

    def test_validate_file_path_valid(self, tmp_path):
        """Test validating a valid file path."""
        test_file = tmp_path / "test.json"
        test_file.write_text("{}")

        validated = validate_file_path(test_file)
        assert validated.exists()
        assert validated.is_absolute()

    def test_validate_file_path_dangerous_pattern(self):
        """Test rejecting dangerous path patterns."""
        with pytest.raises(SecurityError, match="Dangerous path pattern"):
            validate_file_path(Path("../etc/passwd"))

    def test_validate_file_path_invalid_extension(self, tmp_path):
        """Test rejecting invalid file extensions."""
        test_file = tmp_path / "test.exe"
        test_file.write_text("malicious")

        with pytest.raises(SecurityError, match="File extension not allowed"):
            validate_file_path(test_file)

    def test_check_file_size_valid(self, tmp_path):
        """Test accepting valid file size."""
        test_file = tmp_path / "test.json"
        test_file.write_text("{}" * 100)

        # Should not raise
        check_file_size(test_file, max_size=1024)

    def test_check_file_size_too_large(self, tmp_path):
        """Test rejecting too large files."""
        test_file = tmp_path / "test.json"
        test_file.write_text("{}" * 1000)

        with pytest.raises(SecurityError, match="File too large"):
            check_file_size(test_file, max_size=100)

    def test_validate_coverage_data_valid(self):
        """Test validating valid coverage data."""
        data = {
            "test1": {"file.py": [1, 2, 3]},
            "test2": {"file.py": [4, 5, 6]},
        }

        # Should not raise
        validate_coverage_data(data)

    def test_validate_coverage_data_empty(self):
        """Test rejecting empty coverage data."""
        with pytest.raises(ValidationError, match="empty"):
            validate_coverage_data({})

    def test_validate_coverage_data_too_many_tests(self):
        """Test rejecting too many tests."""
        data = {f"test_{i}": {"file.py": [1]} for i in range(1000)}

        with pytest.raises(SecurityError, match="Too many tests"):
            validate_coverage_data(data, max_tests=100)

    def test_validate_coverage_data_invalid_structure(self):
        """Test rejecting invalid data structure."""
        with pytest.raises(ValidationError, match="must be a dictionary"):
            validate_coverage_data([])

        with pytest.raises(ValidationError, match="must be a dictionary"):
            validate_coverage_data({"test1": []})

        with pytest.raises(ValidationError, match="must be a list"):
            validate_coverage_data({"test1": {"file.py": "not a list"}})

    def test_validate_coverage_data_invalid_line_numbers(self):
        """Test rejecting invalid line numbers."""
        with pytest.raises(ValidationError, match="must be integer"):
            validate_coverage_data({"test1": {"file.py": ["1"]}})

        with pytest.raises(ValidationError, match="must be >= 1"):
            validate_coverage_data({"test1": {"file.py": [0]}})

    def test_sanitize_output_path_valid(self, tmp_path):
        """Test sanitizing valid output path."""
        output_file = tmp_path / "output.json"

        sanitized = sanitize_output_path(output_file)
        assert sanitized.is_absolute()

    def test_sanitize_output_path_dangerous(self):
        """Test rejecting dangerous output paths."""
        with pytest.raises(SecurityError, match="Dangerous path pattern"):
            sanitize_output_path(Path("../../../etc/passwd"))


class TestConfig:
    """Test configuration management."""

    def test_default_config(self):
        """Test default configuration values."""
        config = TestIQConfig()

        assert config.log.level == "INFO"
        assert config.security.max_file_size == 100 * 1024 * 1024
        assert config.performance.enable_parallel is True
        assert config.analysis.similarity_threshold == 0.7

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "log": {"level": "DEBUG"},
            "security": {"max_tests": 1000},
            "performance": {"max_workers": 8},
            "analysis": {"similarity_threshold": 0.8},
        }

        config = TestIQConfig.from_dict(data)

        assert config.log.level == "DEBUG"
        assert config.security.max_tests == 1000
        assert config.performance.max_workers == 8
        assert config.analysis.similarity_threshold == 0.8

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = TestIQConfig()
        config.log.level = "DEBUG"

        data = config.to_dict()

        assert data["log"]["level"] == "DEBUG"
        assert "security" in data
        assert "performance" in data
        assert "analysis" in data

    def test_load_config_yaml(self, tmp_path):
        """Test loading YAML config file."""
        config_file = tmp_path / ".testiq.yaml"
        config_file.write_text(
            """
log:
  level: DEBUG
security:
  max_tests: 5000
"""
        )

        config = load_config(config_file)

        assert config.log.level == "DEBUG"
        assert config.security.max_tests == 5000

    def test_load_config_invalid_file(self):
        """Test loading non-existent config file."""
        with pytest.raises(ConfigurationError):
            from testiq.config import load_config_file

            load_config_file(Path("/nonexistent/config.yaml"))

    def test_load_config_from_env(self, monkeypatch):
        """Test loading config from environment variables."""
        monkeypatch.setenv("TESTIQ_LOG_LEVEL", "ERROR")
        monkeypatch.setenv("TESTIQ_MAX_TESTS", "10000")
        monkeypatch.setenv("TESTIQ_ENABLE_PARALLEL", "false")

        env_config = load_config_from_env()

        assert env_config["log"]["level"] == "ERROR"
        assert env_config["security"]["max_tests"] == 10000
        assert env_config["performance"]["enable_parallel"] is False


class TestPerformance:
    """Test performance features."""

    def test_cache_manager(self, tmp_path):
        """Test cache manager."""
        from testiq.performance import CacheManager

        cache = CacheManager(cache_dir=tmp_path, enabled=True)

        # Test set and get
        cache.set("test_key", {"result": "value"})
        result = cache.get("test_key")

        assert result == {"result": "value"}

    def test_cache_manager_disabled(self):
        """Test disabled cache manager."""
        from testiq.performance import CacheManager

        cache = CacheManager(enabled=False)

        cache.set("test_key", {"result": "value"})
        result = cache.get("test_key")

        assert result is None

    def test_parallel_processor(self):
        """Test parallel processor."""
        from testiq.performance import ParallelProcessor

        processor = ParallelProcessor(max_workers=2, enabled=True)

        def square(x):
            return x * x

        items = [1, 2, 3, 4, 5]
        results = processor.map(square, items)

        assert results == [1, 4, 9, 16, 25]

    def test_parallel_processor_disabled(self):
        """Test disabled parallel processor."""
        from testiq.performance import ParallelProcessor

        processor = ParallelProcessor(enabled=False)

        def square(x):
            return x * x

        items = [1, 2, 3, 4, 5]
        results = processor.map(square, items)

        assert results == [1, 4, 9, 16, 25]

    def test_compute_similarity(self):
        """Test cached similarity computation."""
        from testiq.performance import compute_similarity

        lines1 = frozenset([("file.py", 1), ("file.py", 2), ("file.py", 3)])
        lines2 = frozenset([("file.py", 2), ("file.py", 3), ("file.py", 4)])

        similarity = compute_similarity(lines1, lines2)

        # Jaccard: intersection=2, union=4, similarity=0.5
        assert similarity == 0.5


class TestLogging:
    """Test logging configuration."""

    def test_setup_logging(self):
        """Test setting up logging."""
        from testiq.logging_config import setup_logging

        logger = setup_logging(level="DEBUG")

        assert logger.name == "testiq"
        assert logger.level == 10  # DEBUG

    def test_setup_logging_with_file(self, tmp_path):
        """Test setting up logging with file."""
        from testiq.logging_config import setup_logging

        log_file = tmp_path / "test.log"
        logger = setup_logging(level="INFO", log_file=log_file)

        logger.info("Test message")

        assert log_file.exists()
        assert "Test message" in log_file.read_text()

    def test_get_logger(self):
        """Test getting logger instance."""
        from testiq.logging_config import get_logger

        logger = get_logger("testiq.test")

        assert logger.name == "testiq.test"
