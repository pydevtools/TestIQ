<!-- ⚠️ MARKED FOR DELETION - See docs/DELETE_THESE_FILES.md -->
<!-- Reason: Most content covered in main README and examples -->

# Frequently Asked Questions

## General

### What is TestIQ?

TestIQ is an intelligent test analysis tool that finds duplicate and redundant tests by analyzing code coverage data. It helps you reduce CI time and maintain a cleaner test suite.

### How does TestIQ work?

TestIQ uses a coverage-based approach: if two tests cover exactly the same lines of code, they're likely redundant. It compares the set of lines covered by each test to find:
- Exact duplicates (100% identical coverage)
- Subset relationships (one test completely covered by another)
- Similar tests (high coverage overlap using Jaccard similarity)

### Why coverage-based detection?

Coverage-based detection is:
- **Simple**: No complex analysis needed
- **Fast**: Set operations are O(1) for comparisons  
- **Language-agnostic**: Works with any language/framework
- **Reliable**: Clear signal with low false positives
- **Practical**: Uses existing coverage infrastructure

---

## Usage

### Do I need to modify my tests?

No! TestIQ works with your existing tests. You just need to generate per-test coverage data.

### What test frameworks are supported?

TestIQ works with any framework that can produce coverage data:
- Python: pytest, unittest, nose
- JavaScript: Jest, Mocha, Jasmine
- Java: JUnit with JaCoCo
- Ruby: RSpec with SimpleCov
- And more!

See the [Integration Guide](integration.md) for details.

### Can I use TestIQ without pytest?

Yes! TestIQ is framework-agnostic. It just needs coverage data in JSON format. See [Integration Guide](integration.md) for examples with different frameworks.

### How do I generate coverage data?

See the [Integration Guide](integration.md) for your specific framework. Generally:

1. Enable per-test coverage tracking
2. Run your tests
3. Export coverage data to JSON
4. Run TestIQ analysis

---

## Results & Interpretation

### Should I delete all flagged tests?

No! Always review flagged tests manually. Tests with identical coverage might:
- Test different edge cases with different inputs
- Verify different error conditions
- Serve as regression tests for specific bugs

Use TestIQ results as a starting point for manual review.

### What's a good similarity threshold?

Default (0.7 / 70%): Good balance for most projects
- Higher (0.8-0.9): More conservative, fewer false positives
- Lower (0.5-0.7): More aggressive, more review needed

Start with default and adjust based on your results.

### What if two tests cover the same code but test different things?

This is expected! Coverage-based detection finds tests with similar _execution paths_, not similar _intent_. Examples:

```python
def test_divide_positive():
    assert divide(10, 2) == 5  # Covers lines 10-15

def test_divide_negative():
    assert divide(-10, 2) == -5  # Covers same lines 10-15
```

Both tests are valuable despite identical coverage. Always consider:
- Different input values
- Different edge cases
- Different expected outcomes

### Can TestIQ detect semantic duplicates?

No. TestIQ focuses on coverage-based detection. It won't catch:
- Tests with different coverage but same purpose
- Tests written differently but testing the same thing
- Tests with identical assertions but different setup

This is intentional - it keeps the tool simple, fast, and reliable.

---

## Technical

### What's the performance for large test suites?

TestIQ is fast:
- 100 tests: < 1 second
- 1,000 tests: ~5 seconds
- 10,000 tests: ~2 minutes

Performance depends on:
- Number of tests
- Lines covered per test
- Similarity threshold

### How much memory does TestIQ use?

Approximately: `Number of tests × Average lines per test × 16 bytes`

Example:
- 1,000 tests
- 100 lines average per test
- ≈ 1.6 MB memory usage

For very large suites (>10,000 tests), consider batch processing.

### Can I run TestIQ in CI/CD?

Yes! TestIQ is designed for CI/CD integration. Use JSON output format:

```bash
testiq analyze coverage.json --format json --output results.json
```

