"""Unit tests for core functions: deep_get, load_suite, CaseResult."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from test_sprint_lite import CaseResult, deep_get, load_suite

# ── deep_get ────────────────────────────────────────────────

class TestDeepGet:
    def test_simple_key(self):
        assert deep_get({"a": 1}, "a") == 1

    def test_nested_dotted_key(self):
        data = {"user": {"profile": {"name": "Alice"}}}
        assert deep_get(data, "user.profile.name") == "Alice"

    def test_deeply_nested(self):
        data = {"a": {"b": {"c": {"d": 42}}}}
        assert deep_get(data, "a.b.c.d") == 42

    def test_key_not_found_raises_keyerror(self):
        with pytest.raises(KeyError, match="JSON 路径不存在"):
            deep_get({"a": 1}, "b")

    def test_dotted_key_missing_intermediate_raises_keyerror(self):
        with pytest.raises(KeyError, match="JSON 路径不存在"):
            deep_get({"a": {"b": 1}}, "a.c.d")

    def test_list_value(self):
        data = {"items": [1, 2, 3]}
        assert deep_get(data, "items") == [1, 2, 3]

    def test_null_value(self):
        assert deep_get({"x": None}, "x") is None


# ── load_suite ─────────────────────────────────────────────

class TestLoadSuite:
    def test_valid_yaml(self, sample_yaml_file: str):
        suite = load_suite(sample_yaml_file)
        assert suite["name"] == "Test Suite"
        assert len(suite["tests"]) == 2

    def test_missing_tests_field_raises_valueerror(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.dump({"name": "No Tests"}, f)
            f_path = f.name
        try:
            with pytest.raises(ValueError, match="tests"):
                load_suite(f_path)
        finally:
            Path(f_path).unlink(missing_ok=True)

    def test_nonexistent_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_suite("/nonexistent/path.yaml")

    def test_empty_tests_list_is_valid(self):
        """Empty list is technically valid — runtime validation is elsewhere."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.dump({"name": "Empty", "tests": []}, f)
            f_path = f.name
        try:
            suite = load_suite(f_path)
            assert suite["tests"] == []
        finally:
            Path(f_path).unlink(missing_ok=True)


# ── CaseResult ─────────────────────────────────────────────

class TestCaseResult:
    def test_defaults(self):
        r = CaseResult(case_id="1", name="test", passed=True, elapsed_ms=42)
        assert r.error == ""

    def test_with_error(self):
        r = CaseResult(
            case_id="2", name="fail", passed=False, elapsed_ms=100,
            error="status_code 断言失败"
        )
        assert "断言" in r.error
