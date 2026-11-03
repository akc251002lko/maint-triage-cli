
#!/usr/bin/env python3
"""
maint-triage-cli
Professional GitHub repository maintenance analyzer.

Uses only Python's standard library.
"""

import argparse
import json
import logging
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

from datetime import datetime, timezone
from typing import Any


API = "https://api.github.com"
TIMEOUT = 30
PER_PAGE = 100
logger = logging.getLogger("maint_triage_cli")


class TriageError(Exception):
    """Expected application error."""


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def paint(value, color):
    if sys.stdout.isatty() and "NO_COLOR" not in os.environ:
        return f"{color}{value}{Colors.RESET}"
    return str(value)


def validate_repo(repo):
    """Validate GitHub owner/repository identifier."""

    if not isinstance(repo, str) or repo.count("/") != 1:
        raise TriageError("Repository must use owner/name format.")

    owner, name = repo.split("/")

    owner_pattern = r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$"
    name_pattern = r"^[A-Za-z0-9._-]{1,100}$"

    if not re.fullmatch(owner_pattern, owner):
        raise TriageError("Invalid GitHub owner name.")

    if (
        not re.fullmatch(name_pattern, name)
        or name in (".", "..")
        or name.endswith(".git")
    ):
        raise TriageError("Invalid GitHub repository name.")

    return owner, name


def github_get(url: str, token: str | None = None) -> tuple[Any, str]:
    """Fetch one GitHub API page."""

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "maint-triage-cli/2.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    logger.debug("GitHub API GET %s", url)

    try:
        with urllib.request.urlopen(
            request,
            timeout=TIMEOUT,
        ) as response:

            data = json.loads(response.read().decode("utf-8"))
            next_link = response.headers.get("Link", "")

            return data, next_link

    except urllib.error.HTTPError as error:
        if error.code == 401:
            message = "Authentication failed. Check GITHUB_TOKEN."

        elif error.code == 403:
            remaining = error.headers.get(
                "X-RateLimit-Remaining", "unknown"
            )
            message = (
                "Access forbidden or API rate limit exceeded. "
                f"Remaining requests: {remaining}."
            )

        elif error.code == 404:
            message = "Repository not found or inaccessible."

        elif error.code == 451:
            message = "Repository unavailable for legal reasons."

        else:
            message = f"GitHub API returned HTTP {error.code}."

        raise TriageError(message)

    except urllib.error.URLError as error:
        raise TriageError(f"Network error: {error.reason}")

    except (TimeoutError, OSError):
        raise TriageError("GitHub API request timed out or failed.")

    except (json.JSONDecodeError, UnicodeDecodeError):
        raise TriageError("GitHub returned an invalid JSON response.")


def fetch_open_items(owner, name, token=None):
    """Fetch all open issues and pull requests using pagination."""

    owner = urllib.parse.quote(owner, safe="")
    name = urllib.parse.quote(name, safe="")

    url = (
        f"{API}/repos/{owner}/{name}/issues"
        f"?state=open&per_page={PER_PAGE}"
    )

    all_items = []

    while url:
        data, link_header = github_get(url, token)

        if not isinstance(data, list):
            raise TriageError("Unexpected GitHub API response.")

        all_items.extend(data)

        match = re.search(
            r'<([^>]+)>;\s*rel="next"',
            link_header,
        )

        url = match.group(1) if match else None

    return all_items


def fetch_open_pull_requests(owner: str, name: str, token: str | None = None) -> list[dict[str, Any]]:
    """Fetch open PRs with reviewer, draft, and head-commit metadata."""
    owner_q = urllib.parse.quote(owner, safe="")
    name_q = urllib.parse.quote(name, safe="")
    url = f"{API}/repos/{owner_q}/{name_q}/pulls?state=open&per_page={PER_PAGE}"
    results: list[dict[str, Any]] = []
    while url:
        data, link_header = github_get(url, token)
        if not isinstance(data, list):
            raise TriageError("Unexpected pull request API response.")
        results.extend(data)
        match = re.search(r'<([^>]+)>;\s*rel="next"', link_header)
        url = match.group(1) if match else None
    for item in results:
        item["pull_request"] = item.get("pull_request", {"url": item.get("url", "")})
        head = item.get("head", {}).get("sha")
        item["ci_state"] = "unknown"
        if head:
            status_url = f"{API}/repos/{owner_q}/{name_q}/commits/{urllib.parse.quote(head, safe='')}/status"
            try:
                status, _ = github_get(status_url, token)
                if isinstance(status, dict):
                    item["ci_state"] = str(status.get("state", "unknown"))
            except TriageError as error:
                logger.warning("Could not inspect CI status for PR #%s: %s", item.get("number"), error)
    return results

