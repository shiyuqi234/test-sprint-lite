"""Shared pytest fixtures for Test Sprint Lite."""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, Mock

import pytest
import yaml


@pytest.fixture
def sample_suite_dict() -> Dict[str, Any]:
    """Return a minimal valid suite as a dict."""
    return {
        "name": "Test Suite",
        "base_url": "https://httpbin.org",
        "tests": [
            {
                "id": "test_1",
                "name": "Health Check",
                "method": "GET",
                "path": "/get",
                "timeout": 5,
                "retry": 1,
                "expect": {"status_code": 200},
            },
            {
                "id": "test_2",
                "name": "Create Item",
                "method": "POST",
                "path": "/post",
                "timeout": 10,
                "retry": 0,
                "headers": {"Content-Type": "application/json"},
                "json": {"name": "test"},
                "expect": {
                    "status_code": 201,
                    "json": {"json": {"name": "test"}},
                    "text_contains": "test",
                },
            },
        ],
    }


@pytest.fixture
def sample_yaml_file(sample_suite_dict: Dict[str, Any]) -> str:
    """Write sample suite to a temp YAML file, return the path."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(sample_suite_dict, f, allow_unicode=True)
        path = f.name
    yield path
    Path(path).unlink(missing_ok=True)


@pytest.fixture
def mock_response() -> Mock:
    """Return a mock requests.Response with default 200 OK."""
    resp = MagicMock()
    resp.status_code = 200
    resp.text = '{"id": 1, "name": "test"}'
    resp.json.return_value = {"id": 1, "name": "test"}
    return resp


@pytest.fixture
def mock_response_201() -> Mock:
    """Return a mock response with 201 Created."""
    resp = MagicMock()
    resp.status_code = 201
    resp.text = '{"created": true}'
    resp.json.return_value = {"created": True}
    return resp
