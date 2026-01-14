<!-- ⚠️ MARKED FOR DELETION - See docs/DELETE_THESE_FILES.md -->
<!-- Reason: Redundant documentation index - main README is sufficient -->

# TestIQ Documentation

Welcome to the TestIQ documentation! This directory contains comprehensive guides, API references, and resources for using TestIQ.

## 📚 Documentation Index

### Getting Started
- **[Installation Guide](installation.md)** - How to install TestIQ
- **[Quick Start Guide](guide.md#quick-start)** - Get up and running in minutes
- **[Integration Guide](integration.md)** - Integrate with pytest, unittest, and other frameworks

### Core Documentation
- **[User Guide](guide.md)** - Complete guide to using TestIQ
  - Core concepts (exact duplicates, subsets, similarity)
  - CLI usage with examples
  - Python API tutorials
  - Best practices
  - Troubleshooting
- **[API Reference](api.md)** - Complete Python API documentation
  - `CoverageDuplicateFinder` - Core analysis class
  - Reporting classes (HTML, CSV)
  - CI/CD integration (Quality Gates, Baselines, Trends)
  - Plugin system
  - Quality analysis
- **[CLI Reference](cli-reference.md)** - Command-line interface documentation
  - `testiq analyze` - Analyze test coverage
  - `testiq quality-score` - Calculate quality metrics
  - `testiq baseline` - Manage baselines
  - All options and flags

### Advanced Features
- **[Enterprise Features](enterprise-features.md)** - Enterprise capabilities
  - Structured logging
  - Configuration management
  - Security features
  - Performance optimizations
- **[FAQ](faq.md)** - Frequently asked questions

### Project Information
- **[CHANGELOG](CHANGELOG.md)** - Version history and release notes
  - v0.2.0 - Code quality improvements, enhanced features (current)
  - v0.1.0 - Initial release with enterprise features
- **[Production Readiness](PRODUCTION_READINESS.md)** - Production deployment guide
  - Feature completeness status
  - Test coverage analysis
  - Deployment recommendations
- **[Security Policy](SECURITY.md)** - Security and vulnerability reporting
- **[Contributing Guidelines](CONTRIBUTING.md)** - How to contribute to TestIQ

## 🔍 Quick Navigation

### By Task

**I want to...**

- **Install TestIQ** → [Installation Guide](installation.md)
- **Analyze my tests** → [Quick Start](guide.md#quick-start)
- **Integrate with pytest** → [Integration Guide](integration.md)
- **Use the Python API** → [API Reference](api.md)
- **Set up CI/CD** → [User Guide - CI/CD Integration](guide.md#cicd-integration)
- **Generate HTML reports** → [API Reference - HTMLReportGenerator](api.md#htmlreportgenerator)
- **Create quality gates** → [API Reference - QualityGate](api.md#qualitygate)
- **Extend with plugins** → [API Reference - Plugin System](api.md#plugin-system)
- **Configure TestIQ** → [Enterprise Features - Configuration](enterprise-features.md#configuration-management)
- **Report a security issue** → [Security Policy](SECURITY.md)
- **Contribute code** → [Contributing Guidelines](CONTRIBUTING.md)
- **See what's new** → [CHANGELOG](CHANGELOG.md)

### By User Type

**Developers:**
- Start with [Quick Start Guide](guide.md#quick-start)
- Learn [Core Concepts](guide.md#core-concepts)
- Explore [Python API](api.md)

**DevOps Engineers:**
- Read [CI/CD Integration](guide.md#cicd-integration)
- Learn about [Quality Gates](api.md#qualitygate)
- Set up [GitHub Actions](guide.md#github-actions-integration)

**QA Engineers:**
- Understand [Duplicate Types](guide.md#duplicate-types)
- Learn [Best Practices](guide.md#best-practices)
- Use [HTML Reports](api.md#htmlreportgenerator)

**Team Leads:**
- Review [Enterprise Features](enterprise-features.md)
- Check [Production Readiness](PRODUCTION_READINESS.md)
- See [Version History](CHANGELOG.md)

## 📖 Reading Order

### For New Users
1. [Installation Guide](installation.md) - Set up TestIQ
2. [Quick Start](guide.md#quick-start) - Run your first analysis
3. [Core Concepts](guide.md#core-concepts) - Understand how it works
4. [CLI Reference](cli-reference.md) - Learn the commands
5. [Best Practices](guide.md#best-practices) - Use it effectively

### For Advanced Users
1. [API Reference](api.md) - Deep dive into the API
2. [Enterprise Features](enterprise-features.md) - Advanced capabilities
3. [Integration Guide](integration.md) - Custom integrations
4. [Plugin System](api.md#plugin-system) - Extend functionality

### For Contributors
1. [Contributing Guidelines](CONTRIBUTING.md) - How to contribute
2. [Production Readiness](PRODUCTION_READINESS.md) - Project status
3. [Security Policy](SECURITY.md) - Security practices

## 🆘 Getting Help

- **General Questions** → Check [FAQ](faq.md) or [User Guide](guide.md)
- **API Questions** → See [API Reference](api.md)
- **Bug Reports** → [GitHub Issues](https://github.com/yourusername/testiq/issues)
- **Security Issues** → Follow [Security Policy](SECURITY.md)
- **Discussions** → [GitHub Discussions](https://github.com/yourusername/testiq/discussions)

## 📝 Documentation Standards

All documentation follows:
- **Markdown format** for readability
- **Code examples** for clarity
- **Cross-references** for navigation
- **Practical examples** over theory

## 🔄 Keeping Up to Date

Documentation is versioned with the code. Always refer to the docs matching your installed version:

```bash
# Check your version
testiq --version

# Documentation for your version
# docs for v0.2.0 are in this directory
```

---

**Need something not covered here?** Open an issue or discussion on GitHub!
