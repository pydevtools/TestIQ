# TestIQ Examples

This directory contains comprehensive examples demonstrating how to use TestIQ in different scenarios.

## 🆕 What's New in Latest Version

- **Enhanced Code Quality**: Reduced cognitive complexity in analysis engine for better maintainability
- **Improved Constants Management**: String literals extracted to constants following best practices
- **Better Type Support**: Added type stubs for click and PyYAML for enhanced IDE autocomplete
- **pytest Now Included**: No need to install pytest separately - it's now a core dependency!
- **Refined Error Handling**: Unused parameters properly marked, unused variables removed
- **Cleaner Code**: F-strings without placeholders fixed, nested conditionals simplified

## 📁 Directory Structure

```
examples/
├── python/              # Python API examples
│   └── manual_test.py  # Complete Python API demonstration
├── bash/               # Shell script examples
│   └── quick_test.sh   # Quick CLI testing script
├── cicd/               # CI/CD integration examples
│   ├── Jenkinsfile     # Jenkins pipeline example
│   ├── github-actions.yml  # GitHub Actions workflow example
│   └── gitlab-ci.yml   # GitLab CI/CD pipeline example
├── sample_coverage.json    # Sample coverage data for testing
└── README.md          # This file
```

## 🚀 Quick Start

### Run Python API Example

The Python example demonstrates all TestIQ features including duplicate detection, quality scoring, report generation, CI/CD features, plugins, and security validation.

```bash
# From project root
python examples/python/manual_test.py

# From examples directory
cd examples/python
python manual_test.py
```

**What it does:**
- ✅ Demonstrates exact, subset, and similarity duplicate detection
- ✅ Shows quality scoring with refactored recommendation engine
- ✅ Generates HTML, CSV, and Markdown reports (with improved styling)
- ✅ Demonstrates CI/CD features (quality gates, baselines)
- ✅ Shows plugin system usage
- ✅ Validates security features
- ✅ Uses constants following TestIQ best practices

**Generated outputs:** `reports/test_report.html`, `reports/test_report.csv`, `reports/test_report.md`

**Latest improvements:**
- Uses string constants to avoid duplication
- Demonstrates improved code organization
- Shows proper error handling patterns

### Run Pytest Plugin Example ✨ NEW

Demonstrates using the TestIQ pytest plugin to generate per-test coverage data.

```bash
# From project root
python examples/python/pytest_plugin_example.py
```
- ✅ **Note**: pytest is now included with testiq installation!

**What it does:**
- ✅ Runs pytest with `--testiq-output` flag
- ✅ Generates per-test coverage in TestIQ format
- ✅ Analyzes coverage to find duplicates
- ✅ Creates HTML reports with results

**Key insight:** Shows the proper way to generate TestIQ-compatible coverage data from pytest!

### Run Bash CLI Example

Quick test script that runs all main CLI commands.

```bash
# From project root (recommended)
bash examples/bash/quick_test.sh

# Or from examples/bash directory
cd examples/bash
./quick_test.sh
```

**What it tests:**
1. Demo command
2. Basic analysis (with improved recommendation engine)
4. HTML report generation (with enhanced styling)
5. Quality gate checking
6. Baseline management
7. Python API integration

**Latest features tested:**
- Enhanced error handling
- Improved code quality checks
- Better performance with caching
7. Python API integration

## 🔧 CI/CD Integration Examples

### Jenkins Pipeline

**File:** [examples/cicd/Jenkinsfile](cicd/Jenkinsfile)

Complete Jenkins declarative pipeline showing:
- ✅ Environment setup with virtual environment
- ✅ Running tests with coverage
- ✅ TestIQ analysis with quality gates
- ✅ Exception handling (UNSTABLE vs FAILURE)
- ✅ Baseline management for trend tracking
- ✅ Report publishing and artifact archiving

**Key features:**
```groovy
// Quality gate with error handling
try {
    sh 'testiq analyze coverage.json --quality-gate --max-duplicates 10'
    currentBuild.result = 'SUCCESS'
} catch (Exception e) {
    // Mark as UNSTABLE instead of FAILURE
    currentBuild.result = 'UNSTABLE'
    echo "Quality gate failed but continuing..."
}
```

