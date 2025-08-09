# ArXiv LLM 论文摘要

本项目可自动从 arXiv 上获取、分析并总结大型语言模型（LLM）领域的最新研究论文。它利用大型语言模型（Google Gemini、OpenAI GPT 或 DeepSeek）对论文进行分类、总结其贡献、评估其新颖性，并以 Markdown 格式生成简洁的每日摘要（支持中文或英文）。

## 功能特性

- **每日论文获取**：根据可配置的查询条件，自动搜索 arXiv 上过去48小时内提交的论文。
- **LLM 驱动的分析**：对每篇论文，使用 LLM 完成以下任务：
    - **分类**：将其归入预定义的学术主题。
    - **总结**：用一句话概括其核心贡献。
    - **评估**：在 1-5 的范围内为其潜在新颖性打分。
- **多模型支持**：通过命令行标志，轻松在 **Google Gemini**、**OpenAI GPT** 和 **DeepSeek** 模型间切换。
- **多语言输出**：可生成 **英文** 或 **中文** 的摘要报告。
- **每日摘要报告**：生成一个整洁、可读的带日期 Markdown 文件（例如 `digest_2024-08-09.md`），并高亮当天的“最佳推荐”。

---

## 安装与设置

### 1. 环境要求

- Python 3.7+
- `git` (用于克隆仓库)

### 2. 克隆仓库

如果尚未克隆，请将项目克隆到本地：

```bash
git clone <repository_url>
cd <repository_directory>
```

### 3. 安装依赖

所需的 Python 包已在 `requirements_arxiv.txt` 中列出。使用 pip 安装它们：

```bash
pip install -r requirements_arxiv.txt
```

### 4. 设置 API 密钥

该脚本需要 LLM 提供商的 API 密钥。您可以通过命令行参数提供，或将其设置为环境变量。

**如何获取您的 API 密钥：**

- **Google Gemini:**
    1. 前往 [Google AI Studio](https://aistudio.google.com/app/apikey)。
    2. 登录后点击 **"Create API key"** 来生成您的密钥。

- **OpenAI GPT:**
    1. 前往 OpenAI 平台的 [API 密钥页面](https://platform.openai.com/api-keys)。
    2. 登录后点击 **"Create new secret key"** 来生成您的密钥。

- **DeepSeek:**
    1. 前往 [DeepSeek Platform](https://platform.deepseek.com/) 并登录。
    2. 在您的用户面板中找到 **"API Keys"** 部分来创建密钥。

**如何设置您的 API 密钥：**

您可以直接通过命令行标志传递密钥（例如 `--openai-api-key "sk-..."`），或者将其设置为环境变量。

设置环境变量的示例 (以 `zsh` 为例):
```bash
echo "export OPENAI_API_KEY='你的_OPENAI_API_KEY'" >> ~/.zshrc
source ~/.zshrc
```
根据需要，将 `OPENAI_API_KEY` 替换为 `GOOGLE_API_KEY` 或 `DEEPSEEK_API_KEY`。

---

## 如何使用

### 最简用法

直接运行脚本即可，无需任何参数。

```bash
python arxiv_digest.py
```

默认情况下，该命令会自动执行以下操作：
- **使用 `deepseek`** 作为语言模型。
- **获取过去 `2` 天** 的新论文。
- **生成 `中文`** 摘要报告。
- **处理最多 `20` 篇** 论文。

您只需要确保已经设置了 `DEEPSEEK_API_KEY` 环境变量。

### 高级用法

如果您想自定义，可以使用以下可选参数：

- `--provider`: 选择 LLM 提供商 (`google`, `openai`, `deepseek`)。
  - **默认值**: `deepseek`
- `--max-results`: 设置要获取的最大论文数。
  - **默认值**: `20`
- `--days` 或 `-d`: 设置回顾搜索新论文的天数。
  - **默认值**: `2`
- `--lang`: 设置输出语言 (`en` 代表英文, `zh` 代表中文)。
  - **默认值**: `zh`
- `--[provider]-api-key`: 直接在命令行提供 API 密钥。

### 示例

**使用 Google Gemini 生成过去一天内10篇论文的英文摘要：**
```bash
python3 arxiv_digest.py --provider google --lang en --days 1 --max-results 10
```

---
## 高级配置

### 自定义模型

您可以轻松更改脚本使用的默认模型。

1.  打开 `arxiv_digest.py` 文件。
2.  找到名为 `MODEL_CONFIG` 的字典。

    ```python
    MODEL_CONFIG = {
        "google": "gemini-2.5-flash",
        "openai": "gpt-5",
        "deepseek": "deepseek-chat"
    }
    ```
3.  将引号内的模型名称修改为您想使用的任何兼容模型。例如，如果您想使用 OpenAI 的 `gpt-4o` 模型，只需修改：

    ```python
    MODEL_CONFIG = {
        "google": "gemini-2.5-flash",
        "openai": "gpt-4o",  # <-- 修改这里
        "deepseek": "deepseek-chat"
    }
    ```
4.  保存文件即可。下次当您通过 `--provider openai` 运行时，脚本将使用您指定的新模型。
