# Contributing

Thank you for considering a contribution to Maint Triage CLI.

## Development Requirements

- Python 3.11 or newer.
- Python standard library only; do not add third-party runtime dependencies without prior discussion.
- GitHub API access is optional for unit tests. Tests should mock network calls.

## Before Submitting

Run the checks from the repository root:

```bash
python -m py_compile triage.py tests/test_triage.py
python -m unittest discover -s tests -v
python triage.py --help
```

## Contribution Guidelines

- Keep changes focused and document user-visible behaviour.
- Add or update unit tests for bug fixes and new report categories.
- Preserve read-only behaviour; do not add write operations to the GitHub API client.
- Read credentials only from `GITHUB_TOKEN`; never hard-code secrets.
- Preserve pagination, timeout handling, and clear HTTP error messages.
- Update README examples when CLI options or output formats change.

## Pull Requests

Describe the problem, the implementation, and the tests executed. Include sample output only when it contains no private repository data or credentials.

## Security

For vulnerability reporting, follow [SECURITY.md](SECURITY.md). Do not publish exploitable details in a public issue.
