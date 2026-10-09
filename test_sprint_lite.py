import argparse
import html
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Tuple

import requests
import yaml


@dataclass
class CaseResult:
    case_id: str
    name: str
    passed: bool
    elapsed_ms: int
    error: str = ""


def load_suite(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or "tests" not in data:
        raise ValueError("YAML 格式错误：需要包含 tests 字段")
    return data


def deep_get(data: Dict[str, Any], dotted_key: str) -> Any:
    cur: Any = data
    for part in dotted_key.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            # 支持数组索引访问（如 data.items.0.id）
            cur = cur[int(part)]
        else:
            raise KeyError(f"JSON 路径不存在: {dotted_key}")
    return cur


def assert_case(resp: requests.Response, expect: Dict[str, Any]) -> None:
    if "status_code" in expect and resp.status_code != expect["status_code"]:
        raise AssertionError(
            f"status_code 断言失败: actual={resp.status_code}, expect={expect['status_code']}"
        )

    if "text_contains" in expect:
        keyword = str(expect["text_contains"])
        if keyword not in resp.text:
            raise AssertionError(f"text_contains 断言失败: 未找到 '{keyword}'")

    if "json" in expect:
        try:
            body = resp.json()
        except json.JSONDecodeError as e:
            raise AssertionError(f"响应不是合法 JSON: {e}") from e

        expected_json: Dict[str, Any] = expect["json"]
        for key, value in expected_json.items():
            actual = deep_get(body, key) if "." in key else body.get(key)
            if actual != value:
                raise AssertionError(
                    f"json 断言失败: key={key}, actual={actual}, expect={value}"
                )


def request_with_retry(
    method: str,
    url: str,
    headers: Dict[str, str],
    params: Dict[str, Any],
    body: Any,
    timeout: int,
    retry: int,
) -> requests.Response:
    last_error: Exception | None = None
    for i in range(retry + 1):
        try:
            return requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=body,
                timeout=timeout,
            )
        except requests.RequestException as e:
            last_error = e
            if i < retry:
                time.sleep(0.5)

    assert last_error is not None
    raise last_error


def run_case(case: Dict[str, Any], base_url: str) -> CaseResult:
    case_id = str(case.get("id", "unknown"))
    name = str(case.get("name", case_id))
    method = str(case.get("method", "GET")).upper()
    path = str(case.get("path", ""))
    url = f"{base_url}{path}"
    timeout = int(case.get("timeout", 5))
    retry = int(case.get("retry", 0))
    headers = case.get("headers", {}) or {}
    params = case.get("params", {}) or {}
    body = case.get("json", None)
    expect = case.get("expect", {}) or {}

    start = time.time()
    try:
        resp = request_with_retry(
            method=method,
            url=url,
            headers=headers,
            params=params,
            body=body,
            timeout=timeout,
            retry=retry,
        )
        assert_case(resp, expect)
        passed = True
        error = ""
    except Exception as e:  # noqa: BLE001
        passed = False
        error = str(e)

    elapsed_ms = int((time.time() - start) * 1000)
    return CaseResult(case_id=case_id, name=name, passed=passed, elapsed_ms=elapsed_ms, error=error)


def run_suite(suite: Dict[str, Any], workers: int = 1) -> Tuple[List[CaseResult], int, int]:
    base_url = suite.get("base_url", "").rstrip("/")
    tests: List[Dict[str, Any]] = suite["tests"]

    if not isinstance(tests, list) or not tests:
        raise ValueError("tests 必须是非空列表")
    if workers < 1:
        raise ValueError("workers 必须 >= 1")

    results: List[CaseResult] = [CaseResult("", "", False, 0, "") for _ in tests]

    if workers == 1:
        for idx, case in enumerate(tests):
            results[idx] = run_case(case, base_url)
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_map = {
                executor.submit(run_case, case, base_url): idx for idx, case in enumerate(tests)
            }
            for future in as_completed(future_map):
                idx = future_map[future]
                results[idx] = future.result()

    passed_count = sum(1 for r in results if r.passed)
    failed_count = len(results) - passed_count
    return results, passed_count, failed_count


