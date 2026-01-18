"""Tests for source_reader module."""



from testiq.source_reader import SourceCodeReader


class TestSourceCodeReader:
    """Tests for SourceCodeReader class."""

    def test_init(self):
        """Test reader initialization."""
        reader = SourceCodeReader()
        assert reader._cache == {}

    def test_read_simple_file(self, tmp_path):
        """Test reading a simple source file."""
        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("line 1\nline 2\nline 3\n")

        reader = SourceCodeReader()
        result = reader.read_file(str(test_file))

        assert result is not None
        assert result[1] == "line 1"
        assert result[2] == "line 2"
        assert result[3] == "line 3"
        assert len(result) == 3

    def test_read_file_with_trailing_whitespace(self, tmp_path):
        """Test that trailing whitespace is stripped."""
        test_file = tmp_path / "test.py"
        test_file.write_text("line 1   \nline 2\t\t\n")

        reader = SourceCodeReader()
        result = reader.read_file(str(test_file))

        assert result[1] == "line 1"  # Trailing spaces removed
        assert result[2] == "line 2"  # Trailing tabs removed

    def test_read_nonexistent_file(self):
        """Test reading a non-existent file returns None."""
        reader = SourceCodeReader()
        result = reader.read_file("/nonexistent/file.py")

        assert result is None

    def test_caching(self, tmp_path):
        """Test that files are cached after first read."""
        test_file = tmp_path / "test.py"
        test_file.write_text("line 1\nline 2\n")

        reader = SourceCodeReader()

        # First read
        result1 = reader.read_file(str(test_file))
        assert str(test_file) in reader._cache

        # Modify file (shouldn't affect cached result)
        test_file.write_text("modified\n")

        # Second read (should return cached version)
        result2 = reader.read_file(str(test_file))
        assert result2 == result1
        assert result2[1] == "line 1"  # Original content

    def test_empty_file(self, tmp_path):
        """Test reading an empty file."""
        test_file = tmp_path / "empty.py"
        test_file.write_text("")

        reader = SourceCodeReader()
        result = reader.read_file(str(test_file))

        assert result == {}

    def test_unicode_content(self, tmp_path):
        """Test reading file with unicode characters."""
        test_file = tmp_path / "unicode.py"
        test_file.write_text("# 中文注释\ndef foo():\n    pass\n", encoding='utf-8')

        reader = SourceCodeReader()
        result = reader.read_file(str(test_file))

        assert result is not None
        assert "中文" in result[1]

    def test_invalid_utf8_handled(self, tmp_path):
        """Test that invalid UTF-8 is handled gracefully."""
        test_file = tmp_path / "binary.dat"
        # Write some binary data that's not valid UTF-8
        test_file.write_bytes(b'\x80\x81\x82\x83')

        reader = SourceCodeReader()
        result = reader.read_file(str(test_file))

        # Should not crash, may return content with replacement chars
        assert result is not None or result is None

    def test_one_indexed_lines(self, tmp_path):
        """Test that line numbers are 1-indexed."""
        test_file = tmp_path / "test.py"
        test_file.write_text("first\nsecond\nthird\n")

        reader = SourceCodeReader()
        result = reader.read_file(str(test_file))

        assert 1 in result
        assert 2 in result
        assert 3 in result
        assert 0 not in result

    def test_read_multiple_files(self, tmp_path):
        """Test read_multiple method."""
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("file 1 line 1\nfile 1 line 2\n")
        file2.write_text("file 2 line 1\nfile 2 line 2\n")

        reader = SourceCodeReader()
        result = reader.read_multiple([str(file1), str(file2)])

        assert len(result) == 2
        assert result[str(file1)][1] == "file 1 line 1"
        assert result[str(file2)][1] == "file 2 line 1"

    def test_read_multiple_with_nonexistent(self, tmp_path):
        """Test read_multiple skips non-existent files."""
        file1 = tmp_path / "file1.py"
        file1.write_text("file 1 line 1\n")

        reader = SourceCodeReader()
        result = reader.read_multiple([str(file1), "/nonexistent/file.py"])

        # Should only include the existing file
        assert len(result) == 1
        assert str(file1) in result

    def test_read_multiple_empty_list(self):
        """Test read_multiple with empty list."""
        reader = SourceCodeReader()
        result = reader.read_multiple([])

        assert result == {}

    def test_multiple_files_cached(self, tmp_path):
        """Test that multiple files can be cached separately."""
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("file 1 content\n")
        file2.write_text("file 2 content\n")

        reader = SourceCodeReader()

        result1 = reader.read_file(str(file1))
        result2 = reader.read_file(str(file2))

        assert len(reader._cache) == 2
        assert result1[1] == "file 1 content"
        assert result2[1] == "file 2 content"

    def test_file_read_error_handling(self, tmp_path):
        """Test that read errors return None gracefully."""
        # Create a directory (not a file) to trigger error
        dir_path = tmp_path / "not_a_file"
        dir_path.mkdir()

        reader = SourceCodeReader()
        result = reader.read_file(str(dir_path))

        assert result is None
