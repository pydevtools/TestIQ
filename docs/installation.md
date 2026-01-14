<!-- ⚠️ MARKED FOR DELETION - See docs/DELETE_THESE_FILES.md -->
<!-- Reason: Installation is simple (pip install testiq) - doesn't need dedicated doc -->

# Installation Guide

## Prerequisites

- Python 3.9 or higher
- pip or uv package manager

## Installation Methods

### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install TestIQ
uv pip install testiq
```

### Using pip

```bash
pip install testiq
```

### Development Installation

To install TestIQ for development with all dev dependencies:

```bash
# Clone the repository
git clone https://github.com/testiq-dev/testiq.git
cd testiq

# Install with dev dependencies using uv
uv pip install -e ".[dev]"

# Or using pip
pip install -e ".[dev]"
```

## Verify Installation

```bash
# Check version
testiq --version

# Run demo
testiq demo
```

## Updating

```bash
# Using uv
uv pip install --upgrade testiq

# Using pip
pip install --upgrade testiq
```

## Uninstallation

```bash
# Using uv
uv pip uninstall testiq

# Using pip
pip uninstall testiq
```

## Dependencies

TestIQ requires:
- `click` - For CLI interface
- `coverage` - For coverage data handling
- `rich` - For beautiful terminal output

All dependencies are automatically installed.

## Troubleshooting

### Command not found

If `testiq` command is not found after installation:

```bash
# Check if it's in your PATH
which testiq

# If using pip --user, add to PATH
export PATH="$HOME/.local/bin:$PATH"
```

### Import Error

If you get import errors:

```bash
# Verify installation
python -c "import testiq; print(testiq.__version__)"
```

### Permission Denied

If you get permission errors:

```bash
# Use --user flag
pip install --user testiq

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install testiq
```
