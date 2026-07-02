# Test Sprint Lite

一个面向测试入门同学的轻量测试工具，支持：
- YAML 编写接口测试用例
- 关键字段断言（状态码 / JSON 字段 / 文本包含）
- 重试与超时配置
- 并发执行（多线程）
- Markdown / HTML 测试报告输出

## 适合人群
- 大三/大四，想找测开实习
- 想从手工测试过渡到自动化测试

## 快速开始
1. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```
2. 运行示例
   ```bash
   python test_sprint_lite.py run --file sample_tests.yaml --report report.md --html-report report.html --workers 4
   ```

## 用例格式（YAML）
```yaml
name: Demo API Suite
base_url: https://jsonplaceholder.typicode.com

tests:
  - id: get_post_1
    name: 获取文章 1
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
```

## 参数说明
- `--file`：测试用例 YAML 文件
- `--report`：Markdown 报告路径，默认 `report.md`
- `--html-report`：HTML 报告路径（可选）
- `--workers`：并发线程数，默认 `1`

## 简历可写点
- 独立实现了一个 YAML 驱动的 API 自动化测试工具
- 支持断言、重试、超时、并发执行、报告生成
- 通过命令行参数控制执行与输出，具备基础工程化能力
