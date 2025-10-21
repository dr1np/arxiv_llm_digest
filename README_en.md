# ArXiv LLM Paper Digest

This project automatically fetches and analyzes recent papers related to Large Language Models (LLMs) from arXiv, generating daily Markdown summaries.

Note: This branch/version has been simplified to support only one LLM provider (DeepSeek) and uses OpenAI-compatible API calls uniformly.

## Key Features

- Retrieves recent papers from arXiv based on configurable queries
- Uses DeepSeek (OpenAI-compatible interface) to classify each paper, summarize contributions, and score novelty
- Outputs reports in Chinese/English, with results saved in the `arxiv_digests_md/` directory
- Configuration centralized in `config.json` (or `config.example.json`), can be overridden via command-line parameters

## Quick Start

1. Install dependencies:

```bash
pip install -r requirements_arxiv.txt
```

2. Configure API Key (example, bash):

```bash
export DEEPSEEK_API_KEY="sk-..."
```

3. Run with default configuration:

```bash
python arxiv_digest.py
```

4. Specify configuration file or temporarily override parameters:

```bash
python arxiv_digest.py --config config.json --days 3 --max-results 30 --lang zh
python arxiv_digest.py --api-key "sk-..." --days 1
```

## Configuration Description (`config.json`)

Main fields:

- `search_query`: arXiv query string, follows arXiv/Lucene syntax (example: `(cat:cs.CL OR cat:cs.AI) AND (all:LLM)`)
- `model`: DeepSeek model name (e.g., `deepseek-chat` or `deepseek-ai/DeepSeek-V3`)
- `api_base_url`: DeepSeek API base URL (OpenAI compatible)
- `max_results`: Maximum number of papers to fetch
- `days`: Number of days to search back
- `prompts`, `report_templates`: LLM prompts and report templates, embedded in the configuration file

Example (`config.example.json` already includes a default example):

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

## Output File Naming

Generated Markdown reports are saved in `arxiv_digests_md/`, with filename format:

```
digest_{YYYY-MM-DD}_{keywords}.md
```

Where `keywords` are derived from `search_query` (lightly cleaned for filename safety).

## Migration Instructions (From Multi-Provider to Standard OpenAI API)

- Removed dependency on `google-generativeai`
- Unified use of `openai.OpenAI(api_key=..., base_url=...)` to call DeepSeek or other API providers
- Configuration simplified to single `model` and `api_base_url`

## Debugging and Verification

Check syntax:

```bash
python -m py_compile arxiv_digest.py
```

Verify configuration file is valid JSON:

```bash
python -c "import json; json.load(open('config.json'))"
```

## Follow-up Suggestions

- If multi-provider support needs restoration, abstract it into a provider adapter layer
- Add more robust error retry and rate limit handling for DeepSeek

---

For more details, please check  `config.example.json`.