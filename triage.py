#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

API = "https://api.github.com"

def gh_get(path, token=None):
    req = urllib.request.Request(API + path)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "maint-triage-cli")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        print(f"GitHub API error {e.code}: {e.read().decode()}", file=sys.stderr)
        raise

def days_since(iso):
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - dt).days

def item_line(i):
    return f"- [#{i['number']} {i['title']}]({i['html_url']}) — updated {days_since(i['updated_at'])}d ago"

def section(title, items):
    lines = [f"## {title} ({len(items)})", ""]
    if not items:
        lines.append("_None_")
    else:
        lines.extend(item_line(i) for i in items)
    lines.append("")
    return "\n".join(lines)

def main():
    p = argparse.ArgumentParser(description="Small maintainer triage report for a GitHub repo.")
    p.add_argument("--repo", required=True, help="owner/name")
    p.add_argument("--days", type=int, default=30, help="stale threshold in days")
    p.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"), help="optional GitHub token")
    p.add_argument("--format", choices=["markdown", "text"], default="markdown")
    args = p.parse_args()

    if "/" not in args.repo:
        sys.exit("--repo must be owner/name")

    items = gh_get(f"/repos/{args.repo}/issues?state=open&per_page=100", args.token)
    issues = [i for i in items if "pull_request" not in i]
    prs = [i for i in items if "pull_request" in i]

    no_labels = [i for i in issues if not i.get("labels")]
    stale_issues = [i for i in issues if days_since(i["updated_at"]) >= args.days]
    stale_prs = [i for i in prs if days_since(i["updated_at"]) >= args.days]
    drafts = [i for i in prs if i.get("draft")]

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = f"# Triage report: {args.repo}\n\nGenerated: {now}\n"

    if args.format == "markdown":
        out = "\n".join([
            header,
            section("Issues missing labels", no_labels),
            section(f"Issues stale >= {args.days} days", stale_issues),
            section(f"PRs stale >= {args.days} days", stale_prs),
            section("Draft PRs", drafts),
        ])
    else:
        def txt(title, xs):
            lines = [f"{title} ({len(xs)})"]
            lines += [f"  #{i['number']} {i['title']} — {i['html_url']}" for i in xs] or ["  None"]
            return "\n".join(lines)
        out = "\n\n".join([
            f"Triage report: {args.repo}\nGenerated: {now}",
            txt("Issues missing labels", no_labels),
            txt(f"Issues stale >= {args.days} days", stale_issues),
            txt(f"PRs stale >= {args.days} days", stale_prs),
            txt("Draft PRs", drafts),
        ])

    print(out)

if __name__ == "__main__":
    main()
