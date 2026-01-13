# TestIQ - Intelligent Test Analysis

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Test Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen.svg)](htmlcov/index.html)
[![Tests](https://img.shields.io/badge/tests-224%2F224%20passing-brightgreen.svg)](tests/)

**TestIQ** is an enterprise-grade Python library that analyzes test coverage to identify duplicate, redundant, and inefficient tests. Save time, reduce CI costs, and improve test suite quality with intelligent analysis.

---

## 🚀 Key Features

- **🎯 Duplicate Detection** - Find exact duplicates, subsets, and similar tests
- **📊 Quality Scoring** - A-F grading with actionable recommendations
- **🚦 CI/CD Integration** - Quality gates, baselines, and trend tracking
- **⚡ Performance** - Parallel processing and caching for large test suites
- **🔌 Extensible** - Plugin system with custom hooks
- **📝 Multiple Formats** - HTML, CSV, JSON, and Markdown reports

---

## 📦 Installation

```bash
pip install testiq
```

---

## 🚀 How to Use TestIQ

### Quick Start

**See it in action immediately:**

```bash
# Run demo with sample data
testiq demo
```

**Generate per-test coverage data:**

TestIQ needs **per-test** coverage (which lines each test executes). Use our pytest plugin:

```bash
# Run tests with TestIQ plugin (easiest method)
pytest --testiq-output=testiq_coverage.json

# Then analyze with TestIQ
testiq analyze testiq_coverage.json --output=report.html
```

**Alternative methods:**

```bash
# Method 2: Use pytest coverage contexts
pytest --cov --cov-context=test
python -m testiq.coverage_converter coverage.json --with-contexts

# Method 3: Convert standard pytest coverage (limited functionality)
pytest --cov=your_package --cov-report=json
python -m testiq.coverage_converter coverage.json
```

**Manual sample data:**

```bash
# Create sample coverage data (for testing)
cat > testiq_coverage.json << 'EOF'
{
  "test_login_success": {
    "auth.py": [10, 11, 12, 15, 20, 25],
    "user.py": [5, 6, 7, 8]
  },
  "test_login_failure": {
    "auth.py": [10, 11, 12, 15, 16],
    "user.py": [5, 6]
  }
}
EOF

# Analyze the sample data
testiq analyze testiq_coverage.json
```

> **📖 See [Pytest Integration Guide](docs/pytest-integration.md) for complete setup instructions**

### CLI Usage

#### 1. Analyze Your Tests

```bash
# Basic analysis with terminal output
testiq analyze coverage.json

# Generate beautiful HTML report
testiq analyze coverage.json --format html --output reports/report.html

# Get quality score and recommendations
testiq quality-score coverage.json

# CSV export for spreadsheet analysis
testiq analyze coverage.json --format csv --output reports/results.csv

# JSON output for automation
testiq analyze coverage.json --format json --output reports/results.json
```

#### 2. CI/CD Integration

```bash
# Quality gates (exit code 2 if failed)
testiq analyze coverage.json --quality-gate --max-duplicates 5

# Save baseline for future comparisons
testiq analyze coverage.json --save-baseline my-baseline

# Compare against baseline
testiq analyze coverage.json --quality-gate --baseline my-baseline

# Manage baselines
testiq baseline list
testiq baseline show my-baseline
testiq baseline delete old-baseline
```

#### 3. Python API

```python
from testiq.analyzer import CoverageDuplicateFinder
import json

# Create analyzer with performance options
finder = CoverageDuplicateFinder(
    enable_parallel=True,
    max_workers=4,
    enable_caching=True
)

# Load coverage data
with open('coverage.json') as f:
    coverage_data = json.load(f)

# Add test coverage
for test_name, test_coverage in coverage_data.items():
    finder.add_test_coverage(test_name, test_coverage)

# Find issues
exact_duplicates = finder.find_exact_duplicates()
subset_duplicates = finder.find_subset_duplicates()
similar_tests = finder.find_similar_coverage(threshold=0.8)

# Generate reports
from testiq.reporting import HTMLReportGenerator
html_gen = HTMLReportGenerator(finder)
html_gen.generate(Path("reports/report.html"), threshold=0.8)

# Quality analysis
from testiq.analysis import QualityAnalyzer
analyzer = QualityAnalyzer(finder)
score = analyzer.calculate_score(threshold=0.8)
print(f"Quality Score: {score.overall_score}/100 (Grade: {score.grade})")
```

#### 4. Examples & Testing

**See complete working examples:**
- 📁 **[Python API Examples](examples/python/)** - Complete demonstration of all features
- 📁 **[Bash Examples](examples/bash/)** - Quick CLI testing scripts
- 📁 **[CI/CD Examples](examples/cicd/)** - Jenkins & GitHub Actions integration
- 📖 **[Manual Testing Guide](docs/manual-testing.md)** - Comprehensive testing guide

**CI/CD Integration:**
- [Jenkinsfile Example](examples/cicd/Jenkinsfile) - Complete Jenkins pipeline with quality gates
- [GitHub Actions Example](examples/cicd/github-actions.yml) - Full workflow with error handling

---

### Next Steps

1. **Try the demo:** `testiq demo`
2. **Analyze your tests:** `testiq analyze coverage.json`
3. **Run examples:** `python examples/python/manual_test.py`
4. **Integrate with CI/CD:** See [examples/cicd/](examples/cicd/)

---

## 💡 Why TestIQ?

- ✅ **Reduce Test Count** - Remove 10-30% of redundant tests
- ✅ **Faster CI/CD** - Shorter test execution times  
- ✅ **Lower Costs** - Reduced CI resource usage
- ✅ **Better Quality** - Focus on valuable, unique tests

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[Installation Guide](docs/installation.md)** | How to install TestIQ |
| **[Pytest Integration](docs/pytest-integration.md)** | **Generate per-test coverage data** |
| **[User Guide](docs/guide.md)** | Complete usage guide with examples |
| **[CLI Reference](docs/cli-reference.md)** | Command-line interface documentation |
| **[API Reference](docs/api.md)** | Python API documentation |
| **[Integration Guide](docs/integration.md)** | pytest, unittest, GitHub Actions |
| **[Manual Testing Guide](docs/manual-testing.md)** | How to test TestIQ manually |
| **[Enterprise Features](docs/enterprise-features.md)** | Advanced capabilities |
| **[FAQ](docs/faq.md)** | Frequently asked questions |
| **[Contributing](docs/CONTRIBUTING.md)** | How to contribute |
| **[Changelog](docs/CHANGELOG.md)** | Version history |

---

## 🤝 Contributing

We welcome contributions! See **[CONTRIBUTING.md](docs/CONTRIBUTING.md)** for guidelines.

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🔒 Security

For security vulnerabilities, see **[SECURITY.md](docs/SECURITY.md)** for responsible disclosure.

---

**Made with ❤️ by Kiran K Kotari**