def days_since(timestamp, now=None):
    """Calculate the age of the last update in whole days."""

    try:
        updated = datetime.fromisoformat(
            timestamp.replace("Z", "+00:00")
        )

        if updated.tzinfo is None:
            raise ValueError("Timezone information is missing.")

        reference = now or datetime.now(timezone.utc)

        return max(0, (reference - updated).days)

    except (ValueError, AttributeError, TypeError):
        raise TriageError(
            f"Invalid GitHub timestamp: {timestamp}"
        )


def classify_items(items: list[dict[str, Any]], threshold: int, now: datetime) -> dict[str, list[dict[str, Any]]]:
    """Categorize issues and pull requests."""

    issues = [
        item for item in items
        if "pull_request" not in item
    ]

    prs = [
        item for item in items
        if "pull_request" in item
    ]

    missing_labels = [
        item for item in issues
        if not item.get("labels")
    ]

    stale_issues = [
        item for item in issues
        if days_since(item.get("updated_at"), now) >= threshold
    ]

    stale_prs = [
        item for item in prs
        if days_since(item.get("updated_at"), now) >= threshold
    ]

    drafts = [
        item for item in prs
        if item.get("draft") is True
    ]
    review_bottlenecks = [
        item for item in prs
        if item.get("requested_reviewers")
    ]
    ci_attention = [
        item for item in prs
        if str(item.get("ci_state", "unknown")).lower() in ("failure", "error", "pending")
    ]

    return {
        "missing_labels": missing_labels,
        "stale_issues": stale_issues,
        "stale_prs": stale_prs,
        "draft_prs": drafts,
        "review_bottlenecks": review_bottlenecks,
        "ci_attention": ci_attention,
    }


def format_item(item, now):
    """Format one GitHub issue or pull request."""

    age = days_since(item.get("updated_at"), now)

    return {
        "number": item["number"],
        "title": item["title"],
        "url": item["html_url"],
        "updated_days_ago": age,
        "labels": [
            label["name"]
            for label in item.get("labels", [])
        ],
    }


def build_report(repo, categories, threshold, now):
    """Create a structured triage report."""

    sections = {}

    for name, items in categories.items():
        sections[name] = [
            format_item(item, now)
            for item in items
        ]

    for key in ("missing_labels", "stale_issues", "stale_prs", "draft_prs", "review_bottlenecks", "ci_attention"):
        sections.setdefault(key, [])

    total_open = sum(len(items) for items in categories.values())

    return {
        "repository": repo,
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stale_threshold_days": threshold,
        "summary": {
            "issues_missing_labels": len(
                sections["missing_labels"]
            ),
            "stale_issues": len(sections["stale_issues"]),
            "stale_pull_requests": len(sections["stale_prs"]),
            "draft_pull_requests": len(sections["draft_prs"]),
        },
        "sections": sections,
    }


def markdown_section(title, items):
    """Generate a Markdown report section."""

    lines = [f"## {title} ({len(items)})", ""]

    if not items:
        lines.append("_None_")
    else:
        for item in items:
            lines.append(
                f"- [#{item['number']} "
                f"{item['title']}]({item['url']}) "
                f"— updated {item['updated_days_ago']}d ago"
            )

    lines.append("")
    return "\n".join(lines)


def text_section(title, items):
    """Generate a plain-text report section."""

    lines = [f"{title} ({len(items)})"]

    if not items:
        lines.append("  None")
    else:
        for item in items:
            lines.append(
                f"  #{item['number']} {item['title']} "
                f"— {item['updated_days_ago']}d ago"
            )
            lines.append(f"     {item['url']}")

    return "\n".join(lines)


