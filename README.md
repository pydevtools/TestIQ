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
## 📦 Installation

```bash
pip install testiq
```

## 🎯 Quick Start

### 1. Analyze Your Tests

```bash
# Basic analysis with terminal output
testiq analyze coverage.json

# Generate beautiful HTML report
testiq analyze coverage.json --format html --output report.html

# CSV export for data analysis
testiq analyze coverage.json --format csv --output duplicates.csv

# JSON output for programmatic use
testiq analyze coverage.json --format json --output results.json
```

---

## 🎯 Quick Start

**CLI Usage:**

```bash
# Analyze tests and generate report
testiq analyze coverage.json --format html --output report.html

# Get quality score
testiq quality-score coverage.json

# CI/CD with quality gates
testiq analyze coverage.json --quality-gate --max-duplicates 5
```

**Python API:**

```python
from testiq.analyzer import CoverageDuplicateFinder

finder = CoverageDuplicateFinder()
finder.add_test_coverage("test_login", {"auth.py": [10, 11, 12]})

duplicates = finder.find_exact_duplicates()
report = finder.generate_report()
```

📖 **[Full Documentation →](docs/README.md)** | **[User Guide →](docs/guide.md)** | **[API Reference →](docs/api.md)**

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
| **[User Guide](docs/guide.md)** | Complete usage guide with examples |
| **[CLI Reference](docs/cli-reference.md)** | Command-line interface documentation |
| **[API Reference](docs/api.md)** | Python API documentation |
| **[Integration Guide](docs/integration.md)** | pytest, unittest, GitHub Actions |
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
