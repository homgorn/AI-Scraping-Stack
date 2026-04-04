# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.4.x   | ✅ Yes    |
| < 0.4   | ❌ No     |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please:

1. **DO NOT** open a public issue.
2. Email us at: **security@ai-scraping-stack.com** (or open a private security advisory on GitHub)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and aim to release a patch within 7 days.

## Security Best Practices

- Never commit `.env` files or API keys
- Rotate API keys regularly
- Use HTTPS in production
- Enable Rate Limiting
- Restrict CORS origins
- Use strong API keys (32+ random characters)
- Keep dependencies updated (`pip audit`)