See [Integration Guide](integration.md#cicd-integration) for examples.

### Does TestIQ modify my code or tests?

No. TestIQ only analyzes data and produces reports. It never modifies your code.

---

## Troubleshooting

### "No duplicates found" but I know there are some

Possible causes:

1. **Coverage data incomplete**: Ensure all tests are included
2. **File paths don't match**: Use consistent relative paths
3. **Threshold too high**: Try lowering `--threshold`
4. **Tests cover different code**: They might not be duplicates

### TestIQ is slow on my project

Try:

1. **Increase threshold**: `--threshold 0.9` reduces comparisons
2. **Filter tests**: Analyze subsets separately
3. **Check coverage data**: Ensure it's not including library code
4. **Batch processing**: Process tests in smaller groups

### Coverage data format error

Ensure your JSON follows this format:

```json
{
  "test_name": {
    "file.py": [1, 2, 3],
    "other.py": [10, 20]
  }
}
```

Common errors:
- Missing quotes around keys
- Line numbers as strings instead of integers
- Nested structures

### Tests flagged as duplicates but aren't

This can happen when:

1. **Same setup, different assertions**: Tests use same code path but verify different things
2. **Parameterized tests**: Multiple tests with same structure
3. **Different edge cases**: Tests cover same code with different inputs

Solution: Review flagged tests and keep ones that test different scenarios.

---

## Best Practices

### How often should I run TestIQ?

**Recommended schedule:**
- **Locally**: Before committing large test changes
- **CI**: On every PR
- **Weekly**: Generate reports for team review

### Should I fail CI if duplicates are found?

Not recommended. Instead:
- Generate report as artifact
- Post to PR comments
- Track metrics over time
- Review during code review

Example CI check:

```bash
# Analyze but don't fail
testiq analyze coverage.json --format markdown --output report.md
# Always exit 0
exit 0
```

### How do I track improvement over time?

1. Run TestIQ regularly
2. Save reports with timestamps
3. Track metrics:
   - Number of exact duplicates
   - Number of subset duplicates
   - Percentage of tests flagged

Example:

```bash
testiq analyze coverage.json --format json --output "reports/$(date +%Y%m%d).json"
```

### What should I do after finding duplicates?

1. **Review**: Manually verify each flagged test
2. **Categorize**:
   - True duplicates → Remove
   - Different edge cases → Keep
   - Can be merged → Refactor
3. **Refactor**: Consider parametrized tests for similar tests
4. **Document**: Note why tests were kept/removed

---

## Comparison

### How is TestIQ different from code duplication tools?

**Code duplication tools** (PMD, SonarQube):
- Find duplicate _code_
- Look at syntax/structure
- Apply to all code

**TestIQ**:
- Finds duplicate _tests_
- Looks at coverage/behavior
- Specific to test suites

Both are useful but serve different purposes!

### Do I still need code coverage tools?

Yes! Coverage tools (coverage.py, Istanbul) tell you what code is tested. TestIQ tells you what tests are redundant. They complement each other.

### Can I use TestIQ with SonarQube?

Yes! They serve different purposes:
- **SonarQube**: Overall code quality, code duplication
- **TestIQ**: Test suite optimization, test duplication

Use both for comprehensive quality analysis.

---

## Contributing

### Can I contribute?

Yes! Contributions are welcome. See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

### I found a bug, what should I do?

Open an issue on [GitHub](https://github.com/testiq-dev/testiq/issues) with:
- TestIQ version
- Test framework and version
- Sample coverage data (if possible)
- Expected vs actual behavior

### Can I add support for my framework?

Yes! We welcome integrations. Either:
1. Contribute to TestIQ repository
2. Create a plugin/extension
3. Share your integration approach in discussions

---

## Licensing & Commercial Use

### What's the license?

MIT License - free for personal and commercial use.

### Can I use TestIQ in my company?

Yes! MIT license allows commercial use.

### Is there a paid version?

Not currently. TestIQ is fully open source. Future SaaS features (dashboards, historical tracking) may be offered as optional paid services.

---

## Still Have Questions?

- 📫 Email: kirankotari@live.com
- 🐛 Issues: [GitHub Issues](https://github.com/testiq-dev/testiq/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/testiq-dev/testiq/discussions)
- 📚 Docs: [Full Documentation](https://github.com/testiq-dev/testiq/tree/main/docs)
