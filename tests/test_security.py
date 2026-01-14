"""
Tests for security module.
"""

import tempfile
from pathlib import Path

import pytest

from testiq.exceptions import SecurityError, ValidationError
from testiq.security import (
    ALLOWED_EXTENSIONS,
    DANGEROUS_PATTERNS,
    MAX_FILE_SIZE,
    MAX_LINES_PER_FILE,
    MAX_TESTS,
    check_file_size,
    compute_file_hash,
    sanitize_output_path,
    validate_coverage_data,
    validate_file_path,
)


class TestValidateFilePath:
    """Test validate_file_path function."""

    def test_valid_json_file(self, tmp_path):
        """Test valid JSON file path."""
        test_file = tmp_path / "test.json"
        test_file.write_text("{}")
        result = validate_file_path(test_file, check_exists=True)
        assert result.exists()
        assert result.suffix == ".json"

    def test_valid_yaml_file(self, tmp_path):
        """Test valid YAML file path."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("key: value")
        result = validate_file_path(test_file, check_exists=True)
        assert result.exists()
        assert result.suffix == ".yaml"

    def test_valid_yml_file(self, tmp_path):
        """Test valid YML file path."""
        test_file = tmp_path / "test.yml"
        test_file.write_text("key: value")
        result = validate_file_path(test_file, check_exists=True)
        assert result.exists()
        assert result.suffix == ".yml"

    def test_nonexistent_file_with_check(self, tmp_path):
        """Test nonexistent file with check_exists=True."""
        test_file = tmp_path / "missing.json"
        with pytest.raises(ValidationError, match="File does not exist"):
            validate_file_path(test_file, check_exists=True)

    def test_nonexistent_file_without_check(self, tmp_path):
        """Test nonexistent file with check_exists=False."""
        test_file = tmp_path / "missing.json"
        result = validate_file_path(test_file, check_exists=False)
        assert result.suffix == ".json"

    def test_dangerous_path_patterns(self, tmp_path):
        """Test detection of various dangerous path patterns."""
        # Test 1: Path traversal attack
        dangerous_file = tmp_path / "../../../etc/passwd.json"
        with pytest.raises(SecurityError, match="Dangerous path pattern detected"):
            validate_file_path(dangerous_file, check_exists=False)

        # Test 2: Tilde expansion pattern
        tilde_file = Path("~/test.json")
        with pytest.raises(SecurityError, match="Dangerous path pattern detected"):
            validate_file_path(tilde_file, check_exists=False)

    def test_invalid_extension(self, tmp_path):
        """Test rejection of invalid file extensions."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        with pytest.raises(SecurityError, match="File extension not allowed"):
            validate_file_path(test_file, check_exists=True)

    def test_dangerous_pattern_windows_backslash(self, tmp_path):
        """Test detection of Windows-style path traversal."""
        # Create a file with backslash in name (Unix allows this)
        try:
            dangerous_file = tmp_path / "..\\test.json"
            with pytest.raises(SecurityError, match="Dangerous path pattern detected"):
                validate_file_path(dangerous_file, check_exists=False)
        except (OSError, ValueError):
            # Some filesystems don't allow backslashes in filenames
            pytest.skip("Filesystem doesn't support backslashes in filenames")




class TestCheckFileSize:
    """Test check_file_size function."""

    def test_file_within_limit(self, tmp_path):
        """Test file within size limit."""
        test_file = tmp_path / "small.json"
        test_file.write_text("x" * 1000)
        # Should not raise
        check_file_size(test_file, max_size=10000)

    def test_file_exceeds_limit(self, tmp_path):
        """Test file exceeding size limit."""
        test_file = tmp_path / "large.json"
        test_file.write_bytes(b"x" * 10000)
        with pytest.raises(SecurityError, match="File too large"):
            check_file_size(test_file, max_size=1000)

    def test_file_at_exact_limit(self, tmp_path):
        """Test file at exact size limit."""
        test_file = tmp_path / "exact.json"
        test_file.write_bytes(b"x" * 1000)
        # Should not raise
        check_file_size(test_file, max_size=1000)

    def test_default_max_size(self, tmp_path):
        """Test default MAX_FILE_SIZE limit."""
        test_file = tmp_path / "test.json"
        test_file.write_text("small")
        # Should not raise with default
        check_file_size(test_file)

    def test_nonexistent_file(self, tmp_path):
        """Test checking size of nonexistent file."""
        test_file = tmp_path / "missing.json"
        with pytest.raises(ValidationError, match="Cannot check file size"):
            check_file_size(test_file)


