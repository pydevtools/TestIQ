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

            # Sort line numbers
            for lines in coverage.values():
                lines.sort()

            self.test_coverage[self.current_test] = coverage

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
