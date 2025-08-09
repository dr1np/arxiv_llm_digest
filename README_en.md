# ArXiv LLM Paper Digest

This project automates the process of fetching, analyzing, and summarizing the latest research papers on Large Language Models (LLMs) from arXiv. It uses a Large Language Model (Google Gemini, OpenAI GPT, or DeepSeek) to categorize papers, summarize their contributions, and rate their novelty, delivering a concise daily digest in Markdown format in either English or Chinese.

## Features

- **Daily Paper Fetching**: Automatically searches arXiv for papers submitted in the last 48 hours based on a configurable query.
- **LLM-Powered Analysis**: For each paper, it uses an LLM to:
    - **Categorize** it into a predefined academic topic.
    - **Summarize** its core contribution in a single sentence.
    - **Rate** its potential novelty on a 1-5 scale.
- **Multi-Provider Support**: Easily switch between **Google Gemini**, **OpenAI GPT**, and **DeepSeek** models via a command-line flag.
- **Multi-Language Output**: Generate the digest report in either **English** or **Chinese**.
- **Daily Digest Report**: Generates a clean, readable dated Markdown file (e.g., `digest_2024-08-09.md`), highlighting a "Top Recommendation" for the day.

---

## Setup & Installation

### 1. Prerequisites

- Python 3.7+
- `git` (for cloning)

### 2. Clone the Repository

If you haven't already, clone the project to your local machine:

```bash
git clone <repository_url>
cd <repository_directory>
```

### 3. Install Dependencies

The required Python packages are listed in `requirements_arxiv.txt`. Install them using pip:

```bash
pip install -r requirements_arxiv.txt
```

### 4. Set Up API Keys

This script requires API keys for the LLM providers. You can provide them either via command-line arguments or by setting them as environment variables.

**How to get your API Keys:**

- **Google Gemini:**
    1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
    2. Sign in and click **"Create API key"** to generate your key.

- **OpenAI GPT:**
    1. Go to the [API keys page](https://platform.openai.com/api-keys) on the OpenAI Platform.
    2. Sign in and click **"Create new secret key"** to generate your key.

- **DeepSeek:**
    1. Go to the [DeepSeek Platform](https://platform.deepseek.com/) and sign in.
    2. Navigate to the **"API Keys"** section in your dashboard to create a key.

**How to set your API Keys:**

You can either pass the key directly with a command-line flag (e.g., `--openai-api-key "sk-..."`) or set it as an environment variable.

To set an environment variable (example for `zsh`):
```bash
echo "export OPENAI_API_KEY='YOUR_OPENAI_API_KEY'" >> ~/.zshrc
source ~/.zshrc
```
Replace `OPENAI_API_KEY` with `GOOGLE_API_KEY` or `DEEPSEEK_API_KEY` as needed.

---

## How to Use

### Easiest Way to Run

Simply execute the script without any arguments.

```bash
python arxiv_digest.py
```

By default, this command will automatically:
- **Use `deepseek`** as the language model.
- **Fetch new papers from the last `2` days**.
- **Generate the report in `Chinese` (`zh`)**.
- **Process a maximum of `20` papers**.

You just need to ensure your `DEEPSEEK_API_KEY` environment variable is set.

### Advanced Usage

For more control, you can use the following optional arguments:

- `--provider`: Choose the LLM provider (`google`, `openai`, `deepseek`).
  - **Default**: `deepseek`
- `--max-results`: Set the maximum number of papers to fetch.
  - **Default**: `20`
- `--days` or `-d`: Set the number of days back to search for new papers.
  - **Default**: `2`
- `--lang`: Set the output language (`en` for English, `zh` for Chinese).
  - **Default**: `zh`
- `--[provider]-api-key`: Provide the API key directly on the command line.

### Examples

**Generate an English digest for the last day's top 10 papers using Google Gemini:**
```bash
python3 arxiv_digest.py --provider google --lang en --days 1 --max-results 10
```
