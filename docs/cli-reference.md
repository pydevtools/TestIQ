# CLI Reference

Complete reference for TestIQ command-line interface.

## Synopsis

```
testiq [OPTIONS] COMMAND [ARGS]...
```

## Global Options

### --version

Show the version and exit.

```bash
testiq --version
```

### --help

Show help message and exit.

```bash
testiq --help
```

---

## Commands

### analyze

Analyze test coverage data to find duplicates.

**Syntax:**

```bash
testiq analyze COVERAGE_FILE [OPTIONS]
```

**Arguments:**

- `COVERAGE_FILE` - JSON file containing per-test coverage data (required)

**Options:**

#### --threshold, -t

Similarity threshold (0.0-1.0) for detecting similar tests.

- **Type**: float
- **Default**: 0.7
- **Range**: 0.0 to 1.0

```bash
testiq analyze coverage.json --threshold 0.8
```

Higher values = more strict matching (fewer results, higher confidence)
Lower values = more lenient matching (more results, may include false positives)

#### --output, -o

Output file for the report.

- **Type**: path
- **Default**: stdout

```bash
testiq analyze coverage.json --output report.md
```

#### --format, -f

Output format for the report.

- **Type**: choice
- **Choices**: `markdown`, `json`, `text`
- **Default**: `text`

```bash
# Markdown format (good for documentation)
testiq analyze coverage.json --format markdown

# JSON format (good for CI/CD integration)
testiq analyze coverage.json --format json

# Text format with rich formatting (default, best for terminal)
testiq analyze coverage.json --format text
```

**Examples:**

```bash
# Basic analysis
testiq analyze coverage_data.json

# Analysis with custom threshold
testiq analyze coverage_data.json --threshold 0.85

# Save markdown report
testiq analyze coverage_data.json --format markdown --output duplicates.md

# Generate JSON for CI pipeline
testiq analyze coverage_data.json --format json --output results.json

# Strict matching (90% similarity)
testiq analyze coverage_data.json -t 0.9 -f markdown -o strict_report.md
```

---

### demo

Run a demonstration with sample data.

**Syntax:**

```bash
testiq demo
```

**Description:**

Runs TestIQ with built-in sample test coverage data to demonstrate functionality.
Useful for:
- Understanding output format
- Testing installation
- Learning how to interpret results

**Example:**

```bash
testiq demo
```

---

## Input Format

TestIQ expects coverage data in JSON format:

```json
{
  "test_module::TestClass::test_method_1": {
    "src/auth.py": [10, 11, 12, 15, 20, 25],
    "src/user.py": [5, 6, 7, 8]
  },
  "test_module::TestClass::test_method_2": {
    "src/auth.py": [10, 11, 12, 15, 20, 25],
    "src/user.py": [5, 6, 7, 8]
  }
}
```

**Format Requirements:**
- Top-level object with test names as keys
- Each test maps to an object of filename → line number arrays
- Filenames should be relative paths
- Line numbers must be integers

---

## Output Formats

### Text Format (default)

Rich formatted output with tables and colors, optimized for terminal viewing.

**Features:**
- Colored tables
- Summary statistics
- Easy to read in terminal

**Use when:**
- Running interactively
- Viewing results in terminal
- Debugging

### Markdown Format

GitHub-flavored markdown suitable for documentation and reports.

**Features:**
- Headers and tables
- Suitable for version control
- Renders in GitHub/GitLab

**Use when:**
- Generating reports
- Adding to documentation
- Committing to repository

### JSON Format

Structured data for programmatic processing.

**Features:**
- Machine-readable
- Easy to parse
- CI/CD integration

**Structure:**

```json
{
  "exact_duplicates": [
    ["test1", "test2"],
    ["test3", "test4", "test5"]
  ],
  "subset_duplicates": [
    {
      "subset": "test_minimal",
      "superset": "test_complete",
      "ratio": 0.33
    }
  ],
  "similar_tests": [
    {
      "test1": "test_login_v1",
      "test2": "test_login_v2",
      "similarity": 0.85
    }
  ]
}
```

**Use when:**
- CI/CD integration
- Automated processing
- Custom reporting

---

## Exit Codes

- `0` - Success
- `1` - Error (invalid input, file not found, etc.)

---

## Environment Variables

None currently supported.

---

## Examples

### Basic Workflow

```bash
# 1. Generate coverage data (varies by framework)
pytest --testiq

# 2. Analyze
testiq analyze coverage_data.json

# 3. Review results
# (displayed in terminal)
```

### CI/CD Integration

```bash
# Generate JSON report for CI
testiq analyze coverage_data.json \
  --format json \
  --output testiq-report.json

# Check if duplicates exist
if [ $(jq '.exact_duplicates | length' testiq-report.json) -gt 0 ]; then
  echo "Found duplicate tests!"
  exit 1
fi
```

### Strict Analysis

```bash
# Only report tests with 95%+ similarity
testiq analyze coverage_data.json \
  --threshold 0.95 \
  --format markdown \
  --output high-confidence-duplicates.md
```

### Multi-format Output

```bash
# Generate all formats
testiq analyze coverage_data.json --format text
testiq analyze coverage_data.json --format markdown -o report.md
testiq analyze coverage_data.json --format json -o data.json
```

---

## Tips

1. **Start with demo**: Run `testiq demo` to understand output
2. **Adjust threshold**: Default 0.7 works for most cases, adjust based on results
3. **Use markdown for docs**: Save reports with `--format markdown` for documentation
4. **JSON for automation**: Use `--format json` for CI/CD pipelines
5. **Review before deleting**: Always manually review flagged tests before removal

---

## See Also

- [Integration Guide](integration.md) - How to generate coverage data
- [API Documentation](api.md) - Python API reference
- [FAQ](faq.md) - Frequently asked questions
