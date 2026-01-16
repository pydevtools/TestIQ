"""
Pytest plugin for generating per-test coverage data compatible with TestIQ.

This plugin tracks which lines each test executes and generates a JSON file
in the format TestIQ expects: {test_name: {filename: [line_numbers]}}

Installation:
    pip install pytest-cov

Usage:
    pytest --testiq-output=testiq_coverage.json

Or in pytest.ini:
    [pytest]
    addopts = --testiq-output=testiq_coverage.json
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.nodes import Item


class TestIQPlugin:
    """Pytest plugin to collect per-test coverage data for TestIQ."""

    def __init__(self, output_file: str) -> None:
        """Initialize the plugin."""
        self.output_file = output_file
        self.test_coverage: Dict[str, Dict[str, List[int]]] = {}
        self.current_test: str = ""
        self.traced_lines: Set[tuple[str, int]] = set()
        self.file_cache: Dict[str, Dict[int, str]] = {}  # Cache file contents
        self.docstring_lines_cache: Dict[str, Set[int]] = {}  # Cache docstring lines

    def pytest_runtest_protocol(self, item: Item) -> None:
        """Called for each test item."""
        # Get full test name (module::class::test)
        self.current_test = item.nodeid
        self.traced_lines = set()

        # Set up trace function for this test
        sys.settrace(self._trace_lines)

    def _trace_lines(self, frame: Any, event: str, arg: Any) -> Any:
        """Trace function to record line execution."""
        if event == "line":
            filename = frame.f_code.co_filename
            lineno = frame.f_lineno

            # Filter to only project files (not libraries)
            if self._is_project_file(filename):
                # Skip if this line is part of a docstring
                if not self._is_docstring_line(filename, lineno):
                    self.traced_lines.add((filename, lineno))

        return self._trace_lines

    def _is_project_file(self, filename: str) -> bool:
        """Check if file is part of the project (not a library)."""
        # Exclude standard library and site-packages
        if "/site-packages/" in filename or "/lib/python" in filename:
            return False
        if filename.startswith("<"):  # <string>, <stdin>, etc.
            return False

        # Include files in current working directory
        try:
            Path(filename).relative_to(Path.cwd())
            return True
        except ValueError:
            return False

    def _get_docstring_delimiter(self, trimmed: str) -> Optional[str]:
        """Extract docstring delimiter from a line."""
        if '"""' in trimmed:
            return '"""'
        elif "'''" in trimmed:
            return "'''"
        return None

    def _is_single_line_docstring(self, trimmed: str, delimiter: str) -> bool:
        """Check if a line contains a complete single-line docstring."""
        first_idx = trimmed.find(delimiter)
        after_first = trimmed[first_idx + 3:]
        return delimiter in after_first

    def _process_docstring_line(
        self, 
        line_num: int, 
        trimmed: str, 
        in_docstring: bool, 
        docstring_delimiter: str,
        docstring_lines: set
    ) -> tuple[bool, str]:
        """Process a single line for docstring detection."""
        delimiter = self._get_docstring_delimiter(trimmed)
        if not delimiter:
            if in_docstring:
                docstring_lines.add(line_num)
            return in_docstring, docstring_delimiter
        
        if not in_docstring:
            # Starting a docstring
            docstring_lines.add(line_num)
            if self._is_single_line_docstring(trimmed, delimiter):
                return False, ''
            return True, delimiter
        elif delimiter == docstring_delimiter:
            # Ending a docstring
            docstring_lines.add(line_num)
            return False, ''
        
        # Inside a multi-line docstring with different delimiter
        docstring_lines.add(line_num)
        return in_docstring, docstring_delimiter

    def _find_docstring_lines(self, file_lines: Dict[int, str]) -> set:
        """Find all lines that are part of docstrings."""
        docstring_lines = set()
        in_docstring = False
        docstring_delimiter = ''

        for line_num in sorted(file_lines.keys()):
            line = file_lines[line_num]
            trimmed = line.strip()
            in_docstring, docstring_delimiter = self._process_docstring_line(
                line_num, trimmed, in_docstring, docstring_delimiter, docstring_lines
            )

        return docstring_lines

    def _is_docstring_line(self, filename: str, lineno: int) -> bool:
        """Check if a line is part of a docstring."""
        # Use cached result if available
        if filename in self.docstring_lines_cache:
            return lineno in self.docstring_lines_cache[filename]

        # Read and cache the file if not already cached
        if filename not in self.file_cache:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    self.file_cache[filename] = {i + 1: line for i, line in enumerate(lines)}
            except Exception:
                # If we can't read the file, assume no docstrings
                self.docstring_lines_cache[filename] = set()
                return False

        # Find all docstring lines in this file
        docstring_lines = self._find_docstring_lines(self.file_cache[filename])
        self.docstring_lines_cache[filename] = docstring_lines
        return lineno in docstring_lines

    def pytest_runtest_teardown(self, item: Item) -> None:
        """Called after each test finishes."""
        # Stop tracing
        sys.settrace(None)

        # Convert traced lines to TestIQ format
        if self.current_test and self.traced_lines:
            coverage: Dict[str, List[int]] = {}

            for filename, lineno in self.traced_lines:
                # Make path relative to project root
                try:
                    rel_path = str(Path(filename).relative_to(Path.cwd()))
                except ValueError:
                    rel_path = filename

                if rel_path not in coverage:
                    coverage[rel_path] = []
                coverage[rel_path].append(lineno)

            # Add function/class definition lines for better context
            self._add_definition_lines(coverage)

            # Sort line numbers and remove duplicates
            for file_path in coverage:
                coverage[file_path] = sorted(set(coverage[file_path]))

            self.test_coverage[self.current_test] = coverage

    def _get_file_content(self, file_path: str) -> Optional[Dict[int, str]]:
        """Get cached file content or read and cache it."""
        abs_path = str(Path.cwd() / file_path)
        if abs_path not in self.file_cache:
            try:
                with open(abs_path, 'r', encoding='utf-8') as f:
                    file_lines = f.readlines()
                    self.file_cache[abs_path] = {i + 1: line for i, line in enumerate(file_lines)}
            except Exception:
                return None
        return self.file_cache[abs_path]

    def _is_definition_line(self, line_text: str) -> bool:
        """Check if a line is a function or class definition."""
        stripped = line_text.strip()
        return stripped.startswith('def ') or stripped.startswith('class ')

    def _should_stop_search(self, line_text: str, check_line: int, line_num: int) -> bool:
        """Determine if we should stop searching backwards for definitions."""
        stripped = line_text.strip()
        if not stripped or stripped.startswith('#'):
            return False
        if stripped.startswith('@'):  # Decorator, continue searching
            return False
        # Don't search too far back
        return check_line < line_num - 50

    def _find_definition_for_line(self, line_num: int, file_content: Dict[int, str]) -> Optional[int]:
        """Find the nearest definition line for a given executed line."""
        for check_line in range(line_num - 1, 0, -1):
            if check_line not in file_content:
                break
            
            line_text = file_content[check_line]
            
            if self._is_definition_line(line_text):
                return check_line
            
            if self._should_stop_search(line_text, check_line, line_num):
                break
        
        return None

    def _add_definition_lines(self, coverage: Dict[str, List[int]]) -> None:
        """
        Add function/class definition lines to coverage.
        
        If a function body is executed, include the def line.
        If a class method is executed, include the class line.
        """
        for file_path, lines in coverage.items():
            if not lines:
                continue
            
            file_content = self._get_file_content(file_path)
            if not file_content:
                continue
            
            definition_lines = set()
            for line_num in lines:
                def_line = self._find_definition_for_line(line_num, file_content)
                if def_line:
                    definition_lines.add(def_line)
            
            coverage[file_path].extend(definition_lines)

    def pytest_sessionfinish(self, session: Any) -> None:
        """Called after all tests complete."""
        if self.test_coverage:
            output_path = Path(self.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w") as f:
                json.dump(self.test_coverage, f, indent=2)

            print(f"\n✓ TestIQ coverage data saved to: {output_path}")
            print(f"  {len(self.test_coverage)} tests tracked")


def pytest_addoption(parser: Parser) -> None:
    """Add command-line options for TestIQ plugin."""
    group = parser.getgroup("testiq")
    group.addoption(
        "--testiq-output",
        action="store",
        default=None,
        help="Output file for TestIQ per-test coverage data (JSON format)",
    )


def pytest_configure(config: Config) -> None:
    """Register the TestIQ plugin if --testiq-output is specified."""
    output_file = config.getoption("--testiq-output")
    if output_file:
        plugin = TestIQPlugin(output_file)
        config.pluginmanager.register(plugin, "testiq_plugin")
        config.addinivalue_line("markers", "testiq: mark test for TestIQ analysis")
