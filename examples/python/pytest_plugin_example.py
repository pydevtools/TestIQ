#!/usr/bin/env python3
"""
Example: Using TestIQ pytest plugin to track per-test coverage.

This script demonstrates:
1. Running pytest with TestIQ plugin to generate per-test coverage
2. Analyzing the coverage data with TestIQ
3. Generating reports

Requirements:
    pip install testiq
    
Note: pytest is now included as a dependency of testiq, so no need
to install it separately!

Usage:
    python examples/python/pytest_plugin_example.py
    
Key Features Demonstrated:
- Automatic per-test coverage tracking via pytest plugin
- Quality scoring with latest improvements
- HTML report generation with enhanced styling
- Cognitive complexity improvements in analysis engine
"""

import json
import subprocess
import sys
from pathlib import Path


def main():
    print("=" * 70)
    print("TestIQ Pytest Plugin Example")
    print("=" * 70)
    print()

    # Step 1: Run pytest with TestIQ plugin
    print("Step 1: Running pytest with TestIQ plugin...")
    print("-" * 70)

    output_file = "testiq_coverage.json"

    # Run pytest with TestIQ plugin
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            f"--testiq-output={output_file}",
            "-v",
        ],
        capture_output=True,
        text=True,
    )

    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr, file=sys.stderr)

    if not Path(output_file).exists():
        print(f"❌ Coverage file not generated: {output_file}")
        return 1

    # Step 2: Check the format
    print()
    print("Step 2: Examining coverage data format...")
    print("-" * 70)

    with open(output_file) as f:
        coverage_data = json.load(f)

    print(f"Number of tests tracked: {len(coverage_data)}")
    print()
    print("Sample test coverage:")
    for test_name in list(coverage_data.keys())[:2]:
        print(f"\nTest: {test_name}")
        for file, lines in list(coverage_data[test_name].items())[:2]:
            print(f"  {file}: {lines[:5]}{'...' if len(lines) > 5 else ''}")

    # Step 3: Analyze with TestIQ
    print()
    print("Step 3: Analyzing with TestIQ...")
    print("-" * 70)

    result = subprocess.run(
        [sys.executable, "-m", "testiq", "analyze", output_file], capture_output=True, text=True
    )

    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr, file=sys.stderr)

    # Step 4: Generate HTML report
    print()
    print("Step 4: Generating HTML report...")
    print("-" * 70)

    html_report = "reports/pytest_plugin_report.html"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "testiq",
            "analyze",
            output_file,
            "--format",
            "html",
            "--output",
            html_report,
        ],
        capture_output=True,
        text=True,
    )

    if Path(html_report).exists():
        print(f"✓ HTML report generated: {html_report}")
        print(f"  Open with: open {html_report}")
    else:
        print("❌ Failed to generate HTML report")
        print(result.stdout)

    print()
    print("=" * 70)
    print("✅ Example complete!")
    print("=" * 70)
    print()
    print("Summary:")
    print("  1. pytest --testiq-output=... generates per-test coverage")
    print("  2. TestIQ format: {test_name: {file: [lines]}}")
    print("  3. testiq analyze finds duplicates and generates reports")
    print()
    print("Next steps:")
    print("  • View HTML report for interactive analysis")
    print("  • Add --quality-gate to enforce quality standards")
    print("  • Integrate into CI/CD pipeline")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
