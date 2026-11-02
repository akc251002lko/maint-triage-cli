# maint-triage-cli

A lightweight, zero-dependency CLI tool designed to help open-source maintainers automate the "invisible work" of triaging issues and pull requests. 

Maintainer burnout is real. Keeping track of stale issues, missing labels, and unreviewed PRs takes time away from writing code. This tool generates a quick, actionable report so you know exactly what needs attention.

## Features

- **Missing Labels:** Quickly spot open issues that haven't been categorized.
- **Stale Issues & PRs:** Find items that haven't been updated in `X` days.
- **Draft PRs:** Keep an eye on open draft pull requests.
- **Markdown or Text Output:** Generate reports perfectly formatted to paste into GitHub issues, discussions, or team chats.

## Requirements

- Python 3.8+
- No external dependencies (uses Python standard library).

## Usage

Run the tool against any public GitHub repository:

```bash
python triage.py --repo owner/name# maint-triage-cli
A tiny CLI that generates maintainer triage reports for GitHub repos.
