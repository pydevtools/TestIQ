"""
Convert pytest coverage.json to TestIQ format.

Pytest's coverage.json provides aggregated coverage across all tests.
This converter creates synthetic per-test coverage by analyzing pytest's
test output with the --cov flag.

Usage:
    python -m testiq.coverage_converter coverage.json -o testiq_coverage.json

Note: This provides aggregated coverage, not true per-test coverage.
For accurate per-test data, use the pytest plugin instead.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import click

from testiq.logging_config import get_logger

logger = get_logger(__name__)


def convert_pytest_coverage(coverage_data: Dict[str, Any]) -> Dict[str, Dict[str, List[int]]]:
    """
    Convert pytest coverage.json format to TestIQ format.

    Args:
        coverage_data: Pytest coverage.json data

    Returns:
        TestIQ format: {test_name: {filename: [line_numbers]}}

    Note: Since pytest coverage is aggregated, this creates a single
    synthetic "all_tests" entry with all covered lines.
    """
    if "files" not in coverage_data:
        raise ValueError("Invalid pytest coverage format: missing 'files' key")

    testiq_format: Dict[str, Dict[str, List[int]]] = {}
    all_coverage: Dict[str, List[int]] = {}

    # Extract coverage from pytest format
    for filepath, file_data in coverage_data["files"].items():
        if "executed_lines" not in file_data:
            continue

        executed_lines = file_data["executed_lines"]
        if not isinstance(executed_lines, list):
            logger.warning(f"Skipping {filepath}: executed_lines is not a list")
            continue

        # Make path relative if possible
        try:
            rel_path = str(Path(filepath).relative_to(Path.cwd()))
        except ValueError:
            rel_path = filepath

        all_coverage[rel_path] = sorted(executed_lines)

    # Create synthetic "all_tests" entry since pytest doesn't track per-test
    if all_coverage:
        testiq_format["all_tests_aggregated"] = all_coverage

    return testiq_format


def convert_pytest_contexts(coverage_data: Dict[str, Any]) -> Dict[str, Dict[str, List[int]]]:
    """
    Convert pytest coverage with contexts (if available).

    Pytest can track coverage per test if run with:
        pytest --cov --cov-context=test

    Args:
        coverage_data: Pytest coverage.json with contexts

    Returns:
        TestIQ format with per-test coverage (if contexts available)
    """
    # Check if contexts are available
    meta = coverage_data.get("meta", {})
    if not meta.get("show_contexts", False):
        logger.warning(
            "Coverage data doesn't include test contexts. "
            "Run with: pytest --cov --cov-context=test"
        )
        return convert_pytest_coverage(coverage_data)

    # Parse contexts if available
    testiq_format: Dict[str, Dict[str, List[int]]] = {}

    for filepath, file_data in coverage_data.get("files", {}).items():
        # Look for context-specific coverage
        if "contexts" in file_data:
            # Group by test context
            for context, lines in file_data["contexts"].items():
                if context and context != "":
                    # Make path relative
                    try:
                        rel_path = str(Path(filepath).relative_to(Path.cwd()))
                    except ValueError:
                        rel_path = filepath

                    if context not in testiq_format:
                        testiq_format[context] = {}

                    testiq_format[context][rel_path] = sorted(lines)

    if not testiq_format:
        # Fall back to aggregated format
        return convert_pytest_coverage(coverage_data)

    return testiq_format


@click.command()
@click.argument("coverage_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="testiq_coverage.json",
    help="Output file for TestIQ format",
)
@click.option(
    "--with-contexts",
    is_flag=True,
    help="Try to extract per-test coverage from pytest contexts",
)
def main(coverage_file: Path, output: Path, with_contexts: bool) -> None:
    """
    Convert pytest coverage.json to TestIQ format.

    COVERAGE_FILE: Path to pytest coverage.json file

    Examples:
        # Basic conversion (aggregated coverage)
        python -m testiq.coverage_converter coverage.json

        # With test contexts (if available)
        python -m testiq.coverage_converter coverage.json --with-contexts

    Note: For accurate per-test coverage, use the pytest plugin:
        pytest --testiq-output=testiq_coverage.json
    """
    try:
        # Load pytest coverage
        with open(coverage_file) as f:
            coverage_data = json.load(f)

        # Convert format
        if with_contexts:
            testiq_data = convert_pytest_contexts(coverage_data)
        else:
            testiq_data = convert_pytest_coverage(coverage_data)

        # Save TestIQ format
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w") as f:
            json.dump(testiq_data, f, indent=2)

        click.echo(f"✓ Converted {len(testiq_data)} test(s)")
        click.echo(f"✓ Saved to: {output}")

        if not with_contexts and len(testiq_data) == 1:
            click.echo()
            click.echo("⚠️  Note: This is aggregated coverage (all tests combined)")
            click.echo("   For per-test analysis:")
            click.echo("   1. Use: pytest --cov --cov-context=test")
            click.echo("   2. Or use: pytest --testiq-output=testiq_coverage.json")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
