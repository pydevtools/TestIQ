# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| 0.1.x   | :x:                |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please bring it to our attention right away.

### Please DO NOT:

- Open a public GitHub issue for security vulnerabilities
- Disclose the vulnerability publicly before it has been addressed

### Please DO:

1. **Email us directly** at: security@testiq.dev (or use GitHub's private vulnerability reporting)
2. **Provide detailed information** including:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)
3. **Allow reasonable time** for us to respond and fix the issue before public disclosure

### What to Expect:

- **Acknowledgment**: We'll acknowledge receipt within 48 hours
- **Updates**: We'll keep you informed of progress at least every 5 business days
- **Timeline**: We aim to address critical vulnerabilities within 7 days
- **Credit**: We'll credit you in the security advisory (unless you prefer to remain anonymous)

## Security Measures in TestIQ

TestIQ implements several security measures:

### File Security
- Maximum file size limits (default 100MB)
- Path traversal protection
- Input validation for file paths
- Maximum test count limits (100,000 tests)

### Data Handling
- No external network requests
- All data processing is local
- No telemetry or data collection
- Safe JSON parsing with size limits

### Configuration
- Secure defaults for all settings
- YAML/TOML config validation
- No code execution from config files

### Dependencies
- Minimal dependency footprint
- Regular dependency updates
- Security scanning with GitHub Dependabot

## Known Security Considerations

### Coverage Data Files
TestIQ processes JSON coverage files that may be untrusted. We mitigate risks by:
- Limiting file sizes
- Validating JSON structure
- Rejecting malformed data
- Using safe parsing methods

### Plugin System
The plugin system allows custom code execution. Users should:
- Only use plugins from trusted sources
- Review plugin code before installation
- Run TestIQ in isolated environments for untrusted plugins

## Best Practices for Users

1. **Keep Updated**: Always use the latest version of TestIQ
2. **Verify Downloads**: Check package integrity from PyPI
3. **Limit Permissions**: Run TestIQ with minimal required permissions
4. **Isolate Analysis**: Analyze untrusted coverage data in sandboxed environments
5. **Review Plugins**: Audit any third-party plugins before use

## Security Updates

Security updates will be released as:
- **Critical**: Immediate patch release with security advisory
- **High**: Patch release within 7 days
- **Medium**: Included in next minor release
- **Low**: Included in regular release cycle

## Disclosure Policy

- We follow coordinated disclosure
- We'll notify affected users once a fix is available
- We'll publish security advisories on GitHub
- We'll update this document with any new security information

## Contact

For security issues: security@testiq.dev
For general questions: info@testiq.dev

---

*Last updated: 2024-01-15*
