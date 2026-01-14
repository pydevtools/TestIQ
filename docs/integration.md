<!-- ⚠️ MARKED FOR DELETION - See docs/DELETE_THESE_FILES.md -->
<!-- Reason: Covered by examples/cicd/ directory with working examples -->

# Integration Guide

TestIQ works with any test framework that can produce per-test coverage data. This guide shows how to integrate TestIQ with popular testing frameworks.

## Coverage Data Format

TestIQ expects coverage data in JSON format:

```json
{
  "test_name_1": {
    "file1.py": [1, 2, 3, 10, 11],
    "file2.py": [5, 6, 7]
  },
  "test_name_2": {
    "file1.py": [1, 2, 3, 15, 16],
    "file3.py": [20, 21]
  }
}
```

Where:
- Keys are test names
- Values are dictionaries mapping filenames to lists of covered line numbers

---

## Python / pytest

### Method 1: Using pytest-cov Plugin

Install the pytest plugin (coming soon):

```bash
pip install pytest-testiq
```

Run pytest with TestIQ:

```bash
pytest --testiq
```

### Method 2: Custom Plugin (Manual)

Create a `conftest.py` with per-test coverage tracking:

```python
import json
import pytest
from coverage import Coverage

class PerTestCoveragePlugin:
    def __init__(self):
        self.test_coverage = {}
        self.current_test = None
        self.cov = None
    
    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_protocol(self, item):
        self.current_test = item.nodeid
        
        # Start coverage for this test
        self.cov = Coverage()
        self.cov.start()
        
        yield
        
        # Stop and collect coverage
        self.cov.stop()
        coverage_data = self.cov.get_data()
        
        test_coverage = {}
        for filename in coverage_data.measured_files():
            lines = coverage_data.lines(filename)
            if lines and '/site-packages/' not in filename:
                test_coverage[filename] = sorted(lines)
        
        self.test_coverage[self.current_test] = test_coverage
    
    def pytest_sessionfinish(self):
        # Save coverage data
        with open('coverage_data.json', 'w') as f:
            json.dump(self.test_coverage, f, indent=2)
        print(f"\nSaved coverage data to coverage_data.json")

def pytest_configure(config):
    config.pluginmanager.register(PerTestCoveragePlugin())
```

Then run:

```bash
pytest
testiq analyze coverage_data.json
```

---

## JavaScript / Jest

### Using Custom Reporter

Create `testiq-reporter.js`:

```javascript
const fs = require('fs');
const path = require('path');

class TestIQReporter {
  constructor(globalConfig, options) {
    this.coverage = {};
  }

  onTestResult(test, testResult) {
    testResult.testResults.forEach(result => {
      const testName = result.fullName;
      const coverage = result.coverage || {};
      
      const testCoverage = {};
      
      Object.keys(coverage).forEach(filename => {
        const fileCoverage = coverage[filename];
        const lines = Object.keys(fileCoverage.s)
          .map(Number)
          .sort((a, b) => a - b);
        
        testCoverage[path.relative(process.cwd(), filename)] = lines;
      });
      
      this.coverage[testName] = testCoverage;
    });
  }

  onRunComplete() {
    fs.writeFileSync(
      'coverage_data.json',
      JSON.stringify(this.coverage, null, 2)
    );
    console.log('\nSaved coverage data to coverage_data.json');
  }
}

module.exports = TestIQReporter;
```

Add to `jest.config.js`:

```javascript
module.exports = {
  reporters: ['default', './testiq-reporter.js'],
  collectCoverage: true,
  collectCoverageFrom: ['src/**/*.js'],
};
```

Run:

```bash
npm test
testiq analyze coverage_data.json
```

---

## Java / JUnit

### Using JaCoCo

Add JaCoCo plugin to `pom.xml`:

```xml
<plugin>
  <groupId>org.jacoco</groupId>
  <artifactId>jacoco-maven-plugin</artifactId>
  <version>0.8.10</version>
  <executions>
    <execution>
      <goals>
        <goal>prepare-agent</goal>
      </goals>
    </execution>
  </executions>
</plugin>
```

Create a custom listener to extract per-test coverage:

```java
import org.junit.runner.Description;
import org.junit.runner.Result;
import org.junit.runner.notification.RunListener;

public class TestIQListener extends RunListener {
    private Map<String, Map<String, List<Integer>>> coverage = new HashMap<>();
    
    @Override
    public void testFinished(Description description) throws Exception {
        // Extract coverage for this test
        String testName = description.getMethodName();
        // ... extract coverage data from JaCoCo
        
        coverage.put(testName, testCoverage);
    }
    
    @Override
    public void testRunFinished(Result result) throws Exception {
        // Write to JSON
        ObjectMapper mapper = new ObjectMapper();
        mapper.writeValue(new File("coverage_data.json"), coverage);
    }
}
```

---

## Ruby / RSpec

### Using SimpleCov

Add to `spec_helper.rb`:

```ruby
require 'simplecov'
require 'json'

class TestIQFormatter
  def initialize
    @test_coverage = {}
  end

  def format(result)
    result.files.each do |file|
      test_name = RSpec.current_example.full_description
      
      @test_coverage[test_name] ||= {}
      @test_coverage[test_name][file.filename] = file.covered_lines.map(&:line_number)
    end
  end

  def self.save_coverage
    File.write('coverage_data.json', JSON.pretty_generate(@test_coverage))
  end
end

SimpleCov.formatters = SimpleCov::Formatter::MultiFormatter.new([
  SimpleCov::Formatter::HTMLFormatter,
  TestIQFormatter
])

RSpec.configure do |config|
  config.after(:suite) do
    TestIQFormatter.save_coverage
  end
end
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Test Analysis

on: [push, pull_request]

jobs:
  analyze-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install testiq pytest pytest-cov
      
      - name: Run tests with coverage
        run: pytest --testiq
      
      - name: Analyze duplicates
        run: |
          testiq analyze coverage_data.json --format markdown --output report.md
      
      - name: Comment PR
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('report.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: report
            });
```

### GitLab CI

```yaml
test-analysis:
  stage: test
  script:
    - pip install testiq pytest
    - pytest --testiq
    - testiq analyze coverage_data.json --format markdown --output report.md
  artifacts:
    paths:
      - report.md
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

---

## Best Practices

1. **Exclude Library Code**: Filter out third-party library files from coverage data
2. **Run Regularly**: Integrate TestIQ into your CI pipeline
3. **Set Thresholds**: Use appropriate similarity thresholds for your project
4. **Review Results**: Don't blindly delete - review flagged tests
5. **Track Trends**: Monitor duplicate count over time

## Troubleshooting

### No Coverage Data Generated

- Ensure coverage is enabled in your test runner
- Check that per-test coverage is being tracked
- Verify JSON file format matches expected structure

### Missing Tests

- Check that test names are being captured correctly
- Ensure all test files are included in coverage
- Verify file paths are relative to project root

### False Positives

- Adjust similarity threshold
- Review test intent (same coverage doesn't always mean duplicate)
- Check for parameterized tests

## Need Help?

Open an issue on [GitHub](https://github.com/testiq-dev/testiq/issues) with:
- Your test framework and version
- Sample coverage data
- Expected vs actual behavior
