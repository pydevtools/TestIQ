<!-- ⚠️ MARKED FOR DELETION - See docs/DELETE_THESE_FILES.md -->
<!-- Reason: Covered by examples/python/manual_test.py -->

# TestIQ Manual Testing Guide

This guide shows you how to manually test all TestIQ features.

## Quick Start

### 1. Run Built-in Demo
```bash
testiq demo
```
This immediately shows TestIQ in action with sample data.

---

## Sample Data Available

The project includes `sample_coverage.json` with 12 tests designed to showcase:
- ✅ Exact duplicates
- ✅ Subset duplicates  
- ✅ Similar tests
- ✅ Various edge cases

---

## CLI Testing

### Basic Analysis
```bash
# Terminal output (rich formatting)
testiq analyze sample_coverage.json

# With custom threshold
testiq analyze sample_coverage.json --threshold 0.9
testiq analyze sample_coverage.json --threshold 0.5
```

### Output Formats

#### HTML Report (Beautiful, Interactive)
```bash
testiq analyze sample_coverage.json --format html --output report.html

# Open in browser (macOS)
open report.html

# Or manually: File → Open → report.html
```

#### CSV Export (Spreadsheet Analysis)
```bash
testiq analyze sample_coverage.json --format csv --output results.csv

# Open in Excel/Numbers
open results.csv
```

#### JSON (Programmatic)
```bash
testiq analyze sample_coverage.json --format json --output results.json

# Pretty print
cat results.json | python -m json.tool

# Query with jq
cat results.json | jq '.exact_duplicates'
```

#### Markdown (Documentation)
```bash
testiq analyze sample_coverage.json --format markdown --output report.md

# View in terminal
cat report.md

# Or open in VSCode/editor
code report.md
```

### Quality Scoring
```bash
# View quality score in terminal
testiq quality-score sample_coverage.json

# Save detailed report
testiq quality-score sample_coverage.json --output quality.json
testiq quality-score sample_coverage.json --threshold 0.9

# View the report
cat quality.json | python -m json.tool
```

### CI/CD Features

#### Quality Gates
```bash
# Pass if ≤5 duplicates
testiq analyze sample_coverage.json --quality-gate --max-duplicates 5
echo "Exit code: $?"  # 0 = pass, 2 = fail

# Fail if >1 duplicate (should fail with sample data)
testiq analyze sample_coverage.json --quality-gate --max-duplicates 1
echo "Exit code: $?"  # Should be 2

# Multiple thresholds
testiq analyze sample_coverage.json \
  --quality-gate \
  --max-duplicates 10 \
  --threshold 0.9
```

#### Baseline Management
```bash
# Save current state as baseline
testiq analyze sample_coverage.json --save-baseline my-baseline

# List all baselines
testiq baseline list

# View baseline details
testiq baseline show my-baseline

# Compare against baseline (fails if quality decreased)
testiq analyze sample_coverage.json --quality-gate --baseline my-baseline

# Delete baseline
testiq baseline delete old-baseline
testiq baseline delete old-baseline --force  # No confirmation
```

### Configuration
```bash
# Use custom config file
testiq analyze sample_coverage.json --config .testiq.yaml

# Set log level
testiq analyze sample_coverage.json --log-level DEBUG
testiq analyze sample_coverage.json --log-level ERROR

# Log to file
testiq analyze sample_coverage.json --log-file testiq.log
tail -f testiq.log  # Watch logs
```

### Help Commands
```bash
testiq --help
testiq analyze --help
testiq quality-score --help
testiq baseline --help
```

---

## Python API Testing

### Interactive Python Session
```bash
python -i manual_test.py
```

