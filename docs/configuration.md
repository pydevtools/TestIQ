# TestIQ Configuration Files

## Overview

TestIQ supports configuration via TOML or YAML files. These files allow you to customize:
- **Logging**: Log level, file output, rotation settings
- **Security**: File size limits, max tests, allowed extensions
- **Performance**: Parallel processing, workers, caching
- **Analysis**: Similarity thresholds, coverage minimums

## Quick Start

1. **Copy an example file** to your project root:
   ```bash
   # For TOML format
   cp .testiq.toml.example .testiq.toml
   
   # For YAML format  
   cp .testiq.yaml.example .testiq.yaml
   ```

2. **Edit the configuration** to match your needs

3. **Run TestIQ** - it automatically loads `.testiq.toml` or `.testiq.yaml` from:
   - Current directory
   - Project root (searches up from current directory)

## Configuration Files

### `.testiq.toml.example`
**Format**: TOML (Tom's Obvious Minimal Language)  
**Best for**: Python projects, simple key-value configurations

### `.testiq.yaml.example`
**Format**: YAML (YAML Ain't Markup Language)  
**Best for**: CI/CD pipelines, multi-environment setups

## Example Configurations

### Development Environment
```toml
# .testiq.toml
[log]
level = "DEBUG"
file = "logs/testiq-dev.log"

[performance]
enable_parallel = true
max_workers = 8

[analysis]
similarity_threshold = 0.3  # Default: catch more potential duplicates
min_coverage_lines = 1
max_results = 1000
```

### CI/CD Environment
```yaml
# .testiq.yaml
log:
  level: WARNING
  file: null  # Console only for CI

performance:
  enable_parallel: true
  max_workers: 2  # CI has limited resources

analysis:
  similarity_threshold: 0.5  # Stricter for CI
  min_coverage_lines: 1
  max_results: 500
```

### Production Quality Gate
```toml
# .testiq.toml
[log]
level: "ERROR"

[security]
max_tests = 10000
max_file_size = 52428800  # 50MB

[analysis]
similarity_threshold = 0.7  # Very strict for production
min_coverage_lines = 5      # Ignore trivial tests
max_results = 100           # Focus on top issues
```

## Configuration Options

### Logging (`[log]`)
- `level`: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
- `file`: Path to log file (null for console only)
- `enable_rotation`: Rotate log files when they get large (default: true)
- `max_bytes`: Maximum log file size before rotation (default: 10MB)
- `backup_count`: Number of old log files to keep (default: 5)

### Security (`[security]`)
- `max_file_size`: Maximum input file size in bytes (default: 100MB)
- `max_tests`: Maximum number of tests to analyze (default: 50000)
- `max_lines_per_file`: Maximum lines per source file (default: 100000)
- `allowed_extensions`: List of allowed file extensions (default: [".json", ".yaml", ".yml"])

### Performance (`[performance]`)
- `enable_parallel`: Enable parallel processing (default: true)
- `max_workers`: Number of parallel workers (default: 4, auto: CPU count)
- `enable_caching`: Enable result caching (default: true)
- `cache_dir`: Cache directory (default: ~/.testiq/cache, null for default)

### Analysis (`[analysis]`)
- `similarity_threshold`: Minimum similarity to report (0.0-1.0, default: 0.3)
  - 0.3 = 30% overlap between tests
  - Higher values = more strict (fewer similar tests reported)
  - Lower values = more lenient (more similar tests reported)
- `min_coverage_lines`: Minimum coverage lines to consider a test (default: 1)
  - Tests with fewer lines are ignored
- `max_results`: Maximum results to display (default: 1000)
  - Prevents overwhelming output for large test suites

## Command-Line Override

CLI options always override config file settings:

```bash
# Config says threshold=0.3, but CLI overrides to 0.8
testiq analyze coverage.json --threshold 0.8

# Using custom config file
testiq --config my-config.yaml analyze coverage.json

# Setting log level via CLI
testiq --log-level DEBUG analyze coverage.json
```

### Available CLI Options

**Global Options** (for all commands):
```bash
testiq --help                        # Show help
testiq --version                     # Show version
testiq --config PATH                 # Custom config file
testiq --log-level LEVEL             # Set log level (DEBUG|INFO|WARNING|ERROR|CRITICAL)
testiq --log-file PATH               # Log file path
```

**Analyze Command Options:**
```bash
testiq analyze coverage.json --help  # Show all options

# Key options:
--threshold FLOAT                    # Similarity threshold (0.0-1.0, default: 0.3)
--format FORMAT                      # Output format: markdown|json|text|html|csv
--output PATH                        # Output file (required for html/csv)
--quality-gate                       # Enable quality gate (exit code 2 if failed)
--max-duplicates INTEGER             # Max allowed duplicates (default: 0)
--baseline PATH                      # Baseline file for comparison
--save-baseline PATH                 # Save results as baseline
```

**Example CI/CD Usage:**
```bash
# Run with quality gate (fail if duplicates found)
testiq analyze coverage.json \
  --threshold 0.5 \
  --quality-gate \
  --max-duplicates 0 \
  --format html \
  --output report.html
```

## Troubleshooting

**Config not loading?**
1. Check file name: `.testiq.toml` or `.testiq.yaml` (with leading dot)
2. Check location: Must be in current directory or project root
3. Run with debug: `testiq --log-level DEBUG analyze ...`

**Syntax errors?**
- TOML: Use `tomli` to validate: `python -c "import tomli; tomli.load(open('.testiq.toml', 'rb'))"`
- YAML: Use `pyyaml` to validate: `python -c "import yaml; yaml.safe_load(open('.testiq.yaml'))"`

## See Also

- [CLI Reference](docs/cli-reference.md) - Command-line options
- [API Documentation](docs/api.md) - Python API configuration
- [Examples](examples/) - Sample projects with configuration
