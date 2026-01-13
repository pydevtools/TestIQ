# Pytest Integration Guide

TestIQ analyzes **per-test** coverage to find duplicate and redundant tests. This guide shows how to generate compatible coverage data from pytest.

## The Challenge

Pytest's standard `coverage.json` format provides **aggregated coverage** (all tests combined):

```json
{
  "meta": {"format": 3, "version": "7.13.1", ...},
  "files": {
    "src/module.py": {
      "executed_lines": [1, 2, 3, ...]
    }
  }
}
```

But TestIQ needs **per-test coverage**:

```json
{
  "test_login": {
    "auth.py": [10, 11, 12],
    "user.py": [5, 6]
  },
  "test_logout": {
    "auth.py": [20, 21],
    "session.py": [15]
  }
}
```

## Solutions

### Option 1: TestIQ Pytest Plugin (Recommended)

Use our pytest plugin to automatically track per-test coverage:

#### Installation

The plugin is included with TestIQ. Just install TestIQ:

```bash
pip install testiq
```

#### Usage

```bash
# Run tests with TestIQ plugin
pytest --testiq-output=testiq_coverage.json

# Then analyze with TestIQ
testiq analyze testiq_coverage.json
```

#### Configure in pytest.ini

```ini
[pytest]
addopts = --testiq-output=testiq_coverage.json
```

Now just run `pytest` normally:

```bash
pytest
testiq analyze testiq_coverage.json
```

### Option 2: Pytest Coverage Contexts

If you already use `pytest-cov`, enable test contexts:

```bash
# Generate coverage with test contexts
pytest --cov=src --cov-report=json --cov-context=test

# Convert to TestIQ format
python -m testiq.coverage_converter coverage.json --with-contexts

# Analyze
testiq analyze testiq_coverage.json
```

### Option 3: Convert Aggregated Coverage

If you only have standard pytest coverage:

```bash
# Generate standard coverage
pytest --cov=src --cov-report=json

# Convert (creates synthetic "all_tests" entry)
python -m testiq.coverage_converter coverage.json

# Analyze (limited - can only check for zero duplicates)
testiq analyze testiq_coverage.json
```

**Note**: This option provides aggregated coverage, so TestIQ's duplicate detection is limited.

## CI/CD Integration

### GitHub Actions

```yaml
name: Test Quality Analysis
on: [push, pull_request]

jobs:
  testiq:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      
      - name: Install dependencies
        run: |
          pip install testiq pytest pytest-cov
      
      - name: Run tests with TestIQ plugin
        run: |
          pytest --testiq-output=testiq_coverage.json
      
      - name: Analyze test quality
        run: |
          testiq analyze testiq_coverage.json \
            --output=reports/analysis.html \
            --quality-gate \
            --max-duplicates=5
      
      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: testiq-report
          path: reports/
```

### Jenkins

```groovy
pipeline {
    agent any
    
    stages {
        stage('Test with TestIQ') {
            steps {
                sh '''
                    pip install testiq pytest
                    pytest --testiq-output=testiq_coverage.json
                '''
            }
        }
        
        stage('Analyze Test Quality') {
            steps {
                script {
                    def exitCode = sh(
                        script: 'testiq analyze testiq_coverage.json --quality-gate --max-duplicates=5',
                        returnStatus: true
                    )
                    
                    if (exitCode != 0) {
                        currentBuild.result = 'UNSTABLE'
                        echo "Warning: Test quality issues detected"
                    }
                }
            }
        }
        
        stage('Publish Reports') {
            steps {
                publishHTML([
                    reportDir: 'reports',
                    reportFiles: 'analysis.html',
                    reportName: 'TestIQ Analysis'
                ])
            }
        }
    }
}
```

## Troubleshooting

### Error: "Coverage lines must be a list"

This means you're using pytest's standard `coverage.json`. Use one of these solutions:
- Use the TestIQ plugin: `pytest --testiq-output=...`
- Enable contexts: `pytest --cov-context=test`
- Convert the file: `python -m testiq.coverage_converter`

### Plugin not working

Make sure pytest can find the plugin:

```bash
# Check if plugin is registered
pytest --trace-config | grep testiq

# Explicitly enable
pytest -p testiq.pytest_plugin --testiq-output=output.json
```

### Performance with large test suites

The TestIQ plugin uses `sys.settrace()` which adds overhead. Tips:

1. **Run on a subset**: `pytest tests/unit --testiq-output=...`
2. **Use parallel execution**: `pytest -n auto --testiq-output=...`
3. **Filter to specific tests**: `pytest -k "not slow" --testiq-output=...`

## How It Works

### TestIQ Plugin

The plugin uses Python's `sys.settrace()` to track line execution per test:

```python
def pytest_runtest_protocol(item):
    """Start tracing for this test"""
    sys.settrace(trace_function)

def trace_function(frame, event, arg):
    """Record each line execution"""
    if event == "line":
        record_line(frame.f_code.co_filename, frame.f_lineno)
```

### Pytest Contexts

Pytest-cov's context feature tracks which test executed which code:

```bash
# Enable context tracking
pytest --cov --cov-context=test

# Coverage data includes contexts
{
  "files": {
    "file.py": {
      "contexts": {
        "tests/test_foo.py::test_bar": [1, 2, 3],
        "tests/test_baz.py::test_qux": [4, 5, 6]
      }
    }
  }
}
```

## Best Practices

1. **Start with the plugin**: It's the easiest and most accurate
2. **Run regularly**: Integrate into CI/CD to catch test bloat early
3. **Set quality gates**: Use `--max-duplicates` to enforce standards
4. **Review reports**: HTML reports show exactly what's duplicated
5. **Iterate**: Remove duplicates gradually, don't break everything at once

## Examples

### Example 1: Basic Usage

```bash
# Generate per-test coverage
pytest --testiq-output=coverage.json

# Find duplicates
testiq analyze coverage.json

# Generate HTML report
testiq analyze coverage.json --output=report.html
```

### Example 2: Quality Gate

```bash
# Fail build if more than 10 duplicate tests
pytest --testiq-output=coverage.json
testiq analyze coverage.json \
  --quality-gate \
  --max-duplicates=10 || exit 1
```

### Example 3: Baseline Comparison

```bash
# First run: establish baseline
pytest --testiq-output=coverage.json
testiq analyze coverage.json --save-baseline=main

# Later runs: compare against baseline
pytest --testiq-output=coverage.json
testiq analyze coverage.json \
  --baseline=main \
  --quality-gate
```

## See Also

- [CLI Reference](cli-reference.md) - Full command options
- [CI/CD Integration](integration.md) - More pipeline examples
- [User Guide](guide.md) - Understanding TestIQ analysis