Or start Python REPL:
```python
python
>>> from testiq.analyzer import CoverageDuplicateFinder
>>> import json

# Load data
>>> with open('sample_coverage.json') as f:
...     data = json.load(f)

# Analyze
>>> finder = CoverageDuplicateFinder()
>>> for test, cov in data.items():
...     finder.add_test_coverage(test, cov)

# Find issues
>>> exact = finder.find_exact_duplicates()
>>> print(f"Found {len(exact)} duplicate groups")
Found 1 duplicate groups

>>> subsets = finder.find_subset_duplicates()
>>> print(f"Found {len(subsets)} subset duplicates")
Found 10 subset duplicates

# Get report
>>> print(finder.generate_report())
```

### Run Complete Test Script
```bash
python manual_test.py
```

This tests:
1. ✅ Basic duplicate finding
2. ✅ Loading from file
3. ✅ Quality analysis
4. ✅ Recommendations
5. ✅ Report generation (HTML, CSV, Markdown)
6. ✅ Quality gates
7. ✅ Plugin system
8. ✅ Configuration
9. ✅ Security validation

---

## Feature-Specific Testing

### Test Exact Duplicate Detection
```python
from testiq.analyzer import CoverageDuplicateFinder

finder = CoverageDuplicateFinder()

# Add identical tests
finder.add_test_coverage("test_a", {"file.py": [1, 2, 3]})
finder.add_test_coverage("test_b", {"file.py": [1, 2, 3]})
finder.add_test_coverage("test_c", {"file.py": [1, 2, 3]})

duplicates = finder.find_exact_duplicates()
assert len(duplicates) == 1  # One group of 3 tests
assert len(duplicates[0]) == 3  # All 3 are identical
```

### Test Subset Detection
```python
# Add subset relationships
finder.add_test_coverage("small", {"file.py": [1, 2]})
finder.add_test_coverage("large", {"file.py": [1, 2, 3, 4, 5]})

subsets = finder.find_subset_duplicates()
# Should find: small is subset of large
```

### Test Similarity
```python
# Add similar tests
finder.add_test_coverage("test_1", {"file.py": [1, 2, 3, 4, 5]})
finder.add_test_coverage("test_2", {"file.py": [1, 2, 3, 4, 9]})

similar = finder.find_similar_coverage(threshold=0.7)
# Should find these two as similar (80% overlap)
```

### Test Quality Scoring
```python
from testiq.analysis import QualityAnalyzer

analyzer = QualityAnalyzer(finder)
score = analyzer.calculate_score(threshold=0.8)

print(f"Score: {score.overall_score}/100")
print(f"Grade: {score.grade}")
print("Recommendations:")
for rec in score.recommendations:
    print(f"  - {rec}")
```

### Test Report Generation
```python
from testiq.reporting import HTMLReportGenerator, CSVReportGenerator

# HTML
html_gen = HTMLReportGenerator(finder)
html_gen.generate(Path("my_report.html"), threshold=0.8)

# CSV
csv_gen = CSVReportGenerator(finder)
csv_gen.generate_summary(Path("my_report.csv"), threshold=0.8)
```

### Test Plugin System
```python
from testiq.plugins import register_hook, trigger_hook, HookType, HookContext

# Define custom hook
def my_duplicate_handler(ctx: HookContext):
    print(f"Duplicate found: {ctx.data}")

# Register
register_hook(HookType.ON_DUPLICATE_FOUND, my_duplicate_handler)

# Trigger manually
trigger_hook(HookType.ON_DUPLICATE_FOUND, data={"test1": "a", "test2": "b"})
```

### Test CI/CD Integration
```python
from testiq.cicd import QualityGate, QualityGateChecker

gate = QualityGate(
    max_duplicates=5,
    max_duplicate_percentage=10.0,
    fail_on_increase=True
)

checker = QualityGateChecker(gate)
passed, details = checker.check(finder, threshold=0.8)

if not passed:
    print("Quality gate failed!")
    for failure in details['failures']:
        print(f"  - {failure}")
    exit(2)  # Exit with error code
```

---

## Testing Different Scenarios

