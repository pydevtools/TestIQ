# TestIQ User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Core Concepts](#core-concepts)
5. [CLI Usage](#cli-usage)
6. [Python API](#python-api)
7. [CI/CD Integration](#cicd-integration)
8. [Advanced Features](#advanced-features)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Introduction

TestIQ is an enterprise-grade tool for analyzing test coverage to identify duplicate, redundant, and inefficient tests. By removing unnecessary tests, you can:

- **Reduce CI/CD time** by 10-30%
- **Lower infrastructure costs** 
- **Improve maintainability**
- **Focus on valuable tests**

### How It Works

TestIQ analyzes per-test coverage data to find:

1. **Exact Duplicates** - Tests with identical coverage (safe to remove)
2. **Subset Duplicates** - Tests completely covered by other tests
3. **Similar Tests** - Tests with high overlap (configurable threshold)

---

## Installation

### Requirements

- Python 3.9 or higher
- pip or uv package manager

### Install from PyPI

```bash
pip install testiq
```

### Install from Source

```bash
git clone https://github.com/yourusername/testiq.git
cd testiq
pip install -e ".[dev]"
```

### Verify Installation

```bash
testiq --version
```

---

## Quick Start

### 1. Generate Coverage Data

First, collect per-test coverage data. The format is:

```json
{
  "test_name_1": {
    "file.py": [1, 2, 3, 5, 10],
    "other.py": [20, 21, 22]
  },
  "test_name_2": {
    "file.py": [1, 2, 3, 5, 10],
    "other.py": [20, 21, 22]
  }
}
```

See integration guides for pytest, unittest, etc.

### 2. Run Analysis

```bash
testiq analyze coverage.json
```

### 3. Review Results

TestIQ will display:
- Exact duplicate groups
- Subset relationships
- Similar test pairs
- Recommendations

---

## Core Concepts

### Duplicate Types

#### Exact Duplicates

Tests with **identical coverage**. 100% confidence to remove.

```python
test_a: covers [file.py: 1,2,3]
test_b: covers [file.py: 1,2,3]
# Exactly the same - remove one
```

#### Subset Duplicates

One test's coverage is **completely contained** in another.

```python
test_small: covers [file.py: 1,2,3]
test_large: covers [file.py: 1,2,3,4,5,6]
# test_small is subset of test_large - consider removing test_small
```

#### Similar Tests

Tests with **high overlap** (Jaccard similarity).

```python
test_a: covers [file.py: 1,2,3,4,5]
test_b: covers [file.py: 3,4,5,6,7]
# Similarity = |{3,4,5}| / |{1,2,3,4,5,6,7}| = 3/7 ≈ 0.43
```

### Similarity Threshold

Configure how similar tests need to be to be flagged:

- **0.8** (default) - 80% overlap
- **0.9** - 90% overlap (stricter)
- **0.7** - 70% overlap (more lenient)

---

## CLI Usage

### Basic Analysis

```bash
# Analyze with defaults
testiq analyze coverage.json

# Custom threshold
testiq analyze coverage.json --threshold 0.85

# Save to file
testiq analyze coverage.json --output report.md
```

### Output Formats

```bash
# Plain text (default)
testiq analyze coverage.json

# Markdown
testiq analyze coverage.json --format markdown

# JSON (for automation)
testiq analyze coverage.json --format json

# HTML (beautiful reports)
testiq analyze coverage.json --format html --output report.html

# CSV (spreadsheets)
testiq analyze coverage.json --format csv --output duplicates.csv
```

### Quality Scoring

```bash
# Get quality score
testiq quality-score coverage.json

# Save detailed report
testiq quality-score coverage.json --output quality.json
```

### Baseline Management

```bash
# Save current state as baseline
testiq analyze coverage.json --save-baseline prod-v1.0

# Compare against baseline
testiq analyze coverage.json --baseline prod-v1.0

# List all baselines
testiq baseline list

# Show baseline details
testiq baseline show prod-v1.0

# Delete old baseline
testiq baseline delete old-baseline --force
```

### Quality Gates

```bash
# Fail if too many duplicates
testiq analyze coverage.json \
  --quality-gate \
  --max-duplicates 10 \
  --max-duplicate-percentage 5.0

# Fail if duplicates increase from baseline
testiq analyze coverage.json \
  --quality-gate \
  --baseline prod-v1.0
```

---

## Python API

### Basic Usage

```python
from testiq.analyzer import CoverageDuplicateFinder

# Create analyzer
finder = CoverageDuplicateFinder()

# Add test coverage
finder.add_test_coverage("test_login", {
    "auth.py": [10, 11, 12],
    "user.py": [5, 6, 7]
})

finder.add_test_coverage("test_authenticate", {
    "auth.py": [10, 11, 12],
    "user.py": [5, 6, 7]
})

# Find duplicates
exact = finder.find_exact_duplicates()
print(f"Exact duplicates: {exact}")
# [["test_login", "test_authenticate"]]

# Find subsets
subsets = finder.find_subset_duplicates()

# Find similar
similar = finder.find_similar_coverage(threshold=0.8)

# Generate report
report = finder.generate_report()
print(report)
```

### Performance Options

```python
# Enable parallel processing for large test suites
finder = CoverageDuplicateFinder(
    enable_parallel=True,
    max_workers=4,
    enable_caching=True
)
```

### Quality Analysis

```python
from testiq.analysis import QualityAnalyzer, RecommendationEngine

# Calculate quality score
analyzer = QualityAnalyzer(finder)
score = analyzer.calculate_score(threshold=0.9)

print(f"Overall Score: {score.overall_score}/100")
print(f"Grade: {score.grade}")
print(f"Duplicates: {score.duplicate_percentage}%")

# Get recommendations
engine = RecommendationEngine(finder)
report = engine.generate_report()

for rec in report["recommendations"]:
    priority = rec["priority"]
    message = rec["message"]
    print(f"[{priority}] {message}")
```

### HTML Reports

```python
from testiq.reporting import HTMLReportGenerator

generator = HTMLReportGenerator(finder)

# Generate HTML string
html = generator.generate(threshold=0.85)

# Or save to file
generator.save("report.html", threshold=0.85)
```

### CSV Export

```python
from testiq.reporting import CSVReportGenerator

generator = CSVReportGenerator(finder)

# Export all results
generator.to_csv("all_results.csv", threshold=0.85)

# Export specific types
generator.exact_duplicates_to_csv("exact.csv")
generator.subset_duplicates_to_csv("subsets.csv")
generator.similar_coverage_to_csv("similar.csv", threshold=0.85)
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Test Quality

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install TestIQ
        run: pip install testiq
      
      - name: Run tests with coverage
        run: pytest --cov --cov-report=json
      
      - name: Analyze test quality
        run: |
          testiq analyze coverage.json \
            --quality-gate \
            --max-duplicates 10 \
            --save-baseline ci
      
      - name: Generate HTML report
        run: testiq analyze coverage.json --format html --output report.html
      
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: testiq-report
          path: report.html
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    
    stages {
        stage('Test') {
            steps {
                sh 'pytest --cov --cov-report=json'
            }
        }
        
        stage('Quality Check') {
            steps {
                sh '''
                    pip install testiq
                    testiq analyze coverage.json \
                        --quality-gate \
                        --max-duplicates 10 \
                        --baseline main
                '''
            }
        }
        
        stage('Report') {
            steps {
                sh 'testiq analyze coverage.json --format html --output report.html'
                publishHTML([
                    reportDir: '.',
                    reportFiles: 'report.html',
                    reportName: 'TestIQ Report'
                ])
            }
        }
    }
}
```

### Quality Gate Example

```python
from testiq.cicd import QualityGate, QualityGateChecker
import sys

# Define thresholds
gate = QualityGate(
    max_duplicates=10,
    max_duplicate_percentage=5.0,
    fail_on_increase=True
)

# Check quality
checker = QualityGateChecker(gate)
passed, details = checker.check(finder, threshold=0.9)

if not passed:
    print("❌ Quality gate FAILED:")
    for failure in details["failures"]:
        print(f"   {failure}")
    sys.exit(2)  # Exit code 2 = quality failure
else:
    print("✅ Quality gate PASSED")
    sys.exit(0)
```

---

## Advanced Features

### Plugin System

Extend TestIQ with custom hooks:

```python
from testiq.plugins import register_hook, HookType, HookContext

def on_duplicate_found(ctx: HookContext):
    test1 = ctx.data["test1"]
    test2 = ctx.data["test2"]
    
    # Send to Slack, log to database, etc.
    print(f"Duplicate found: {test1} ↔ {test2}")

register_hook(HookType.ON_DUPLICATE_FOUND, on_duplicate_found)
```

Available hooks:
- `BEFORE_ANALYSIS`
- `AFTER_ANALYSIS`
- `ON_DUPLICATE_FOUND`
- `ON_SUBSET_FOUND`
- `ON_SIMILAR_FOUND`
- `ON_ERROR`
- `ON_QUALITY_GATE_FAIL`

### Trend Tracking

Track quality over time:

```python
from testiq.cicd import TrendTracker
from pathlib import Path

tracker = TrendTracker(Path(".testiq/history.json"))

# Add result
tracker.add_result({
    "timestamp": "2024-01-15T10:30:00",
    "exact_duplicates": 5,
    "subset_duplicates": 3,
    "total_tests": 100
})

# Check if improving
if tracker.is_improving("exact_duplicates"):
    print("✅ Test quality is improving!")

# Get trend
trend = tracker.get_trend("exact_duplicates")
# Returns: "improving" | "worsening" | "stable"
```

### Configuration Files

Create `testiq.yaml`:

```yaml
analysis:
  similarity_threshold: 0.8

performance:
  enable_parallel: true
  max_workers: 4
  enable_caching: true

security:
  max_file_size: 104857600  # 100MB
  max_tests: 100000

log:
  level: "INFO"
  enable_rotation: true
  max_bytes: 10485760
  backup_count: 5
```

---

## Best Practices

### 1. Start with High Threshold

```bash
# Start strict to find obvious duplicates
testiq analyze coverage.json --threshold 0.95

# Gradually lower threshold
testiq analyze coverage.json --threshold 0.85
testiq analyze coverage.json --threshold 0.75
```

### 2. Use Quality Gates in CI

Always use quality gates to prevent regression:

```bash
testiq analyze coverage.json \
  --quality-gate \
  --max-duplicates 10 \
  --baseline main
```

### 3. Track Trends

Monitor quality over time:

```python
# Add to your CI pipeline
tracker.add_result(current_analysis)

if tracker.is_improving("exact_duplicates"):
    print("✅ Quality trending up")
else:
    print("⚠️ Quality needs attention")
```

### 4. Review Before Removing

- **Exact duplicates**: Safe to remove
- **Subset duplicates**: Review test intent first
- **Similar tests**: May test different edge cases

### 5. Generate Reports

Use HTML reports for stakeholders:

```bash
testiq analyze coverage.json \
  --format html \
  --output reports/test-quality.html
```

---

## Troubleshooting

### Coverage File Not Found

**Error:** `FileNotFoundError: coverage.json not found`

**Solution:** Ensure you generate coverage data first:

```bash
pytest --cov --cov-report=json
```

### Invalid Coverage Format

**Error:** `InvalidCoverageDataError: Invalid format`

**Solution:** Verify JSON structure:

```json
{
  "test_name": {
    "file.py": [1, 2, 3]
  }
}
```

### No Duplicates Found

If TestIQ finds no duplicates but you expect some:

1. Lower similarity threshold: `--threshold 0.7`
2. Check coverage data quality
3. Ensure coverage is per-test (not aggregate)

### Performance Issues

For large test suites (>1000 tests):

```python
finder = CoverageDuplicateFinder(
    enable_parallel=True,
    max_workers=8,  # Increase workers
    enable_caching=True
)
```

### Memory Issues

Reduce memory usage:

1. Process in batches
2. Disable caching: `enable_caching=False`
3. Reduce worker count

---

## Getting Help

- **Documentation**: [docs/](.)
- **GitHub Issues**: [github.com/yourusername/testiq/issues](https://github.com/yourusername/testiq/issues)
- **Discussions**: [github.com/yourusername/testiq/discussions](https://github.com/yourusername/testiq/discussions)

---

## Next Steps

1. Read the [API Documentation](api.md)
2. Check out [Examples](../examples/)
3. Join the community discussions
