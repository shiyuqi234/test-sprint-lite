# Test Sprint Lite

[![CI](https://github.com/shiyuqi234/test-sprint-lite/actions/workflows/ci.yml/badge.svg)](https://github.com/shiyuqi234/test-sprint-lite/actions)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![Coverage](https://img.shields.io/badge/coverage-99%25-brightgreen)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

轻量 YAML 驱动的 HTTP API 自动化测试工具 | Lightweight YAML-driven HTTP API testing CLI

---

## ✨ Features / 功能

- **YAML 用例定义** — 用 YAML 编写 HTTP API 测试用例，零代码上手
- **多种断言** — 状态码 / JSON 字段（支持 `a.b.c` 点号路径）/ 文本包含
- **重试 & 超时** — 每个用例可独立配置超时时间和重试次数
- **并发执行** — 基于 `ThreadPoolExecutor` 的多线程并发
- **双格式报告** — Markdown 表格 + 内联 CSS 的 HTML 报告
- **CLI 工具** — `pip install` 后直接使用 `tsp run` 命令
- **完整测试覆盖** — 47 个 pytest 用例，99% 代码覆盖率
- **CI/CD 就绪** — GitHub Actions 自动 lint + 测试

---

## 🚀 Quick Start / 快速开始

### 1. Install / 安装

```bash
pip install git+https://github.com/shiyuqi234/test-sprint-lite.git
```

Or for development:

```bash
git clone https://github.com/shiyuqi234/test-sprint-lite.git
cd test-sprint-lite
pip install -e ".[dev]"
```

### 2. Write test cases / 编写用例

```yaml
# my_tests.yaml
name: Demo API Suite
base_url: https://jsonplaceholder.typicode.com

tests:
  - id: get_post_1
    name: Get Post #1
    method: GET
    path: /posts/1
    timeout: 5
    retry: 1
    expect:
      status_code: 200
      json:
        userId: 1
        id: 1
      text_contains: sunt

  - id: get_user_1
    name: Get User #1
    method: GET
    path: /users/1
    timeout: 5
    expect:
      status_code: 200
      json:
        id: 1
        username: Bret
```

### 3. Run / 运行

```bash
# Sequential
tsp run --file my_tests.yaml

# Concurrent (4 workers) with HTML report
tsp run --file my_tests.yaml --workers 4 --html-report report.html

# Custom report path
tsp run --file my_tests.yaml --report results.md
```

---

## 📋 CLI Options / 命令行参数

| Argument | Required | Default | Description |
|---|---|---|---|
| `--file` | ✅ | — | YAML test case file path |
| `--report` | ❌ | `report.md` | Markdown report output path |
| `--html-report` | ❌ | `""` | HTML report output path (optional) |
| `--workers` | ❌ | `1` | Number of concurrent threads |

---

## 🧪 YAML Test Case Format

Each test case supports the following fields:

| Field | Type | Default | Description |
|---|---|---|---|
| `id` | `str` | — | Unique test identifier |
| `name` | `str` | `id` | Human-readable test name |
| `method` | `str` | `GET` | HTTP method |
| `path` | `str` | `""` | Request path (appended to `base_url`) |
| `timeout` | `int` | `5` | Request timeout in seconds |
| `retry` | `int` | `0` | Retry count on connection failure |
| `headers` | `dict` | `{}` | HTTP headers |
| `params` | `dict` | `{}` | Query string parameters |
| `json` | `any` | `null` | JSON request body |
| `expect` | `dict` | `{}` | Assertions (see below) |

### Expect / 断言

```yaml
expect:
  status_code: 200           # Assert HTTP status code
  text_contains: "keyword"   # Assert response body contains text
  json:                      # Assert JSON fields (supports dotted keys)
    user.name: "Alice"
    data.items.0.id: 1
```

---

## 🛠 Development / 开发

### Run tests

```bash
pytest tests/ -v
```

### Run tests with coverage

```bash
pytest tests/ --cov=test_sprint_lite --cov-report=term
```

### Lint

```bash
ruff check test_sprint_lite.py tests/
```

---

## 📁 Project Structure / 项目结构

```
test-sprint-lite/
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Shared fixtures & mocks
│   ├── test_core.py               # deep_get, load_suite, CaseResult
│   ├── test_assert.py             # assert_case, request_with_retry
│   ├── test_runner.py             # run_case, run_suite, reports
│   └── test_cli.py                # CLI argument parsing
├── test_sprint_lite.py            # Main application (single module)
├── pyproject.toml                 # Package metadata & tool config
├── sample_tests.yaml              # Example test suite
├── requirements.txt               # Runtime dependencies
└── README.md
```

---

## 📊 Real-world Evaluation / 真实场景实测

在 [test-case-ai](https://github.com/shiyuqi234/test-case-ai) 的量化评测中，本工具作为执行端运行了 **93 个由 LLM 生成的用例**（3 个 OpenAPI spec、13 个接口），4 线程并发、输出 Markdown/HTML 双报告，全程稳定无崩溃。首次运行通过率 66.7%，其中行为确定的 httpbin 达 92.1%（数组路径断言 `a.b.0.c` 已支持）。

---

## 📝 Resume Bullet Points / 简历可写

- 独立设计并实现了一个 YAML 驱动的 API 自动化测试工具，支持 HTTP 接口测试的全流程：用例定义 → 执行 → 断言 → 报告
- 使用 `concurrent.futures.ThreadPoolExecutor` 实现多线程并发执行，支持用例级重试与超时配置
- 实现了 Markdown 和 HTML 双格式报告输出，HTML 报告包含内联 CSS 样式与 XSS 防护
- 使用 `pyproject.toml` 完成 CLI 工具打包，支持 `pip install` 与 `entry_points`
- 编写 47 个 pytest 单元测试用例，达到 99% 代码覆盖率，配置 GitHub Actions 实现 CI 自动化
- 使用 `unittest.mock` 完成网络请求的 mock 测试，覆盖正常路径、异常路径与重试逻辑

---

## 📄 License

MIT
