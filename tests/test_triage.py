
import json
import unittest

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


if __name__ == "__main__":
    unittest.main()
