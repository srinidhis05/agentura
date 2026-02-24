# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please report it through
[GitHub Security Advisories](https://github.com/agentura-ai/agentura/security/advisories/new).

**Do not open a public issue for security vulnerabilities.**

We will acknowledge receipt within 48 hours and provide a detailed response
within 7 days indicating next steps.

## Supported Versions

| Version | Supported |
|---------|-----------|
| latest  | Yes       |

## Security Best Practices

When deploying Agentura:

- Never commit `.env` files or API keys to version control
- Use `AUTH_REQUIRED=true` in production
- Configure JWT/JWKS authentication on the gateway
- Use network policies to restrict inter-service communication
- Review skill definitions before deploying to production