def render_report(report, output_format):
    """Render the report in the requested format."""

    if output_format == "json":
        return json.dumps(report, indent=2, ensure_ascii=False)

    sections = report["sections"]
    threshold = report["stale_threshold_days"]

    if output_format == "markdown":
        output = [
            f"# Triage Report: {report['repository']}",
            "",
            f"Generated: {report['generated_at']}",
            f"Stale threshold: {threshold} days",
            "",
            "## Summary",
            "",
        ]

        for key, value in report["summary"].items():
            output.append(f"- {key.replace('_', ' ').title()}: {value}")

        output.append("")

        titles = [
            ("Missing Labels", "missing_labels"),
            (f"Stale Issues (>= {threshold} days)", "stale_issues"),
            (f"Stale Pull Requests (>= {threshold} days)", "stale_prs"),
            ("Draft Pull Requests", "draft_prs"),
            ("Review Bottlenecks", "review_bottlenecks"),
            ("CI Attention Required", "ci_attention"),
        ]

        for title, key in titles:
            output.append(
                markdown_section(title, sections[key])
            )

        return "\n".join(output)

    output = [
        f"TRIAGE REPORT: {report['repository']}",
        f"Generated: {report['generated_at']}",
        f"Stale threshold: {threshold} days",
        "",
    ]

    titles = [
        ("Missing Labels", "missing_labels"),
        (f"Stale Issues (>= {threshold} days)", "stale_issues"),
        (f"Stale Pull Requests (>= {threshold} days)", "stale_prs"),
        ("Draft Pull Requests", "draft_prs"),
        ("Review Bottlenecks", "review_bottlenecks"),
        ("CI Attention Required", "ci_attention"),
    ]

    for title, key in titles:
        output.append(text_section(title, sections[key]))

    return "\n\n".join(output)


def display_terminal_report(report):
    """Display a professional terminal summary."""

    summary = report["summary"]

    print()
    print(paint("=" * 58, Colors.CYAN))
    print(paint("             MAINTAINER TRIAGE REPORT", Colors.BOLD))
    print(paint("=" * 58, Colors.CYAN))

    print(f"\n Repository : {report['repository']}")
    print(f" Generated  : {report['generated_at']}")
    print(f" Threshold  : {report['stale_threshold_days']} days")

    print("\n" + "-" * 58)
    print(paint(" TRIAGE SUMMARY", Colors.BOLD))
    print("-" * 58)

    labels = [
        ("Issues missing labels", "issues_missing_labels"),
        ("Stale issues", "stale_issues"),
        ("Stale pull requests", "stale_pull_requests"),
        ("Draft pull requests", "draft_pull_requests"),
    ]

    for label, key in labels:
        count = summary[key]

        color = Colors.RED if count else Colors.GREEN

        print(f" {label:<30} {paint(str(count), color):>10}")

    print("-" * 58)
    print()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(
        prog="maint-triage-cli",
        description=(
            "Generate maintenance triage reports "
            "for GitHub repositories."
        ),
    )

    parser.add_argument(
        "--repo",
        required=True,
        help="GitHub repository in owner/name format.",
    )

    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Stale threshold in days (default: 30).",
    )

    parser.add_argument(
        "--format",
        choices=["markdown", "text", "json"],
        default="markdown",
        help="Report output format.",
    )

    args = parser.parse_args()

    if args.days < 0:
        parser.error("--days cannot be negative.")

    try:
        owner, name = validate_repo(args.repo)

        token = os.environ.get("GITHUB_TOKEN")

        if args.format != "json":
            print(
                paint(
                    f"\nAnalyzing {owner}/{name}...",
                    Colors.CYAN,
                )
            )

        now = datetime.now(timezone.utc)

        items = fetch_open_items(owner, name, token)
        rich_prs = fetch_open_pull_requests(owner, name, token)
        items = [item for item in items if "pull_request" not in item] + rich_prs

        categories = classify_items(
            items,
            args.days,
            now,
        )

        report = build_report(
            args.repo,
            categories,
            args.days,
            now,
        )

        if args.format == "markdown":
            display_terminal_report(report)

        print(render_report(report, args.format))

        return 0

    except TriageError as error:
        print(
            paint(f"\nError: {error}", Colors.RED),
            file=sys.stderr,
        )
        return 1

    except KeyboardInterrupt:
        print("\nOperation cancelled.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
