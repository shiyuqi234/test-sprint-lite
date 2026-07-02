"""Unit tests for assert_case and request_with_retry."""
from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from test_sprint_lite import assert_case, request_with_retry

# ── assert_case ────────────────────────────────────────────

class TestAssertCase:
    def test_status_code_pass(self, mock_response: Mock):
        mock_response.status_code = 200
        assert_case(mock_response, {"status_code": 200})  # no exception

    def test_status_code_fail_raises(self, mock_response: Mock):
        mock_response.status_code = 500
        with pytest.raises(AssertionError, match="status_code"):
            assert_case(mock_response, {"status_code": 200})

    def test_text_contains_pass(self, mock_response: Mock):
        mock_response.text = "hello world"
        assert_case(mock_response, {"text_contains": "world"})

    def test_text_contains_fail_raises(self, mock_response: Mock):
        mock_response.text = "hello world"
        with pytest.raises(AssertionError, match="text_contains"):
            assert_case(mock_response, {"text_contains": "missing"})

    def test_json_assertion_pass(self, mock_response: Mock):
        mock_response.json.return_value = {"id": 1, "name": "test"}
        assert_case(mock_response, {"json": {"id": 1, "name": "test"}})

    def test_json_assertion_fail_raises(self, mock_response: Mock):
        mock_response.json.return_value = {"id": 999}
        with pytest.raises(AssertionError, match="json 断言失败"):
            assert_case(mock_response, {"json": {"id": 1}})

    def test_json_dotted_key_pass(self, mock_response: Mock):
        mock_response.json.return_value = {
            "user": {"profile": {"name": "Alice"}}
        }
        assert_case(
            mock_response,
            {"json": {"user.profile.name": "Alice"}},
        )

    def test_json_dotted_key_fail_raises(self, mock_response: Mock):
        mock_response.json.return_value = {"user": {"name": "Bob"}}
        with pytest.raises(KeyError, match="JSON 路径不存在"):
            assert_case(mock_response, {"json": {"user.profile.name": "Bob"}})

    def test_non_json_response_raises(self, mock_response: Mock):
        import json
        mock_response.json.side_effect = json.JSONDecodeError("not json", doc="", pos=0)
        with pytest.raises(AssertionError, match="不是合法 JSON"):
            assert_case(mock_response, {"json": {"key": "value"}})

    def test_expect_is_empty_dict(self, mock_response: Mock):
        """Empty expect dict should pass (no assertions to check)."""
        assert_case(mock_response, {})  # no exception

    def test_multiple_assertions_all_pass(self, mock_response: Mock):
        mock_response.status_code = 200
        mock_response.text = "hello world"
        mock_response.json.return_value = {"key": "value"}
        assert_case(
            mock_response,
            {
                "status_code": 200,
                "text_contains": "hello",
                "json": {"key": "value"},
            },
        )

    def test_first_assertion_fails_blocks_rest(self, mock_response: Mock):
        """status_code fails → text_contains never checked."""
        mock_response.status_code = 500
        with pytest.raises(AssertionError, match="status_code"):
            assert_case(mock_response, {"status_code": 200, "text_contains": "x"})


# ── request_with_retry ─────────────────────────────────────

class TestRequestWithRetry:
    @patch("test_sprint_lite.requests.request")
    def test_first_attempt_succeeds(self, mock_request: Mock):
        mock_request.return_value = MagicMock(status_code=200)
        resp = request_with_retry(
            method="GET", url="http://example.com",
            headers={}, params={}, body=None, timeout=5, retry=2,
        )
        assert mock_request.call_count == 1
        assert resp.status_code == 200

    @patch("test_sprint_lite.requests.request")
    def test_retry_on_failure_then_succeed(self, mock_request: Mock):
        mock_request.side_effect = [
            requests.ConnectionError("timeout"),
            requests.ConnectionError("timeout"),
            MagicMock(status_code=200),
        ]
        resp = request_with_retry(
            method="GET", url="http://example.com",
            headers={}, params={}, body=None, timeout=5, retry=2,
        )
        assert mock_request.call_count == 3
        assert resp.status_code == 200

    @patch("test_sprint_lite.requests.request")
    def test_all_attempts_fail_raises(self, mock_request: Mock):
        exc = requests.ConnectionError("timeout")
        mock_request.side_effect = exc
        with pytest.raises(requests.ConnectionError):
            request_with_retry(
                method="GET", url="http://example.com",
                headers={}, params={}, body=None, timeout=5, retry=2,
            )
        assert mock_request.call_count == 3  # 1 + 2 retries

    @patch("test_sprint_lite.requests.request")
    def test_retry_zero_means_no_retry(self, mock_request: Mock):
        exc = requests.ConnectionError("timeout")
        mock_request.side_effect = exc
        with pytest.raises(requests.ConnectionError):
            request_with_retry(
                method="GET", url="http://example.com",
                headers={}, params={}, body=None, timeout=5, retry=0,
            )
        assert mock_request.call_count == 1

    @patch("test_sprint_lite.requests.request")
    @patch("test_sprint_lite.time.sleep")
    def test_sleep_between_retries(self, mock_sleep: Mock, mock_request: Mock):
        mock_request.side_effect = [
            requests.ConnectionError("e1"),
            requests.ConnectionError("e2"),
            MagicMock(status_code=200),
        ]
        request_with_retry(
            method="GET", url="http://example.com",
            headers={}, params={}, body=None, timeout=5, retry=3,
        )
        assert mock_sleep.call_count == 2  # slept before retry 1 and retry 2
