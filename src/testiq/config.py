"""
Configuration management for TestIQ.
Supports YAML, TOML config files and environment variables.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # Python < 3.11

import yaml

from testiq.exceptions import ConfigurationError


@dataclass
class LogConfig:
    """Logging configuration."""

    level: str = "INFO"
    file: Optional[str] = None
    enable_rotation: bool = True
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


@dataclass
class SecurityConfig:
    """Security configuration."""

    max_file_size: int = 100 * 1024 * 1024  # 100MB
    max_tests: int = 50000
    max_lines_per_file: int = 100000
    allowed_extensions: list[str] = field(default_factory=lambda: [".json", ".yaml", ".yml"])


@dataclass
class PerformanceConfig:
    """Performance configuration."""

    enable_parallel: bool = True
    max_workers: int = 4
    enable_caching: bool = True
    cache_dir: Optional[str] = None


@dataclass
class AnalysisConfig:
    """Analysis configuration."""

    similarity_threshold: float = 0.3
    min_coverage_lines: int = 1
    max_results: int = 1000


@dataclass
class Config:
    """Main TestIQ configuration."""

    log: LogConfig = field(default_factory=LogConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        """Create config from dictionary."""
        return cls(
            log=LogConfig(**data.get("log", {})),
            security=SecurityConfig(**data.get("security", {})),
            performance=PerformanceConfig(**data.get("performance", {})),
            analysis=AnalysisConfig(**data.get("analysis", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "log": {
                "level": self.log.level,
                "file": self.log.file,
                "enable_rotation": self.log.enable_rotation,
                "max_bytes": self.log.max_bytes,
                "backup_count": self.log.backup_count,
            },
            "security": {
                "max_file_size": self.security.max_file_size,
                "max_tests": self.security.max_tests,
                "max_lines_per_file": self.security.max_lines_per_file,
                "allowed_extensions": self.security.allowed_extensions,
            },
            "performance": {
                "enable_parallel": self.performance.enable_parallel,
                "max_workers": self.performance.max_workers,
                "enable_caching": self.performance.enable_caching,
                "cache_dir": self.performance.cache_dir,
            },
            "analysis": {
                "similarity_threshold": self.analysis.similarity_threshold,
                "min_coverage_lines": self.analysis.min_coverage_lines,
                "max_results": self.analysis.max_results,
            },
        }


def load_config_file(config_path: Path) -> dict[str, Any]:
    """
    Load configuration from file.

    Args:
        config_path: Path to config file (.yaml, .yml, or .toml)

    Returns:
        Configuration dictionary

    Raises:
        ConfigurationError: If file cannot be loaded
    """
    if not config_path.exists():
        raise ConfigurationError(f"Config file not found: {config_path}")

    suffix = config_path.suffix.lower()

    try:
        with open(config_path, "rb") as f:
            if suffix in (".yaml", ".yml"):
                data = yaml.safe_load(f)
            elif suffix == ".toml":
                data = tomllib.load(f)
            else:
                raise ConfigurationError(
                    f"Unsupported config file format: {suffix}. "
                    "Supported formats: .yaml, .yml, .toml"
                )

        if not isinstance(data, dict):
            raise ConfigurationError("Config file must contain a dictionary")

        return data

    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML in config file: {e}")
    except tomllib.TOMLDecodeError as e:
        raise ConfigurationError(f"Invalid TOML in config file: {e}")
    except Exception as e:
        raise ConfigurationError(f"Error reading config file: {e}")


def find_config_file(start_path: Path = None) -> Optional[Path]:
    """
    Find config file in current directory or parent directories.

    Args:
        start_path: Starting directory (default: current directory)

    Returns:
        Path to config file or None if not found
    """
    if start_path is None:
        start_path = Path.cwd()

    config_names = [".testiq.yaml", ".testiq.yml", ".testiq.toml", "testiq.yaml", "testiq.yml"]

    # Search current directory and parents
    current = start_path.resolve()
    for _ in range(10):  # Limit search depth
        for config_name in config_names:
            config_path = current / config_name
            if config_path.exists():
                return config_path

        parent = current.parent
        if parent == current:  # Reached root
            break
        current = parent

    return None


def load_config_from_env() -> dict[str, Any]:
    """
    Load configuration from environment variables.

    Environment variables:
        TESTIQ_LOG_LEVEL: Log level
        TESTIQ_LOG_FILE: Log file path
        TESTIQ_MAX_FILE_SIZE: Maximum file size in bytes
        TESTIQ_MAX_TESTS: Maximum number of tests
        TESTIQ_ENABLE_PARALLEL: Enable parallel processing (true/false)
        TESTIQ_MAX_WORKERS: Maximum number of workers
        TESTIQ_SIMILARITY_THRESHOLD: Similarity threshold (0.0-1.0)

    Returns:
        Configuration dictionary
    """
    config: dict[str, Any] = {}

    # Log config
    if "TESTIQ_LOG_LEVEL" in os.environ:
        config.setdefault("log", {})["level"] = os.environ["TESTIQ_LOG_LEVEL"]
    if "TESTIQ_LOG_FILE" in os.environ:
        config.setdefault("log", {})["file"] = os.environ["TESTIQ_LOG_FILE"]

    # Security config
    if "TESTIQ_MAX_FILE_SIZE" in os.environ:
        config.setdefault("security", {})["max_file_size"] = int(os.environ["TESTIQ_MAX_FILE_SIZE"])
    if "TESTIQ_MAX_TESTS" in os.environ:
        config.setdefault("security", {})["max_tests"] = int(os.environ["TESTIQ_MAX_TESTS"])

    # Performance config
    if "TESTIQ_ENABLE_PARALLEL" in os.environ:
        config.setdefault("performance", {})["enable_parallel"] = (
            os.environ["TESTIQ_ENABLE_PARALLEL"].lower() == "true"
        )
    if "TESTIQ_MAX_WORKERS" in os.environ:
        config.setdefault("performance", {})["max_workers"] = int(os.environ["TESTIQ_MAX_WORKERS"])

    # Analysis config
    if "TESTIQ_SIMILARITY_THRESHOLD" in os.environ:
        config.setdefault("analysis", {})["similarity_threshold"] = float(
            os.environ["TESTIQ_SIMILARITY_THRESHOLD"]
        )

    return config


def load_config(config_path: Optional[Path] = None) -> Config:
    """
    Load configuration from file and environment.

    Priority (highest to lowest):
        1. Environment variables
        2. Specified config file
        3. Auto-discovered config file
        4. Default values

    Args:
        config_path: Path to config file (optional)

    Returns:
        TestIQ configuration
    """
    config_data: dict[str, Any] = {}

    # 1. Load from auto-discovered file
    if config_path is None:
        config_path = find_config_file()

    # 2. Load from specified or discovered file
    if config_path:
        file_config = load_config_file(config_path)
        config_data = _deep_merge(config_data, file_config)

    # 3. Override with environment variables
    env_config = load_config_from_env()
    config_data = _deep_merge(config_data, env_config)

    # 4. Create config with defaults
    return Config.from_dict(config_data)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
