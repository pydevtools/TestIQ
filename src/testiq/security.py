"""
Security utilities for TestIQ.
Provides input validation, sanitization, and security checks.
"""

import hashlib
from pathlib import Path
from typing import Any

from testiq.exceptions import SecurityError, ValidationError

# Default security constants (can be overridden by config)
# These match the defaults in config.SecurityConfig
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_TESTS = 50000
MAX_LINES_PER_FILE = 100000
ALLOWED_EXTENSIONS = {".json", ".yaml", ".yml"}

# Dangerous path patterns for security validation
DANGEROUS_PATTERNS = {"../", "..\\", "~"}


def validate_file_path(file_path: Path, check_exists: bool = True) -> Path:
    """
    Validate and sanitize file path.

    Args:
        file_path: Path to validate
        check_exists: Whether to check if file exists

    Returns:
        Resolved absolute path

    Raises:
        SecurityError: If path is dangerous
        ValidationError: If path is invalid
    """
    try:
        # Resolve to absolute path
        resolved = file_path.resolve()

        # Check for path traversal attempts
        path_str = str(file_path)
        for pattern in DANGEROUS_PATTERNS:
            if pattern in path_str:
                raise SecurityError(f"Dangerous path pattern detected: {pattern}")

        # Check if path escapes intended directory
        # (This is a basic check, adjust based on your security requirements)
        if check_exists and not resolved.exists():
            raise ValidationError(f"File does not exist: {file_path}")

        # Check file extension
        if resolved.suffix.lower() not in ALLOWED_EXTENSIONS:
            raise SecurityError(
                f"File extension not allowed: {resolved.suffix}. "
                f"Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        return resolved

    except (OSError, RuntimeError) as e:
        raise ValidationError(f"Invalid file path: {file_path} - {e}")


def check_file_size(file_path: Path, max_size: int = MAX_FILE_SIZE) -> None:
    """
    Check if file size is within limits.

    Args:
        file_path: Path to check
        max_size: Maximum allowed size in bytes

    Raises:
        SecurityError: If file is too large
    """
    try:
        file_size = file_path.stat().st_size
        if file_size > max_size:
            size_mb = file_size / (1024 * 1024)
            max_mb = max_size / (1024 * 1024)
            raise SecurityError(f"File too large: {size_mb:.2f}MB exceeds limit of {max_mb:.2f}MB")
    except OSError as e:
        raise ValidationError(f"Cannot check file size: {e}")


def validate_coverage_data(data: dict[str, Any], max_tests: int = MAX_TESTS) -> None:
    """
    Validate coverage data structure and limits.

    Args:
        data: Coverage data dictionary
        max_tests: Maximum number of tests allowed

    Raises:
        ValidationError: If data is invalid
        SecurityError: If limits are exceeded
    """
    if not isinstance(data, dict):
        raise ValidationError("Coverage data must be a dictionary")

    if len(data) == 0:
        raise ValidationError("Coverage data is empty")

    if len(data) > max_tests:
        raise SecurityError(f"Too many tests: {len(data)} exceeds limit of {max_tests}")

    # Validate structure
    for test_name, coverage in data.items():
        if not isinstance(test_name, str):
            raise ValidationError(f"Test name must be string, got: {type(test_name)}")

        if not test_name.strip():
            raise ValidationError("Test name cannot be empty")

        if not isinstance(coverage, dict):
            raise ValidationError(
                f"Coverage for '{test_name}' must be a dictionary, got: {type(coverage)}"
            )

        # Validate each file's coverage
        total_lines = 0
        for file_name, lines in coverage.items():
            if not isinstance(file_name, str):
                raise ValidationError(f"File name must be string, got: {type(file_name)}")

            if not isinstance(lines, list):
                raise ValidationError(
                    f"Coverage lines for '{file_name}' must be a list, got: {type(lines)}"
                )

            total_lines += len(lines)

            # Validate line numbers
            for line_num in lines:
                if not isinstance(line_num, int):
                    raise ValidationError(f"Line number must be integer, got: {type(line_num)}")
                if line_num < 1:
                    raise ValidationError(f"Invalid line number: {line_num} (must be >= 1)")

        # Check total lines limit
        if total_lines > MAX_LINES_PER_FILE:
            raise SecurityError(
                f"Test '{test_name}' covers too many lines: {total_lines} "
                f"exceeds limit of {MAX_LINES_PER_FILE}"
            )


def sanitize_output_path(output_path: Path, allowed_dirs: list[Path] = None) -> Path:
    """
    Sanitize output file path.

    Args:
        output_path: Path to sanitize
        allowed_dirs: List of allowed directories (if None, any directory is allowed)

    Returns:
        Sanitized absolute path

    Raises:
        SecurityError: If path is not allowed
    """
    try:
        resolved = output_path.resolve()

        # Check for dangerous patterns
        path_str = str(output_path)
        for pattern in DANGEROUS_PATTERNS:
            if pattern in path_str:
                raise SecurityError(f"Dangerous path pattern detected: {pattern}")

        # Check allowed directories
        if allowed_dirs:
            allowed = False
            for allowed_dir in allowed_dirs:
                try:
                    resolved.relative_to(allowed_dir.resolve())
                    allowed = True
                    break
                except ValueError:
                    continue

            if not allowed:
                raise SecurityError(f"Output path not in allowed directories: {output_path}")

        return resolved

    except (OSError, RuntimeError) as e:
        raise ValidationError(f"Invalid output path: {output_path} - {e}")


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of file for integrity verification.
    
    This function is primarily used for file integrity checks and cache validation.
    Can be used to verify that coverage files haven't been tampered with.

    Args:
        file_path: Path to file

    Returns:
        Hexadecimal hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
