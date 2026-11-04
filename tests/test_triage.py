
import json
import unittest
from contextlib import redirect_stdout
from io import StringIO

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from triage import (
    TriageError,
    validate_repo,
    days_since,
    classify_items,
    build_report,
    render_report,
    fetch_open_items,
    fetch_ci_state,
    display_terminal_report,
    main,
)


class TestRepositoryValidation(unittest.TestCase):

    def test_valid_repository(self):
        self.assertEqual(
            validate_repo("psf/requests"),
            ("psf", "requests"),
        )

    def test_invalid_repository(self):
        with self.assertRaises(TriageError):
            validate_repo("invalid-repository")

    def test_empty_owner(self):
        with self.assertRaises(TriageError):
            validate_repo("/requests")

    def test_empty_repository(self):
        with self.assertRaises(TriageError):
            validate_repo("psf/")

    def test_multiple_slashes(self):
        with self.assertRaises(TriageError):
            validate_repo("psf/requests/extra")


class TestDateCalculations(unittest.TestCase):

    def setUp(self):
        self.now = datetime(
            2026, 11, 2, 12, 0,
            tzinfo=timezone.utc,
        )

    def test_days_since(self):
        updated = (
            self.now - timedelta(days=40)
        ).isoformat()

        self.assertEqual(
            days_since(updated, self.now),
            40,
        )

    def test_future_date(self):
        future = (
            self.now + timedelta(days=5)
        ).isoformat()

        self.assertEqual(
            days_since(future, self.now),
            0,
        )

    def test_invalid_timestamp(self):
        with self.assertRaises(TriageError):
            days_since("invalid-date", self.now)