def write_report(report_path: str, suite_name: str, results: List[CaseResult], passed: int, failed: int) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"# {suite_name} 测试报告",
        "",
        f"- 生成时间: {now}",
        f"- 总用例: {len(results)}",
        f"- 通过: {passed}",
        f"- 失败: {failed}",
        "",
        "| ID | Name | Result | Elapsed(ms) | Error |",
        "|---|---|---|---:|---|",
    ]

    for r in results:
        result_text = "PASS" if r.passed else "FAIL"
        error_text = r.error.replace("|", "\\|") if r.error else ""
        lines.append(f"| {r.case_id} | {r.name} | {result_text} | {r.elapsed_ms} | {error_text} |")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def write_html_report(report_path: str, suite_name: str, results: List[CaseResult], passed: int, failed: int) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(results)
    rows: List[str] = []
    for r in results:
        result_text = "PASS" if r.passed else "FAIL"
        css = "pass" if r.passed else "fail"
        rows.append(
            "<tr>"
            f"<td>{html.escape(r.case_id)}</td>"
            f"<td>{html.escape(r.name)}</td>"
            f"<td class='{css}'>{result_text}</td>"
            f"<td>{r.elapsed_ms}</td>"
            f"<td>{html.escape(r.error)}</td>"
            "</tr>"
        )

    doc = f"""<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{html.escape(suite_name)} - Test Report</title>
  <style>
    :root {{ --ok:#0f766e; --bad:#b91c1c; --bg:#f8fafc; --text:#0f172a; --card:#ffffff; }}
    body {{ margin: 0; font-family: \"Segoe UI\", sans-serif; background: var(--bg); color: var(--text); }}
    .wrap {{ max-width: 980px; margin: 24px auto; padding: 0 16px; }}
    .card {{ background: var(--card); border-radius: 12px; padding: 20px; box-shadow: 0 8px 20px rgba(15,23,42,.08); }}
    h1 {{ margin: 0 0 12px; font-size: 24px; }}
    .meta {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 12px; }}
    .pill {{ border-radius: 999px; padding: 6px 12px; background: #e2e8f0; font-size: 14px; }}
    .pass {{ color: var(--ok); font-weight: 600; }}
    .fail {{ color: var(--bad); font-weight: 600; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
    th, td {{ border-bottom: 1px solid #e2e8f0; text-align: left; padding: 10px 8px; vertical-align: top; }}
    th {{ background: #f1f5f9; }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <div class=\"card\">
      <h1>{html.escape(suite_name)} 测试报告</h1>
      <div class=\"meta\">
        <span class=\"pill\">生成时间: {now}</span>
        <span class=\"pill\">总用例: {total}</span>
        <span class=\"pill pass\">通过: {passed}</span>
        <span class=\"pill fail\">失败: {failed}</span>
      </div>
      <table>
        <thead>
          <tr><th>ID</th><th>Name</th><th>Result</th><th>Elapsed(ms)</th><th>Error</th></tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    </div>
  </div>
</body>
</html>
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(doc)


def cli() -> None:
    parser = argparse.ArgumentParser(description="Test Sprint Lite - 轻量 API 测试工具")
    sub = parser.add_subparsers(dest="command", required=True)

    run_cmd = sub.add_parser("run", help="执行测试")
    run_cmd.add_argument("--file", required=True, help="测试用例 YAML 文件")
    run_cmd.add_argument("--report", default="report.md", help="输出 Markdown 报告路径")
    run_cmd.add_argument("--html-report", default="", help="输出 HTML 报告路径（可选）")
    run_cmd.add_argument("--workers", type=int, default=1, help="并发线程数，默认 1")

    args = parser.parse_args()

    if args.command == "run":
        suite = load_suite(args.file)
        suite_name = str(suite.get("name", "Test Sprint Lite"))
        results, passed, failed = run_suite(suite, workers=args.workers)
        write_report(args.report, suite_name, results, passed, failed)
        if args.html_report:
            write_html_report(args.html_report, suite_name, results, passed, failed)

        print(f"[DONE] Total={len(results)} Passed={passed} Failed={failed}")
        print(f"[REPORT] {args.report}")
        if args.html_report:
            print(f"[HTML REPORT] {args.html_report}")

        if failed > 0:
            raise SystemExit(1)


if __name__ == "__main__":
    cli()
