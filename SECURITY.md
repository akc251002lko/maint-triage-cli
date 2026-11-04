# Security Policy

## Supported Versions

Security fixes are applied to the current default branch. This project is maintained as an actively developed command-line utility; older commits and forks may not receive fixes.

## Reporting a Vulnerability

Please do not disclose exploitable details in a public issue. If GitHub private vulnerability reporting is enabled for this repository, use it. Otherwise, contact the maintainer through the public GitHub profile and request a private reporting channel.

Include the affected commit, impact, reproducible steps, and a suggested mitigation where possible. Do not include access tokens, private repository data, or personal information in a report.

## Credential Safety

- Store GitHub credentials in the `GITHUB_TOKEN` environment variable.
- Never commit tokens, passwords, or private keys.
- Use the minimum GitHub token permissions needed for the repositories being analyzed.
- Treat generated reports as potentially sensitive because they can contain repository issue titles, URLs, and maintenance metadata.

## Scope and Limitations

These tools are read-only GitHub API clients. They do not modify repositories, issues, labels, pull requests, or branch settings. A report is advisory and must be reviewed by a maintainer before acting on it.