class TestValidateCoverageData:
    """Test validate_coverage_data function."""

    def test_valid_coverage_scenarios(self):
        """Test valid coverage data in various scenarios."""
        # Test 1: Normal valid coverage data
        data_normal = {
            "test_one": {"file1.py": [1, 2, 3], "file2.py": [10, 20]},
            "test_two": {"file1.py": [4, 5], "file3.py": [1, 2]},
        }
        # Should not raise
        validate_coverage_data(data_normal)

        # Test 2: Valid coverage at line limit
        lines = list(range(1, MAX_LINES_PER_FILE + 1))
        data_limit = {"test_one": {"file.py": lines}}
        # Should not raise
        validate_coverage_data(data_limit)

    def test_empty_coverage_data(self):
        """Test empty coverage data."""
        with pytest.raises(ValidationError, match="Coverage data is empty"):
            validate_coverage_data({})

    def test_non_dict_coverage_data(self):
        """Test non-dict coverage data."""
        with pytest.raises(ValidationError, match="Coverage data must be a dictionary"):
            validate_coverage_data([])

    def test_too_many_tests(self):
        """Test exceeding max tests limit."""
        data = {f"test_{i}": {"file.py": [1, 2]} for i in range(100)}
        with pytest.raises(SecurityError, match="Too many tests"):
            validate_coverage_data(data, max_tests=50)

    def test_non_string_test_name(self):
        """Test non-string test name."""
        data = {123: {"file.py": [1, 2]}}
        with pytest.raises(ValidationError, match="Test name must be string"):
            validate_coverage_data(data)

    def test_empty_test_name(self):
        """Test empty test name."""
        data = {"   ": {"file.py": [1, 2]}}
        with pytest.raises(ValidationError, match="Test name cannot be empty"):
            validate_coverage_data(data)

    def test_non_dict_coverage(self):
        """Test non-dict coverage for a test."""
        data = {"test_one": [1, 2, 3]}
        with pytest.raises(ValidationError, match="must be a dictionary"):
            validate_coverage_data(data)

    def test_invalid_data_types_in_coverage(self):
        """Test validation of invalid data types in coverage data."""
        # Test 1: Non-string file name
        data_bad_filename = {"test_one": {123: [1, 2]}}
        with pytest.raises(ValidationError, match="File name must be string"):
            validate_coverage_data(data_bad_filename)

        # Test 2: Non-list lines
        data_bad_lines = {"test_one": {"file.py": "not a list"}}
        with pytest.raises(ValidationError, match="must be a list"):
            validate_coverage_data(data_bad_lines)

    def test_line_number_validation_scenarios(self):
        """Test comprehensive line number validation scenarios."""
        # Test 1: Non-integer line number
        data_non_int = {"test_one": {"file.py": [1, 2, "3"]}}
        with pytest.raises(ValidationError, match="Line number must be integer"):
            validate_coverage_data(data_non_int)

        # Test 2: Invalid line number (zero)
        data_zero = {"test_one": {"file.py": [1, 2, 0]}}
        with pytest.raises(ValidationError, match="Invalid line number: 0"):
            validate_coverage_data(data_zero)

        # Test 3: Negative line number
        data_negative = {"test_one": {"file.py": [1, 2, -5]}}
        with pytest.raises(ValidationError, match="Invalid line number: -5"):
            validate_coverage_data(data_negative)

    def test_too_many_lines(self):
        """Test exceeding max lines limit."""
        # Create coverage with many lines
        large_lines = list(range(1, 101000))
        data = {"test_one": {"file.py": large_lines}}
        with pytest.raises(SecurityError, match="covers too many lines"):
            validate_coverage_data(data)



