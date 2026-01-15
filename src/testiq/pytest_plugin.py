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
from typing import Any, Dict, List, Set

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
        docstring_lines = set()
        file_lines = self.file_cache[filename]
        in_docstring = False
        docstring_delimiter = ''

        for line_num in sorted(file_lines.keys()):
            line = file_lines[line_num]
            trimmed = line.strip()

            # Check for docstring delimiters
            if '"""' in trimmed or "'''" in trimmed:
                if '"""' in trimmed:
                    delimiter = '"""'
                else:
                    delimiter = "'''"

                if not in_docstring:
                    # Starting a docstring
                    in_docstring = True
                    docstring_delimiter = delimiter
                    docstring_lines.add(line_num)
                    
                    # Check if it's a single-line docstring
                    first_idx = trimmed.find(delimiter)
                    after_first = trimmed[first_idx + 3:]
                    if delimiter in after_first:
                        # Single-line docstring
                        in_docstring = False
                        docstring_delimiter = ''
                elif in_docstring and delimiter == docstring_delimiter:
                    # Ending a docstring
                    docstring_lines.add(line_num)
                    in_docstring = False
                    docstring_delimiter = ''
            elif in_docstring:
                # Inside a docstring
                docstring_lines.add(line_num)

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

    def _add_definition_lines(self, coverage: Dict[str, List[int]]) -> None:
        """
        Add function/class definition lines to coverage.
        
        If a function body is executed, include the def line.
        If a class method is executed, include the class line.
        """
        for file_path, lines in coverage.items():
            if not lines:
                continue
            
            # Get file contents
            try:
                abs_path = str(Path.cwd() / file_path)
                if abs_path not in self.file_cache:
                    with open(abs_path, 'r', encoding='utf-8') as f:
                        file_lines = f.readlines()
                        self.file_cache[abs_path] = {i + 1: line for i, line in enumerate(file_lines)}
                
                file_content = self.file_cache[abs_path]
            except Exception:
                continue
            
            # Find definition lines to add
            definition_lines = set()
            
            for line_num in lines:
                # Look backwards from this line to find the nearest def/class
                for check_line in range(line_num - 1, 0, -1):
                    if check_line not in file_content:
                        break
                    
                    line_text = file_content[check_line].strip()
                    
                    # Found a function or class definition
                    if line_text.startswith('def ') or line_text.startswith('class '):
                        # Check indentation - make sure we're in the same scope
                        if check_line < line_num:
                            # Add this definition line
                            definition_lines.add(check_line)
                            # Only add the immediate parent definition
                            break
                    
                    # Stop if we hit another statement at the same or lower indentation
                    if line_text and not line_text.startswith('#'):
                        # Check if this is a decorator
                        if line_text.startswith('@'):
                            continue
                        # If we hit something else, stop looking
                        if check_line < line_num - 50:  # Don't search too far
                            break
            
            # Add the definition lines to coverage
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
