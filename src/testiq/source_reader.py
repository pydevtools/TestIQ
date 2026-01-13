"""
Source code reader for TestIQ reports.
Reads actual source files to display in coverage comparisons.
"""

from pathlib import Path
from typing import Optional


class SourceCodeReader:
    """Read and cache source code files for display in reports."""
    
    def __init__(self) -> None:
        """Initialize the source code reader."""
        self._cache: dict[str, dict[int, str]] = {}
    
    def read_file(self, filepath: str) -> Optional[dict[int, str]]:
        """
        Read a source file and return line-by-line content.
        
        Args:
            filepath: Path to the source file
            
        Returns:
            Dictionary mapping line numbers (1-indexed) to source code lines,
            or None if file cannot be read
        """
        if filepath in self._cache:
            return self._cache[filepath]
        
        try:
            file_path = Path(filepath)
            if file_path.exists() and file_path.is_file():
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    result = {
                        i + 1: line.rstrip() for i, line in enumerate(lines)
                    }
                    self._cache[filepath] = result
                    return result
        except Exception:
            pass
        
        return None
    
    def read_multiple(self, filepaths: list[str]) -> dict[str, dict[int, str]]:
        """
        Read multiple source files.
        
        Args:
            filepaths: List of file paths to read
            
        Returns:
            Dictionary mapping filepath to line content dictionary
        """
        result = {}
        for filepath in filepaths:
            content = self.read_file(filepath)
            if content:
                result[filepath] = content
        return result