### Scenario 1: Perfect Test Suite (No Duplicates)
```python
finder = CoverageDuplicateFinder()
finder.add_test_coverage("test_1", {"file.py": [1, 2]})
finder.add_test_coverage("test_2", {"file.py": [3, 4]})
finder.add_test_coverage("test_3", {"file.py": [5, 6]})

assert len(finder.find_exact_duplicates()) == 0
```

### Scenario 2: High Duplication
```python
finder = CoverageDuplicateFinder()
for i in range(10):
    finder.add_test_coverage(f"test_{i}", {"file.py": [1, 2, 3]})

duplicates = finder.find_exact_duplicates()
assert len(duplicates[0]) == 10  # All duplicates
```

### Scenario 3: Large Test Suite
```python
finder = CoverageDuplicateFinder(enable_parallel=True, max_workers=8)

# Add 1000 tests
for i in range(1000):
    finder.add_test_coverage(
        f"test_{i}", 
        {f"file_{i % 10}.py": list(range(i, i+10))}
    )

# Should complete quickly with parallel processing
duplicates = finder.find_exact_duplicates()
```

---

## Viewing Generated Reports

### HTML Report
```bash
# macOS
open sample_report.html

# Linux
xdg-open sample_report.html

# Windows
start sample_report.html

# Or drag & drop to browser
```

### CSV Report
```bash
# Open in Excel/Numbers/Google Sheets
open test_report.csv

# View in terminal
column -t -s, test_report.csv | less
```

### Markdown Report
```bash
# Terminal with formatting
glow test_report.md

# Or plain view
cat test_report.md

# VSCode
code test_report.md
```

---

## Troubleshooting

### Issue: Import errors
```bash
# Reinstall in development mode
pip install -e .
```

### Issue: Permission errors
```bash
# Check file permissions
ls -la sample_coverage.json

# Fix if needed
chmod 644 sample_coverage.json
```

### Issue: Large files taking too long
```python
# Enable parallel processing
finder = CoverageDuplicateFinder(
    enable_parallel=True,
    max_workers=8,  # Use more workers
    enable_caching=True  # Enable caching
)
```

### Debug Mode
```bash
# Enable detailed logging
testiq analyze sample_coverage.json --log-level DEBUG --log-file debug.log

# View logs
tail -f debug.log
```

---

## Performance Testing

### Benchmark Analysis Speed
```python
import time

finder = CoverageDuplicateFinder(enable_parallel=True)

# Load data
with open('sample_coverage.json') as f:
    data = json.load(f)
for test, cov in data.items():
    finder.add_test_coverage(test, cov)

# Time exact duplicates
start = time.time()
finder.find_exact_duplicates()
print(f"Exact duplicates: {time.time() - start:.3f}s")

# Time subset detection
start = time.time()
finder.find_subset_duplicates()
print(f"Subset duplicates: {time.time() - start:.3f}s")

# Time similarity
start = time.time()
finder.find_similar_coverage(0.8)
print(f"Similarity analysis: {time.time() - start:.3f}s")
```

---

## Next Steps

1. ✅ Run `testiq demo` to see it in action
2. ✅ Analyze sample data: `testiq analyze sample_coverage.json`
3. ✅ Open HTML report in browser
4. ✅ Try with your own coverage data
5. ✅ Integrate into CI/CD pipeline
6. ✅ Customize configuration file

---

## Real-World Usage

### With pytest-cov
```bash
# Generate coverage
pytest --cov --cov-report=json

# Analyze
testiq analyze coverage.json --format html --output report.html
```

### In GitHub Actions
```yaml
- name: Analyze test quality
  run: |
    testiq analyze coverage.json \
      --quality-gate \
      --max-duplicates 10 \
      --save-baseline ci-baseline
```

### Pre-commit Hook
```bash
# .git/hooks/pre-commit
#!/bin/bash
pytest --cov --cov-report=json
testiq analyze coverage.json --quality-gate --max-duplicates 5
```

---

**Happy Testing! 🎉**

For more information, see [docs/guide.md](docs/guide.md)
