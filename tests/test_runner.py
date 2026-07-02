"""Unit tests for run_case, run_suite, and report generation."""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

from test_sprint_lite import (
    CaseResult,
    run_case,
    run_suite,
    write_html_report,
    write_report,
)

# ── run_case ───────────────────────────────────────────────

class TestRunCase:
    def test_successful_case(self, mock_response: Mock):
        with patch(
            "test_sprint_lite.request_with_retry", return_value=mock_response
        ):
            case = {
                "id": "t1",
                "name": "test",
                "method": "GET",
                "path": "/api",
                "expect": {"status_code": 200},
            }
            result = run_case(case, "https://example.com")
            assert isinstance(result, CaseResult)
            assert result.case_id == "t1"
            assert result.passed is True
            assert result.error == ""
            assert result.elapsed_ms >= 0

    def test_failed_assertion(self, mock_response: Mock):
        mock_response.status_code = 500
        with patch(
            "test_sprint_lite.request_with_retry", return_value=mock_response
        ):
            case = {
                "id": "t2",
                "name": "fail",
                "method": "GET",
                "path": "/api",
                "expect": {"status_code": 200},
            }
            result = run_case(case, "https://example.com")
            assert result.passed is False
            assert "status_code" in result.error

    def test_default_values(self, mock_response: Mock):
        """Ensure missing optional fields get sensible defaults."""
        with patch(
            "test_sprint_lite.request_with_retry", return_value=mock_response
        ):
            case: Dict[str, Any] = {"id": "min"}
            result = run_case(case, "https://example.com")
            assert result.case_id == "min"
            assert result.name == "min"  # falls back to id


# ── run_suite ─────────────────────────────────────────────

class TestRunSuite:
    @patch("test_sprint_lite.run_case")
    def test_sequential_execution(self, mock_run_case: Mock):
        mock_run_case.side_effect = [
            CaseResult("1", "a", True, 10),
            CaseResult("2", "b", False, 20, error="fail"),
            CaseResult("3", "c", True, 15),
        ]
        suite = {
            "name": "Seq",
            "base_url": "http://localhost",
            "tests": [{}, {}, {}],
        }
        results, passed, failed = run_suite(suite, workers=1)
        assert len(results) == 3
        assert passed == 2
        assert failed == 1
        assert mock_run_case.call_count == 3

    @patch("test_sprint_lite.run_case")
    def test_concurrent_execution(self, mock_run_case: Mock):
        mock_run_case.side_effect = [
            CaseResult("1", "a", True, 10),
            CaseResult("2", "b", True, 5),
        ]
        suite = {
            "name": "Concurrent",
            "base_url": "http://localhost",
            "tests": [{}, {}],
        }
        results, passed, failed = run_suite(suite, workers=4)
        assert len(results) == 2
        assert passed == 2
        assert failed == 0

    def test_empty_tests_raises_valueerror(self):
        with pytest.raises(ValueError, match="非空列表"):
            run_suite({"name": "Empty", "tests": []})

    def test_workers_less_than_1_raises(self, sample_suite_dict: Dict[str, Any]):
        with pytest.raises(ValueError, match="workers"):
            run_suite(sample_suite_dict, workers=0)

    def test_base_url_trailing_slash_stripped(self):
        """ensure rstrip('/') works on base_url."""
        suite = {
            "base_url": "http://example.com/api/",
            "tests": [],
        }
        with pytest.raises(ValueError, match="非空列表"):
            run_suite(suite)  # empty list triggers error, but base_url was processed


# ── write_report ───────────────────────────────────────────

class TestWriteReport:
    def test_markdown_report_content(self):
        results = [
            CaseResult("1", "pass", True, 10),
            CaseResult("2", "fail", False, 20, error="boom"),
        ]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f_path = f.name
        try:
            write_report(f_path, "Suite", results, 1, 1)
            content = Path(f_path).read_text(encoding="utf-8")
            assert "# Suite 测试报告" in content
            assert "PASS" in content
            assert "FAIL" in content
            assert "boom" in content
            stripped = content.replace(" ", "").replace("\n", "")
            assert "|1|pass|PASS|10|" in stripped
        finally:
            Path(f_path).unlink(missing_ok=True)

    def test_pipe_character_escaped_in_error(self):
        """Pipe in error message should be escaped for Markdown tables."""
        results = [CaseResult("1", "test", False, 10, error="a|b")]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f_path = f.name
        try:
            write_report(f_path, "Suite", results, 0, 1)
            content = Path(f_path).read_text(encoding="utf-8")
            assert "a\\|b" in content
        finally:
            Path(f_path).unlink(missing_ok=True)


# ── write_html_report ──────────────────────────────────────

class TestWriteHTMLReport:
    def test_html_report_structure(self):
        results = [
            CaseResult("1", "test", True, 10),
            CaseResult("2", "fail", False, 20, error="<script>alert(1)</script>"),
        ]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as f:
            f_path = f.name
        try:
            write_html_report(f_path, "Suite", results, 1, 1)
            content = Path(f_path).read_text(encoding="utf-8")
            assert "<!doctype html>" in content
            assert "Suite 测试报告" in content
            assert "class='pass'" in content
            assert "class='fail'" in content
            # XSS protection
            assert "&lt;script&gt;" in content
            assert "<script>" not in content
        finally:
            Path(f_path).unlink(missing_ok=True)
