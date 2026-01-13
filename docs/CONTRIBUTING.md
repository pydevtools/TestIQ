# Contributing to TestIQ

Thank you for considering contributing to TestIQ! We welcome contributions from everyone.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue on GitHub with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- TestIQ version and Python version
- Sample coverage data (if applicable)

### Suggesting Features

Feature suggestions are welcome! Please open an issue with:
- Clear description of the feature
- Use case / motivation
- Example usage

### Pull Requests

1. **Fork the repository**
2. **Create a branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**
4. **Add tests** for new functionality
5. **Run tests**: `uv run pytest`
6. **Run linters**: `uv run ruff check . && uv run black --check .`
7. **Commit** with clear message: `git commit -m "Add feature X"`
8. **Push**: `git push origin feature/your-feature-name`
9. **Open a Pull Request**

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/testiq.git
cd testiq

# Install uv if you haven't
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Run linters
uv run ruff check .
uv run black .
```

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for public functions/classes
- Keep functions focused and small
- Write tests for new code

## Testing

- Write unit tests for new functionality
- Maintain or improve code coverage
- Run the full test suite before submitting PR
- Include edge cases in tests

## Documentation

- Update docstrings for code changes
- Update docs/ for user-facing changes
- Add examples for new features
- Keep README.md up to date

## Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- First line should be < 72 characters
- Reference issues and PRs where appropriate

## Code Review Process

1. Maintainer reviews PR
2. Address feedback if any
3. Once approved, maintainer merges
4. Your contribution will be in the next release!

## Community Guidelines

- Be respectful and constructive
- Help others learn and grow
- Follow the Code of Conduct
- Have fun!

## Questions?

Feel free to open an issue or discussion on GitHub.

Thank you for contributing! 🎉
