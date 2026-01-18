# AI-Generated Test Suite Example

This example demonstrates a common problem: **AI coding assistants generate tests quickly, but create duplicates and redundant tests that bloat your test suite.**

## The Problem

When using AI tools like GitHub Copilot, Cursor, or ChatGPT to generate tests:
- ✅ Tests are created fast
- ❌ Many tests are duplicates or subsets of each other
- ❌ Test maintenance becomes a nightmare
- ❌ CI time increases unnecessarily
- ❌ Coverage looks good, but quality is poor

## This Example

A simple calculator app with **50 AI-generated tests**:
- **18 duplicate tests** - Exact copies with different names
- **12 subset tests** - Tests that cover less than other tests
- **20 quality tests** - Actually useful tests

**Result**: 60% of tests are redundant! TestIQ catches this.

## Running the Demo

```bash
# Install dependencies
pip install testiq pytest pytest-cov

# Run tests with TestIQ
pytest --testiq-output=coverage.json

# Analyze with TestIQ
testiq analyze coverage.json --format html --output report.html

# Open the report
open report.html
```

## Expected Results

```
Test Quality Score: D (45/100)
- 18 exact duplicates found
- 12 subset duplicates found
- 40% of tests can be safely removed
- Estimated CI time savings: 2.5 minutes per run
```

## The Solution

Add TestIQ to your CI pipeline:

```yaml
- name: Quality Gate
  run: |
    pytest --testiq-output=coverage.json
    testiq analyze coverage.json --quality-gate 70
```

**Now AI-generated duplicates fail CI automatically!** ✅
