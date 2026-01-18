#!/usr/bin/env python3
"""
Example: Complete TestIQ Python API Usage

This example demonstrates all major features of TestIQ including:
- Duplicate detection (exact, subset, similarity)
- Quality scoring and recommendations
- Report generation (HTML, CSV, Markdown)
- CI/CD features (quality gates, baselines)
- Plugin system
- Configuration and security

Note: This example uses sample test data. In production, you would:
1. Run pytest with --testiq-output flag to generate real coverage data
2. Or use coverage.py with --cov-context=test
3. Then analyze the generated JSON file
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for running from examples/
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir / "src"))

# Ensure reports directory exists in project root
reports_dir = parent_dir / "reports"
reports_dir.mkdir(exist_ok=True)

# Constants for sample data (following TestIQ's best practices)
SAMPLE_AUTH_FILE = "auth.py"
SAMPLE_USER_FILE = "user.py"

# Test 1: Basic usage
print("=" * 60)
print("TEST 1: Basic CoverageDuplicateFinder")
print("=" * 60)

from testiq.analyzer import CoverageDuplicateFinder

finder = CoverageDuplicateFinder()

# Add some test data
finder.add_test_coverage("test_login_1", {
    SAMPLE_AUTH_FILE: [10, 11, 12, 15, 20],
    SAMPLE_USER_FILE: [5, 6, 7]
})

finder.add_test_coverage("test_login_2", {
    SAMPLE_AUTH_FILE: [10, 11, 12, 15, 20],
    SAMPLE_USER_FILE: [5, 6, 7]
})

finder.add_test_coverage("test_login_minimal", {
    SAMPLE_AUTH_FILE: [10, 11, 12]
})

# Find duplicates
exact = finder.find_exact_duplicates()
subsets = finder.find_subset_duplicates()
similar = finder.find_similar_coverage(0.7)

print(f"\n✓ Exact duplicates: {len(exact)} groups")
print(f"✓ Subset duplicates: {len(subsets)} tests")
print(f"✓ Similar tests: {len(similar)} pairs")

# Test 2: Load from file
print("\n" + "=" * 60)
print("TEST 2: Load from sample_coverage.json")
print("=" * 60)

finder2 = CoverageDuplicateFinder(enable_parallel=True, enable_caching=True)

# Load sample coverage data from examples directory
sample_file = Path(__file__).parent.parent / "sample_coverage.json"
with open(sample_file) as f:
    coverage_data = json.load(f)

for test_name, test_coverage in coverage_data.items():
    finder2.add_test_coverage(test_name, test_coverage)

exact2 = finder2.find_exact_duplicates()
subsets2 = finder2.find_subset_duplicates()
similar2 = finder2.find_similar_coverage(0.8)

print(f"\n✓ Total tests: {len(finder2.tests)}")
print(f"✓ Exact duplicates: {len(exact2)} groups")
print(f"✓ Subset duplicates: {len(subsets2)} tests")
print(f"✓ Similar tests (≥80%): {len(similar2)} pairs")

# Test 3: Quality Analysis
print("\n" + "=" * 60)
print("TEST 3: Quality Score & Recommendations")
print("=" * 60)

from testiq.analysis import QualityAnalyzer, RecommendationEngine

analyzer = QualityAnalyzer(finder2)
score = analyzer.calculate_score(threshold=0.8)

print(f"\n✓ Overall Score: {score.overall_score:.1f}/100")
print(f"✓ Grade: {score.grade}")
print(f"✓ Duplication Score: {score.duplication_score:.1f}/100")
print(f"✓ Efficiency Score: {score.coverage_efficiency_score:.1f}/100")
print(f"✓ Uniqueness Score: {score.uniqueness_score:.1f}/100")

print("\n📋 Recommendations:")
for rec in score.recommendations[:3]:
    print(f"  • {rec}")

# Test 4: Recommendations Engine
print("\n" + "=" * 60)
print("TEST 4: Detailed Recommendations")
print("=" * 60)

engine = RecommendationEngine(finder2)
report = engine.generate_report(threshold=0.8)

print(f"\n✓ High Priority Actions: {len([r for r in report['action_items'] if r['priority'] == 'high'])}")
print(f"✓ Medium Priority Actions: {len([r for r in report['action_items'] if r['priority'] == 'medium'])}")
print(f"✓ Low Priority Actions: {len([r for r in report['action_items'] if r['priority'] == 'low'])}")

# Test 5: Generate Reports
print("\n" + "=" * 60)
print("TEST 5: Generate Reports")
print("=" * 60)

from testiq.reporting import CSVReportGenerator, HTMLReportGenerator

# HTML Report
html_gen = HTMLReportGenerator(finder2)
html_report_path = reports_dir / "test_report.html"
html_gen.generate(html_report_path, threshold=0.8)
print(f"✓ HTML report generated: {html_report_path}")

# CSV Report
csv_gen = CSVReportGenerator(finder2)
csv_report_path = reports_dir / "test_report.csv"
csv_gen.generate_summary(csv_report_path, threshold=0.8)
print(f"✓ CSV report generated: {csv_report_path}")

# Markdown Report
markdown_report = finder2.generate_report()
md_report_path = reports_dir / "test_report.md"
md_report_path.write_text(markdown_report)
print(f"✓ Markdown report generated: {md_report_path}")

# Test 6: CI/CD Features
print("\n" + "=" * 60)
print("TEST 6: Quality Gates & Baselines")
print("=" * 60)

from testiq.cicd import QualityGate, QualityGateChecker

# Quality Gate
gate = QualityGate(
    max_duplicates=5,
    max_duplicate_percentage=10.0,
    fail_on_increase=True
)

checker = QualityGateChecker(gate)
passed, details = checker.check(finder2, threshold=0.8)

print(f"\n✓ Quality Gate: {'PASSED ✓' if passed else 'FAILED ✗'}")
print(f"✓ Duplicate count: {details['current']['exact_duplicates']}")
print(f"✓ Duplicate %: {details['current']['duplicate_percentage']:.2f}%")

if not passed:
    print("\n⚠️  Failures:")
    for failure in details['failures']:
        print(f"  • {failure}")

# Test 7: Plugin System
print("\n" + "=" * 60)
print("TEST 7: Plugin System & Hooks")
print("=" * 60)

from testiq.plugins import HookContext, HookType, clear_hooks, register_hook, trigger_hook


# Register a custom hook
def my_hook(ctx: HookContext):
    print(f"  🔔 Hook triggered: {ctx.hook_type.value}")
    print(f"     Data keys: {list(ctx.data.keys())}")

register_hook(HookType.ON_DUPLICATE_FOUND, my_hook)

# Trigger it
trigger_hook(HookType.ON_DUPLICATE_FOUND, data={"test1": "test_a", "test2": "test_b"})

clear_hooks()
print("\n✓ Plugin system working")

# Test 8: Configuration
print("\n" + "=" * 60)
print("TEST 8: Configuration System")
print("=" * 60)

from testiq.config import Config

config = Config()
print(f"\n✓ Default log level: {config.log.level}")
print(f"✓ Max file size: {config.security.max_file_size / 1024 / 1024:.0f}MB")
print(f"✓ Parallel processing: {config.performance.enable_parallel}")
print(f"✓ Max workers: {config.performance.max_workers}")
print(f"✓ Similarity threshold: {config.analysis.similarity_threshold}")

# Test 9: Security Features
print("\n" + "=" * 60)
print("TEST 9: Security Validation")
print("=" * 60)

from testiq.security import check_file_size, validate_coverage_data, validate_file_path

try:
    # Valid file
    path = validate_file_path(sample_file)
    print(f"✓ File validation passed: {path.name}")

    # Check size
    check_file_size(path)
    print("✓ File size check passed")

    # Validate coverage data
    validate_coverage_data(coverage_data)
    print("✓ Coverage data validation passed")

except Exception as e:
    print(f"✗ Validation error: {e}")

# Final Summary
print("=" * 60)
print("ALL TESTS COMPLETED SUCCESSFULLY! ✅")
print("=" * 60)
print("\nGenerated files in reports/:")
print("  • test_report.html - Open in browser to view")
print("  • test_report.csv - Open in Excel/spreadsheet")
print("  • test_report.md - View in text editor")
print("\nNext steps:")
print("  • Open reports/test_report.html in your browser")
print("  • Try: testiq analyze sample_coverage.json")
print("  • Run: testiq demo")
