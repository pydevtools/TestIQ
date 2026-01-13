# Reports Directory

This directory contains all generated test analysis reports from TestIQ.

## Generated Files

All TestIQ analysis outputs are stored here:

- **`*.html`** - Interactive HTML reports with charts and styling
- **`*.csv`** - CSV exports for spreadsheet analysis
- **`*.md`** - Markdown reports for documentation

## Generating Reports

### CLI Commands
```bash
# HTML report
testiq analyze coverage.json --format html --output reports/report.html

# CSV report
testiq analyze coverage.json --format csv --output reports/report.csv

# JSON report
testiq analyze coverage.json --format json --output reports/report.json

# Markdown report
testiq analyze coverage.json --format markdown --output reports/report.md
```

### Python API
```python
from testiq.reporting import HTMLReportGenerator, CSVReportGenerator
from pathlib import Path

# HTML
html_gen = HTMLReportGenerator(finder)
html_gen.generate(Path("reports/report.html"))

# CSV
csv_gen = CSVReportGenerator(finder)
csv_gen.generate_summary(Path("reports/report.csv"))
```

## Git Tracking

This directory structure is tracked by Git (via `.gitkeep`), but generated report files are ignored to keep the repository clean.

## Cleanup

To remove all generated reports:
```bash
rm -f reports/*.html reports/*.csv reports/*.md
```

The `.gitkeep` file ensures the directory structure remains.
