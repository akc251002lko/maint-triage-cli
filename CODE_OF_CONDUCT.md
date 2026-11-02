Contributing to Maint Triage CLI

Thank you for your interest in contributing to Maint Triage CLI!

We welcome bug reports, feature suggestions, documentation improvements, and code contributions that help make this project more reliable and useful.

Please read these guidelines before submitting a contribution.

---

1. Code of Conduct

All contributors are expected to maintain a respectful, constructive, and professional environment.

Please review our "Code of Conduct" (CODE_OF_CONDUCT.md).

2. Ways to Contribute

You can contribute in several ways:

- Report bugs and unexpected behavior.
- Suggest new features and improvements.
- Improve documentation and examples.
- Add automated tests.
- Improve error handling and API reliability.
- Optimize performance and maintainability.
- Review proposed changes.

3. Reporting Bugs

Before reporting a bug:

1. Check whether the issue has already been reported.
2. Confirm that you are using a supported Python version.
3. Verify that the repository name and command-line arguments are valid.
4. Include the steps required to reproduce the problem.

When reporting a bug, provide:

- A clear description of the problem.
- The command you executed.
- Expected behavior.
- Actual behavior.
- Python version and operating system.
- Relevant error messages.

Never include access tokens, passwords, or other sensitive information in bug reports.

4. Suggesting Features

Feature suggestions should explain:

- The problem the feature solves.
- Why the feature would be useful.
- How the proposed functionality should work.
- Any potential compatibility or maintenance considerations.

Keep proposals focused and consistent with the project's purpose.

5. Development Guidelines

Maint Triage CLI is designed to remain lightweight and dependency-free.

Contributions should follow these principles:

- Use Python's standard library wherever possible.
- Maintain compatibility with Python 3.9 and newer.
- Follow PEP 8 conventions.
- Prefer clear, readable, maintainable code.
- Use descriptive function and variable names.
- Handle expected errors explicitly.
- Avoid unnecessary complexity.
- Never commit credentials or personal access tokens.

6. Testing Requirements

All meaningful code changes should include appropriate automated tests.

Run the test suite:

python -m unittest discover -s tests -v

Validate Python syntax:

python -m py_compile triage.py tests/test_triage.py

Ensure existing tests continue to pass before submitting changes.

7. Pull Request Guidelines

Before submitting a pull request:

1. Make sure your changes have a clear purpose.
2. Keep changes focused and reasonably small.
3. Add or update tests where appropriate.
4. Update documentation when functionality changes.
5. Verify that automated checks pass.

Provide a clear pull request description containing:

- What changed.
- Why the change was necessary.
- How the changes were tested.
- Any relevant issue references.

8. Commit Message Guidelines

Use clear, descriptive commit messages.

Recommended prefixes:

Prefix| Purpose
"feat:"| New functionality
"fix:"| Bug fixes
"docs:"| Documentation changes
"test:"| Test improvements
"refactor:"| Code restructuring
"chore:"| Maintenance tasks

Examples:

feat: add issue priority analysis
fix: handle GitHub API rate limits
docs: improve usage instructions
test: expand pagination coverage

9. Compatibility

Contributions must preserve compatibility with Python 3.9 and newer.

Avoid introducing third-party dependencies unless a change has been explicitly discussed and approved.

10. Scope of the Project

Maint Triage CLI focuses on analyzing open GitHub issues and pull requests and producing actionable maintenance reports.

Contributions should support this purpose.

The tool should remain read-only unless a future feature is explicitly designed and reviewed to support repository modifications.

11. Questions and Support

For questions, bug reports, or feature discussions, please use the repository's GitHub Issues section.

Thank you for helping improve Maint Triage CLI!

---

Maint Triage CLI — Better visibility. Smarter triage. Healthier repositories.