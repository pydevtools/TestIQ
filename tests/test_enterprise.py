"""Tests for enterprise features: security, logging, config, exceptions."""

from pathlib import Path

import pytest

from testiq.config import Config, load_config, load_config_from_env
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
    """Test security features integration."""

    def test_validate_coverage_data_invalid_structure(self):
        """Test rejecting invalid data structures (integration check)."""
        with pytest.raises(ValidationError, match="must be a dictionary"):
            validate_coverage_data([])

        with pytest.raises(ValidationError, match="must be a dictionary"):
            validate_coverage_data({"test1": []})

        with pytest.raises(ValidationError, match="must be a list"):
            validate_coverage_data({"test1": {"file.py": "not a list"}})


class TestConfig:
    """Test configuration management."""

    def test_default_config(self):
        """Test default configuration values."""
        config = Config()

        assert config.log.level == "INFO"
        assert config.security.max_file_size == 100 * 1024 * 1024
        assert config.performance.enable_parallel is True
        assert config.analysis.similarity_threshold == pytest.approx(0.3)

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "log": {"level": "DEBUG"},
            "security": {"max_tests": 1000},
            "performance": {"max_workers": 8},
            "analysis": {"similarity_threshold": 0.8},
        }

        config = Config.from_dict(data)

        assert config.log.level == "DEBUG"
        assert config.security.max_tests == 1000
        assert config.performance.max_workers == 8
        assert config.analysis.similarity_threshold == pytest.approx(0.8)

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = Config()
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
    """Test performance features integration."""

    def test_compute_similarity(self):
        """Test cached similarity computation."""
        from testiq.performance import compute_similarity

        lines1 = frozenset([("file.py", 1), ("file.py", 2), ("file.py", 3)])
        lines2 = frozenset([("file.py", 2), ("file.py", 3), ("file.py", 4)])

        similarity = compute_similarity(lines1, lines2)

        # Jaccard: intersection=2, union=4, similarity=0.5
        assert similarity == pytest.approx(0.5)


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
