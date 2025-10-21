# ArXiv LLM 论文摘要

该项目自动从 arXiv 获取并分析近期与大型语言模型（LLM）相关的论文，生成每日 Markdown 摘要。

注意：此分支/版本已简化为只支持一个 LLM 提供商（DeepSeek），并统一使用 OpenAI 兼容的 API 调用方式。

## 主要特性

- 从 arXiv 根据可配置查询检索近期论文
- 使用 DeepSeek（OpenAI 兼容接口）对每篇论文做分类、贡献总结与新颖性评分
- 输出可选中文/英文报告，结果保存在 `arxiv_digests_md/` 目录下
- 配置集中在 `config.json`（或 `config.example.json`）中，可通过命令行参数覆盖

## 快速开始

1. 安装依赖：

```bash
pip install -r requirements_arxiv.txt
```

2. 配置 API Key（示例，bash）：

```bash
export ARXIV_DIGEST_API_KEY="xx-xxxx"
```

3. 使用默认配置运行：

```bash
python arxiv_digest.py
```

4. 指定配置文件或临时覆盖参数：

```bash
python arxiv_digest.py --config config.json --days 3 --max-results 30 --lang zh
python arxiv_digest.py --api-key "sk-..." --days 1
```

## 配置说明（`config.json`）

主要字段：

- `search_query`：arXiv 查询字符串，遵循 arXiv/Lucene 语法（示例：`(cat:cs.CL OR cat:cs.AI) AND (all:LLM)`）
- `model`：DeepSeek 模型名称（如 `deepseek-chat` 或 `deepseek-ai/DeepSeek-V3`）
- `api_base_url`：DeepSeek API 基础 URL（OpenAI 兼容）
- `max_results`：最大抓取论文数
- `days`：向后搜索的天数
- `prompts`、`report_templates`：LLM 提示与报告模板，已内嵌于配置文件

示例（`config.example.json` 已包含默认示例）：

```json
{
  "search_query": "(cat:cs.CL OR cat:cs.AI) AND (all:LLM)",
  "model": "deepseek-chat",
  "api_base_url": "https://api.deepseek.com/v1",
  "max_results": 20,
  "days": 2,
  "lang": "zh"
}
```

## 输出文件命名

生成的 Markdown 报告会保存在 `arxiv_digests_md/`，文件名格式为：

```
digest_{YYYY-MM-DD}_{keywords}.md
```

其中 `keywords` 来源于 `search_query`（会进行简单清理以便文件名安全）。

## 迁移说明（从多提供商到标准OpenAI API）

- 移除对 `google-generativeai` 的依赖
- 统一使用 `openai.OpenAI(api_key=..., base_url=...)` 调用 DeepSeek或其他API供应商的API
- 配置文件简化为单一 `model` 和 `api_base_url`

## 调试与验证

检查语法：

```bash
python -m py_compile arxiv_digest.py
```

验证配置文件为合法 JSON：

```bash
python -c "import json; json.load(open('config.json'))"
```

## 跟进建议

- 如果需要恢复多提供商支持，可将其抽象为一个提供商适配层
- 为 DeepSeek 添加更健壮的错误重试与速率限制处理

---

更多细节请查看 `config.example.json`。