**Usage:**
1. Copy `Jenkinsfile` to your repository root
2. Configure Jenkins to use it as pipeline script
3. Adjust thresholds in environment variables
4. Run pipeline!

**When quality gate fails:**
- Build marked as `UNSTABLE` (yellow) not `FAILURE` (red)
- Pipeline continues to publish reports
- Artifacts are archived for review
- Optional notifications sent

### GitHub Actions

**File:** [examples/cicd/github-actions.yml](cicd/github-actions.yml)

Complete GitHub Actions workflow showing:
- ✅ Multi-step workflow with proper error handling
- ✅ Quality gate checks with continue-on-error
- ✅ Artifact uploading (reports available for 30 days)
- ✅ PR comments with quality scores
- ✅ Job summaries with analysis results
- ✅ Baseline comparison for pull requests

**Key features:**
```yaml
# Quality gate with custom handling
- name: Quality gate check
  id: quality-gate
  continue-on-error: true  # Don't stop workflow on failure
  run: |
    testiq analyze coverage.json --quality-gate \
      --max-duplicates 10 --threshold 0.8

# Handle failure appropriately
- name: Handle quality gate failure
  if: steps.quality-gate.outcome == 'failure'
  run: |
    echo "::warning::Quality gate failed!"
    exit 1  # Fail job but artifacts still uploaded
```

**Usage:**
1. Copy to `.github/workflows/testiq-quality.yml`
2. Push to repository
3. Workflow runs automatically on push/PR
4. View results in Actions tab

**When quality gate fails:**
- Step fails but workflow continues
- Reports uploaded to artifacts
- PR comment shows failure with details
- Job summary shows quality score
- Workflow marked as failed (red X)

### GitLab CI/CD

**File:** [examples/cicd/gitlab-ci.yml](cicd/gitlab-ci.yml)

Complete GitLab CI/CD pipeline showing:
- ✅ Multi-stage pipeline (test, analyze, quality-gate, report)
- ✅ Caching for faster builds
- ✅ Quality gate checks with custom error handling
- ✅ GitLab Pages integration for report publishing
- ✅ Baseline comparison for merge requests
- ✅ Scheduled quality checks (nightly builds)

**Key features:**
```yaml
# Quality gate with custom handling
testiq:quality-gate:
  script:
    - |
      testiq analyze coverage.json --quality-gate || {
        echo "⚠️ Quality gate failed!"
        exit 1  # Fail pipeline
      }
  
  # Or allow failure for non-blocking
  allow_failure: true
  
  # Always publish reports
  artifacts:
    when: always
    paths:
      - reports/
```

**Usage:**
1. Copy to `.gitlab-ci.yml` in repository root
2. Push to GitLab
3. Pipeline runs automatically
4. View reports in job artifacts or GitLab Pages

**When quality gate fails:**
- Job fails by default (can be overridden with `allow_failure: true`)
- Reports still uploaded to artifacts
- Available in GitLab Pages (on main branch)
- Manual retry available

## 📊 Sample Coverage Data

**File:** `sample_coverage.json`

Sample pytest coverage data for testing TestIQ features. Contains intentional duplicates and test patterns for demonstration.

**Structure:**
```json
{
  "test_name": {
    "file.py": [1, 2, 3, 4, 5],
    "other.py": [10, 11, 12]
  }
}
```

**Usage in your tests:**
```bash
# Use with CLI
testiq analyze examples/sample_coverage.json

# Generate from your tests
pytest --cov=. --cov-report=json:coverage.json
testiq analyze coverage.json
```

## 💡 Real-World Usage Examples

### Example 1: Local Development

```bash
# Quick quality check during development
pytest --cov=. --cov-report=json:coverage.json
testiq quality-score coverage.json

# Full analysis with report
testiq analyze coverage.json --format html --output reports/analysis.html
open reports/analysis.html  # View in browser
```

### Example 2: Pre-commit Hook

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
pytest --cov=. --cov-report=json:coverage.json
testiq analyze coverage.json --quality-gate --max-duplicates 5
if [ $? -ne 0 ]; then
    echo "❌ Quality gate failed! Fix duplicate tests before committing."
    exit 1
fi
```

### Example 3: Python Script Integration

```python
from testiq.analyzer import CoverageDuplicateFinder
from testiq.cicd import QualityGate, QualityGateChecker
import json
import sys

