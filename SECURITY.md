# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please send an email to security@aluvia.io.

Please include:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will respond within 48 hours and provide an estimated timeline for a fix.

## Security Best Practices

When using the Aluvia SDK:

1. **Keep API keys secure**: Never commit API keys to version control
2. **Use environment variables**: Store API keys in environment variables or secure vaults
3. **Limit connection IDs**: Don't share connection IDs publicly
4. **Update regularly**: Keep the SDK updated to the latest version
5. **Monitor usage**: Regularly check your Aluvia dashboard for unusual activity

## Known Security Considerations

- The local proxy server binds to 127.0.0.1 by default for security
- API keys are transmitted over HTTPS
- Proxy credentials are managed securely by the ConfigManager
