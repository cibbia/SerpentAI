# Serpent.AI – Security Policy

## Supported Versions

| Version | Supported | Security fixes |
|---------|-----------|----------------|
| 2025.x  | ✅        | ✅ |
| <2025   | ❌        | ❌ |

## Reporting a Vulnerability

Please email **security@serpent.ai** with a detailed description and, if possible, a proof-of-concept. You will receive an acknowledgement within **72 hours**. We aim to release patches within **14 days** for critical issues.

## Vulnerability Management

1. **Automated scanning** – Every push / PR and a weekly cron run `pip-audit` to detect known CVEs in Python dependencies.
2. **Dependency updates** – We rely on Dependabot to keep third-party libraries up-to-date.
3. **Release process** – Security fixes are back-ported to the latest release branch and documented in `CHANGELOG.md`.

## Hall of Fame

We thank all researchers who responsibly disclose vulnerabilities.