class TestSanitizeOutputPath:
    """Test sanitize_output_path function."""

    def test_valid_output_path(self, tmp_path):
        """Test valid output path."""
        output_path = tmp_path / "output.html"
        result = sanitize_output_path(output_path)
        assert result.is_absolute()

    def test_dangerous_pattern_in_path(self, tmp_path):
        """Test detection of dangerous patterns."""
        output_path = tmp_path / "../../../etc/output.html"
        with pytest.raises(SecurityError, match="Dangerous path pattern detected"):
            sanitize_output_path(output_path)

    def test_allowed_directory(self, tmp_path):
        """Test path within allowed directory."""
        allowed_dir = tmp_path / "allowed"
        allowed_dir.mkdir()
        output_path = allowed_dir / "output.html"
        result = sanitize_output_path(output_path, allowed_dirs=[allowed_dir])
        assert result.is_absolute()

    def test_disallowed_directory(self, tmp_path):
        """Test path outside allowed directories."""
        allowed_dir = tmp_path / "allowed"
        allowed_dir.mkdir()
        disallowed_dir = tmp_path / "disallowed"
        disallowed_dir.mkdir()
        output_path = disallowed_dir / "output.html"
        with pytest.raises(SecurityError, match="not in allowed directories"):
            sanitize_output_path(output_path, allowed_dirs=[allowed_dir])

    def test_no_allowed_dirs_restriction(self, tmp_path):
        """Test path when no allowed_dirs restriction is set."""
        output_path = tmp_path / "anywhere" / "output.html"
        result = sanitize_output_path(output_path, allowed_dirs=None)
        assert result.is_absolute()

    def test_multiple_allowed_directories(self, tmp_path):
        """Test path with multiple allowed directories."""
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        output_path = dir2 / "output.html"
        result = sanitize_output_path(output_path, allowed_dirs=[dir1, dir2])
        assert result.is_absolute()


class TestComputeFileHash:
    """Test compute_file_hash function."""

    def test_hash_small_file(self, tmp_path):
        """Test hash computation for small file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        hash1 = compute_file_hash(test_file)
        assert len(hash1) == 64  # SHA-256 produces 64 hex characters
        assert isinstance(hash1, str)

    def test_hash_consistency(self, tmp_path):
        """Test hash is consistent for same content."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        hash1 = compute_file_hash(test_file)
        hash2 = compute_file_hash(test_file)
        assert hash1 == hash2

    def test_hash_different_content(self, tmp_path):
        """Test different content produces different hash."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        hash1 = compute_file_hash(file1)
        hash2 = compute_file_hash(file2)
        assert hash1 != hash2

    def test_hash_large_file(self, tmp_path):
        """Test hash computation for large file (> 4KB chunks)."""
        test_file = tmp_path / "large.txt"
        test_file.write_bytes(b"x" * 10000)
        hash_result = compute_file_hash(test_file)
        assert len(hash_result) == 64

    def test_hash_empty_file(self, tmp_path):
        """Test hash computation for empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")
        hash_result = compute_file_hash(test_file)
        assert len(hash_result) == 64
        # Empty file should have a specific known hash
        assert hash_result == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


class TestConstants:
    """Test security constants."""

    def test_max_file_size(self):
        """Test MAX_FILE_SIZE constant."""
        assert MAX_FILE_SIZE == 100 * 1024 * 1024
        assert MAX_FILE_SIZE == 104857600  # 100MB

    def test_max_tests(self):
        """Test MAX_TESTS constant."""
        assert MAX_TESTS == 50000

    def test_max_lines_per_file(self):
        """Test MAX_LINES_PER_FILE constant."""
        assert MAX_LINES_PER_FILE == 100000

    def test_allowed_extensions(self):
        """Test ALLOWED_EXTENSIONS constant."""
        assert ".json" in ALLOWED_EXTENSIONS
        assert ".yaml" in ALLOWED_EXTENSIONS
        assert ".yml" in ALLOWED_EXTENSIONS
        assert len(ALLOWED_EXTENSIONS) == 3

    def test_dangerous_patterns(self):
        """Test DANGEROUS_PATTERNS constant."""
        assert "../" in DANGEROUS_PATTERNS
        assert "..\\" in DANGEROUS_PATTERNS
        assert "~" in DANGEROUS_PATTERNS
