"""Integration tests for the CLI entry point."""
from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from test_sprint_lite import cli


class TestCLI:
    @patch("test_sprint_lite.run_suite")
    @patch("test_sprint_lite.load_suite")
    @patch("sys.argv", ["tsp", "run", "--file", "tests.yaml"])
    def test_run_exits_zero_on_all_pass(
        self, mock_load: Mock, mock_run: Mock,
    ):
        mock_load.return_value = {"name": "T", "tests": [{}]}
        mock_run.return_value = ([], 0, 0)
        cli()  # SystemExit NOT raised (no failures)

    @patch("test_sprint_lite.run_suite")
    @patch("test_sprint_lite.load_suite")
    @patch("sys.argv", ["tsp", "run", "--file", "tests.yaml"])
    def test_run_exits_nonzero_on_failure(
        self, mock_load: Mock, mock_run: Mock,
    ):
        mock_load.return_value = {"name": "T", "tests": [{}]}
        mock_run.return_value = ([], 0, 1)
        with pytest.raises(SystemExit, match="1"):
            cli()

    @patch("test_sprint_lite.run_suite")
    @patch("test_sprint_lite.load_suite")
    @patch("sys.argv", [
        "tsp", "run", "--file", "tests.yaml",
        "--workers", "4", "--html-report", "out.html"
    ])
    def test_html_report_flag_triggers_writer(
        self, mock_load: Mock, mock_run: Mock,
    ):
        mock_load.return_value = {"name": "T", "tests": [{}]}
        mock_run.return_value = ([], 0, 0)
        with patch("test_sprint_lite.write_html_report") as mock_html:
            cli()
            mock_html.assert_called_once()