class TestIssueClassification(unittest.TestCase):

    def setUp(self):
        self.now = datetime(
            2026, 11, 2, 12, 0,
            tzinfo=timezone.utc,
        )

    def make_item(
        self,
        number,
        title,
        days_old,
        labels=None,
        is_pr=False,
        draft=False,
    ):
        updated = (
            self.now - timedelta(days=days_old)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        item = {
            "number": number,
            "title": title,
            "html_url": (
                f"https://github.com/example/project/issues/{number}"
            ),
            "updated_at": updated,
            "labels": labels or [],
        }

        if is_pr:
            item["pull_request"] = {
                "url": "https://api.github.com/pulls/1"
            }
            item["draft"] = draft

        return item

    def test_missing_labels(self):
        items = [
            self.make_item(1, "Bug", 5),
            self.make_item(
                2,
                "Feature",
                5,
                labels=[{"name": "enhancement"}],
            ),
        ]

        result = classify_items(items, 30, self.now)

        self.assertEqual(
            len(result["missing_labels"]),
            1,
        )

        self.assertEqual(
            result["missing_labels"][0]["number"],
            1,
        )

    def test_stale_issues(self):
        items = [
            self.make_item(1, "Old issue", 45),
            self.make_item(2, "Recent issue", 5),
        ]

        result = classify_items(items, 30, self.now)

        self.assertEqual(
            len(result["stale_issues"]),
            1,
        )

        self.assertEqual(
            result["stale_issues"][0]["number"],
            1,
        )

    def test_stale_pull_requests(self):
        items = [
            self.make_item(
                1, "Old PR", 60, is_pr=True
            ),
            self.make_item(
                2, "Recent PR", 5, is_pr=True
            ),
        ]

        result = classify_items(items, 30, self.now)

        self.assertEqual(len(result["stale_prs"]), 1)

    def test_draft_pull_requests(self):
        items = [
            self.make_item(
                1, "Draft PR", 5,
                is_pr=True,
                draft=True,
            ),
            self.make_item(
                2, "Ready PR", 5,
                is_pr=True,
                draft=False,
            ),
        ]

        result = classify_items(items, 30, self.now)

        self.assertEqual(len(result["draft_prs"]), 1)


class TestReportGeneration(unittest.TestCase):

    def setUp(self):
        self.now = datetime(
            2026, 11, 2, 12, 0,
            tzinfo=timezone.utc,
        )

        self.report = build_report(
            "psf/requests",
            {
                "missing_labels": [],
                "stale_issues": [],
                "stale_prs": [],
                "draft_prs": [],
            },
            30,
            self.now,
        )

    def test_report_repository(self):
        self.assertEqual(
            self.report["repository"],
            "psf/requests",
        )

    def test_report_threshold(self):
        self.assertEqual(
            self.report["stale_threshold_days"],
            30,
        )

    def test_json_output(self):
        output = render_report(self.report, "json")
        parsed = json.loads(output)

        self.assertEqual(
            parsed["repository"],
            "psf/requests",
        )

    def test_markdown_output(self):
        output = render_report(self.report, "markdown")

        self.assertIn(
            "# Triage Report: psf/requests",
            output,
        )

        self.assertIn("Missing Labels", output)

    def test_text_output(self):
        output = render_report(self.report, "text")

        self.assertIn(
            "TRIAGE REPORT: psf/requests",
            output,
        )


class TestPagination(unittest.TestCase):

    @patch("triage.github_get")
    def test_multiple_pages(self, mock_get):

        first_page = [
            {"number": 1},
            {"number": 2},
        ]

        second_page = [
            {"number": 3},
        ]

        next_url = (
            "https://api.github.com/repos/psf/requests/"
            "issues?state=open&per_page=100&page=2"
        )

        mock_get.side_effect = [
            (
                first_page,
                f'<{next_url}>; rel="next"',
            ),
            (
                second_page,
                "",
            ),
        ]

        result = fetch_open_items(
            "psf",
            "requests",
        )

        self.assertEqual(len(result), 3)
        self.assertEqual(
            [item["number"] for item in result],
            [1, 2, 3],
        )

        self.assertEqual(mock_get.call_count, 2)




class TestReviewAndCiIntelligence(unittest.TestCase):

    def setUp(self):
        self.now = datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc)

    def test_requested_reviewers_are_flagged(self):
        item = {
            "number": 10,
            "title": "Needs review",
            "html_url": "https://github.com/example/project/pull/10",
            "updated_at": "2026-11-01T12:00:00Z",
            "labels": [],
            "pull_request": {"url": "https://api.github.com/pulls/10"},
            "requested_reviewers": [{"login": "reviewer"}],
            "draft": False,
            "ci_state": "success",
        }
        result = classify_items([item], 30, self.now)
        self.assertEqual(len(result["review_bottlenecks"]), 1)

    def test_failed_ci_is_flagged(self):
        item = {
            "number": 11,
            "title": "CI failing",
            "html_url": "https://github.com/example/project/pull/11",
            "updated_at": "2026-11-01T12:00:00Z",
            "labels": [],
            "pull_request": {"url": "https://api.github.com/pulls/11"},
            "requested_reviewers": [],
            "draft": False,
            "ci_state": "failure",
        }
        result = classify_items([item], 30, self.now)
        self.assertEqual(len(result["ci_attention"]), 1)


    @patch("triage.github_get")
    def test_check_run_failure_is_detected(self, mock_get):
        mock_get.return_value = ({
            "check_runs": [{"status": "completed", "conclusion": "failure"}]
        }, "")
        self.assertEqual(fetch_ci_state("psf", "requests", "abc123"), "failure")
        self.assertEqual(mock_get.call_count, 1)

    @patch("triage.github_get")
    def test_check_run_in_progress_is_pending(self, mock_get):
        mock_get.return_value = ({
            "check_runs": [{"status": "in_progress", "conclusion": None}]
        }, "")
        self.assertEqual(fetch_ci_state("psf", "requests", "abc123"), "pending")
        self.assertEqual(mock_get.call_count, 1)

    @patch("triage.github_get")
    def test_empty_check_runs_fall_back_to_commit_status(self, mock_get):
        mock_get.side_effect = [
            ({"check_runs": []}, ""),
            ({"state": "success"}, ""),
        ]
        self.assertEqual(fetch_ci_state("psf", "requests", "abc123"), "success")
        self.assertEqual(mock_get.call_count, 2)


    @patch("triage.sys.argv", ["triage.py", "--repo", "psf/requests", "--format", "markdown"])
    @patch("triage.fetch_open_items", return_value=[])
    @patch("triage.fetch_open_pull_requests", return_value=[])
    def test_markdown_cli_stdout_contains_only_markdown(self, _pulls, _items):
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(), 0)
        self.assertTrue(output.getvalue().startswith("# Triage Report: psf/requests"))

    def test_report_contains_new_intelligence_counts(self):
        categories = {
            "missing_labels": [],
            "stale_issues": [],
            "stale_prs": [],
            "draft_prs": [],
            "review_bottlenecks": [],
            "ci_attention": [],
        }
        report = build_report("example/project", categories, 30, self.now)
        self.assertEqual(report["summary"]["review_bottlenecks"], 0)
        self.assertEqual(report["summary"]["ci_attention"], 0)


class TestTerminalSummary(unittest.TestCase):
    def test_displays_review_and_ci_attention_counts(self):
        now = datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc)
        categories = {
            "missing_labels": [],
            "stale_issues": [],
            "stale_prs": [],
            "draft_prs": [],
            "review_bottlenecks": [{"number": 1, "title": "Review", "html_url": "https://github.com/example/project/pull/1", "updated_at": now.isoformat(), "labels": []}],
            "ci_attention": [{"number": 2, "title": "CI", "html_url": "https://github.com/example/project/pull/2", "updated_at": now.isoformat(), "labels": []}],
        }
        report = build_report("example/project", categories, 30, now)
        output = StringIO()
        with redirect_stdout(output):
            display_terminal_report(report)
        rendered = output.getvalue()
        self.assertIn("Review bottlenecks", rendered)
        self.assertIn("CI attention", rendered)


if __name__ == "__main__":
    unittest.main()