# Load coverage data
with open('coverage.json') as f:
    coverage_data = json.load(f)

# Analyze
finder = CoverageDuplicateFinder()
for test_name, test_cov in coverage_data.items():
    finder.add_test_coverage(test_name, test_cov)

# Check quality gate
gate = QualityGate(max_duplicates=10, max_duplicate_percentage=15.0)
checker = QualityGateChecker(gate)
passed, details = checker.check(finder, threshold=0.8)

if not passed:
    print("❌ Quality gate failed!")
    for failure in details['failures']:
        print(f"  • {failure}")
    sys.exit(1)

print("✅ Quality gate passed!")
```

### Example 4: Jenkins Shared Library

Create a reusable Jenkins shared library function:

```groovy
// vars/testIQAnalysis.groovy
def call(Map config = [:]) {
    def coverageFile = config.coverageFile ?: 'coverage.json'
    def maxDuplicates = config.maxDuplicates ?: 10
    def threshold = config.threshold ?: 0.8
    
    try {
        sh """
            testiq analyze ${coverageFile} \
                --quality-gate \
                --max-duplicates ${maxDuplicates} \
                --threshold ${threshold} \
                --format html \
                --output reports/testiq-report.html
        """
        return [success: true, message: 'Quality gate passed']
    } catch (Exception e) {
        currentBuild.result = 'UNSTABLE'
        return [success: false, message: e.message]
    }
}
```

Usage in Jenkinsfile:
```groovy
@Library('my-shared-library') _

pipeline {
    stages {
        stage('Quality Check') {
            steps {
                script {
                    def result = testIQAnalysis(
                        coverageFile: 'coverage.json',
                        maxDuplicates: 5,
                        threshold: 0.9
                    )
                    echo result.message
                }
            }
        }
    }
}
```

## 🎯 Exception Handling Best Practices

### Jenkins

**Option 1: Mark as UNSTABLE (Recommended)**
```groovy
try {
    sh 'testiq analyze coverage.json --quality-gate'
} catch (Exception e) {
    currentBuild.result = 'UNSTABLE'  // Yellow build
    // Continue pipeline to publish reports
}
```

**Option 2: Fail Pipeline**
```groovy
// Quality gate failure stops pipeline
sh 'testiq analyze coverage.json --quality-gate'
// Build fails if quality gate fails
```

**Option 3: Conditional Failure**
```groovy
def exitCode = sh(
    script: 'testiq analyze coverage.json --quality-gate',
    returnStatus: true
)

if (exitCode != 0) {
    if (env.BRANCH_NAME == 'main') {
        error("Quality gate failed on main branch!")  // Fail
    } else {
        currentBuild.result = 'UNSTABLE'  // Warning only on feature branches
    }
}
```

### GitHub Actions

**Option 1: Continue on Error (Recommended)**
```yaml
- name: Quality gate
  continue-on-error: true
  run: testiq analyze coverage.json --quality-gate

- name: Upload reports
  if: always()  # Upload even on failure
  uses: actions/upload-artifact@v4
```

**Option 2: Fail Job**
```yaml
- name: Quality gate
  run: testiq analyze coverage.json --quality-gate
  # Job fails if quality gate fails
```

**Option 3: Custom Exit Code Handling**
```yaml
- name: Quality gate
  id: quality
  run: |
    testiq analyze coverage.json --quality-gate || echo "failed=true" >> $GITHUB_OUTPUT

- name: Handle failure
  if: steps.quality.outputs.failed == 'true'
  run: |
    echo "::warning::Quality gate failed"
    exit 1  # Fail after reports are generated
```

## 📚 Additional Resources

- **Full Documentation:** See [docs/](../docs/) folder
- **API Reference:** [docs/api.md](../docs/api.md)
- **CLI Reference:** [docs/cli-reference.md](../docs/cli-reference.md)
- **Integration Guide:** [docs/integration.md](../docs/integration.md)
- **Manual Testing:** [docs/manual-testing.md](../docs/manual-testing.md)

## 🤝 Contributing Examples

Have a useful example? Contributions welcome!

1. Create your example file in appropriate directory
2. Add documentation in this README
3. Test thoroughly
4. Submit PR

## 📝 License

These examples are part of TestIQ and licensed under the same terms as the main project.
