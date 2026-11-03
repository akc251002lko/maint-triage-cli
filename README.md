
# maint-triage-cli

**A zero-dependency Python CLI for analyzing GitHub repository maintenance activity and generating actionable triage reports.**

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Dependencies](https://img.shields.io/badge/Dependencies-None-success)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Overview

`maint-triage-cli` is a lightweight command-line tool that helps maintainers identify maintenance tasks in public GitHub repositories.

It analyzes open issues and pull requests, identifies items requiring attention, and generates structured reports in Markdown, plain text, or JSON.

The tool uses GitHub's REST API and Python's standard library. No third-party packages are required.

## Features

- **Missing-label detection:** Identify open issues without labels.
- **Stale issue detection:** Find issues that have not been updated within a configurable period.
- **Stale pull request detection:** Identify inactive pull requests.
- **Draft PR tracking:** Find pull requests still marked as drafts.
- **Review bottlenecks:** Surface pull requests with outstanding requested reviewers.
- **CI attention:** Flag pull requests whose combined commit status is pending, failing, or errored.
- **Authenticated API access:** Use GITHUB_TOKEN for higher rate limits and repositories the token can access.
- **Automatic pagination:** Retrieve results across multiple GitHub API pages.
- **Multiple output formats:** Generate Markdown, text, and JSON reports.
- **Optional authentication:** Support GitHub tokens through environment variables.
- **Error handling:** Handle invalid repositories, inaccessible repositories, API errors, and network failures.
- **Zero dependencies:** Operates entirely with Python's standard library.

## Requirements

- Python 3.9 or newer.
- Internet connection.
- Access to the GitHub REST API.

No external Python packages are necessary.

## Installation

Clone the repository:

```bash
git clone https://github.com/akc251002lko/maint-triage-cli.git
```

Navigate into the project:

```bash
cd maint-triage-cli
```

## Usage

Run the tool using Python:

```bash
python triage.py --repo psf/requests
```

### Command-line arguments

| Argument | Description | Default |
|---|---|---|
| `--repo` | GitHub repository in owner/name format | Required |
| `--days` | Stale activity threshold in days | 30 |
| `--format` | Output format: markdown, text, json | markdown |

### Examples

**1. Generate a standard triage report**

```bash
python triage.py --repo psf/requests
```

**2. Use a custom stale threshold**

```bash
python triage.py --repo psf/requests --days 60
```

**3. Generate a Markdown report**

```bash
python triage.py --repo psf/requests --format markdown
```

**4. Generate a plain-text report**

```bash
python triage.py --repo psf/requests --format text
```

**5. Generate a JSON report**

```bash
python triage.py --repo psf/requests --format json
```

## Authentication

The tool supports optional GitHub authentication through the `GITHUB_TOKEN` environment variable.

Authentication is useful when accessing private repositories or when higher API rate limits are required.

### Linux / macOS

```bash
export GITHUB_TOKEN="your_github_token"
```

### Windows PowerShell

```powershell
$env:GITHUB_TOKEN="your_github_token"
```

Then run the application normally.

**Security:** Never hardcode or commit personal access tokens into source code or configuration files.

## Report categories

The analyzer generates four maintenance categories.

| Category | Description |
|---|---|
| Missing Labels | Open issues without assigned labels |
| Stale Issues | Issues inactive for the configured threshold |
| Stale Pull Requests | Pull requests inactive for the configured threshold |
| Draft Pull Requests | Pull requests marked as drafts |

An item can appear in more than one category.

## Example output

```text
==========================================================
             MAINTAINER TRIAGE REPORT
==========================================================

 Repository : psf/requests
 Generated  : 2026-11-02T12:00:00Z
 Threshold  : 30 days

----------------------------------------------------------
 TRIAGE SUMMARY
----------------------------------------------------------

 Issues missing labels                 3
 Stale issues                          5
 Stale pull requests                   2
 Draft pull requests                   1

----------------------------------------------------------
```

The actual counts depend on the selected repository and the time of analysis.

## Project structure

```text
maint-triage-cli/
│
├── .github/
│   └── workflows/
│       └── test.yml
│
├── tests/
│   └── test_triage.py
│
├── triage.py
├── README.md
├── LICENSE
└── .gitignore
```

## Running tests

The project uses Python's built-in `unittest` framework.

Run all tests:

```bash
python -m unittest discover -s tests -v
```

The automated tests cover repository validation, date calculations, issue classification, report generation, and API pagination.

## Error handling

The application handles common operational errors, including:

- Invalid repository identifiers.
- Repositories that cannot be found or accessed.
- Authentication failures.
- GitHub API access restrictions and rate limits.
- Network errors and request timeouts.
- Invalid API responses.

## Technical design

The application follows a lightweight, standard-library-only architecture.

| Component | Responsibility |
|---|---|
| Argument parser | CLI configuration |
| Repository validator | Input validation |
| GitHub API client | HTTP communication |
| Pagination handler | Multi-page data retrieval |
| Classification engine | Maintenance categorization |
| Report generator | Structured report creation |
| Output renderer | Markdown, text, and JSON formatting |

## Limitations

- Only open issues and pull requests are analyzed.
- Staleness is based on the last update timestamp.
- Stale items are identified, not automatically closed.
- The tool does not modify repositories or GitHub issues.
- Review and CI signals depend on GitHub API permissions and the status data exposed by the repository.
- CI attention uses commit combined status; repositories relying exclusively on GitHub Checks may show an unknown status.
- The tool reports findings only and does not automatically close issues, merge PRs, or change labels.

## Contributing

Contributions, bug reports, and feature suggestions are welcome.

Please review the contribution guidelines before submitting changes.

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE) for details.

---

**maint-triage-cli** — Better visibility. Smarter triage. Healthier repositories.
