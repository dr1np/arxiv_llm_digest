# ArXiv LLM Paper Digest

This project automates the process of fetching, analyzing, and summarizing the latest research papers on Large Language Models (LLMs) from arXiv. It uses a Large Language Model (either Google Gemini or OpenAI GPT) to categorize papers, summarize their contributions, and rate their novelty, delivering a concise daily digest in Markdown format.

## Features

- **Daily Paper Fetching**: Automatically searches arXiv for papers submitted in the last 24 hours based on configurable keywords (e.g., LLM, transformer, AI, etc.).
- **LLM-Powered Analysis**: For each paper, it uses an LLM to:
    - **Categorize** it into a predefined academic topic (e.g., Model Architecture, Fine-tuning, Ethics).
    - **Summarize** its core contribution in a single sentence.
    - **Rate** its potential novelty on a 1-5 scale.
- **Dual LLM Support**: Easily switch between **Google Gemini Pro** and **OpenAI GPT** models by changing a single variable.
- **Daily Digest Report**: Generates a clean, readable `daily_arxiv_digest.md` file, highlighting a "Top Recommendation" for the day.

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

This script requires API keys for the LLM providers. It's best practice to set these as environment variables.

**For Google Gemini:**
1.  Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
2.  Export the key as an environment variable:
    ```bash
    export GOOGLE_API_KEY='YOUR_GOOGLE_API_KEY'
    ```

**For OpenAI GPT:**
1.  Get your API key from your [OpenAI Dashboard](https://platform.openai.com/api-keys).
2.  Export the key as an environment variable:
    ```bash
    export OPENAI_API_KEY='YOUR_OPENAI_API_KEY'
    ```

**💡 Pro Tip:** To make these variables permanent, add the `export` commands to your shell's startup file (e.g., `~/.zshrc`, `~/.bash_profile`), then reload your shell with `source ~/.zshrc`.

---

## How to Use

### 1. Configure the Script

Open `arxiv_digest.py` and configure the settings at the top of the file:

- `LLM_PROVIDER`: Set to `"google"` or `"openai"` to choose your desired service.
- `SEARCH_QUERY`: Modify the arXiv search query to match your interests. The default is broad for LLM research.
- `MAX_RESULTS`: Adjust the maximum number of papers to process each day.

### 2. Run Manually

Execute the script from your terminal:

```bash
python arxiv_digest.py
```

The script will:
1.  Print its progress to the console.
2.  Create a new dated report (e.g., `digest_2024-08-08.md`) inside the `arxiv_digests/` directory.
3.  Print the "Today's Top Recommendation" to the console for a quick preview.