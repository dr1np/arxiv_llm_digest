import os
import json
import arxiv
import google.generativeai as genai
import openai
from datetime import datetime, timedelta, timezone

# --- 配置 ---
# 1. LLM 提供商: 'google' 或 'openai'
LLM_PROVIDER = "google"  # <--- 在这里切换

# 2. API 密钥 (从环境变量读取)
#    运行: export GOOGLE_API_KEY='你的Google API密钥'
#    运行: export OPENAI_API_KEY='你的OpenAI API密钥'
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 3. Arxiv 搜索配置, Computation and Language (cs.CL); Artificial Intelligence (cs.AI); Machine Learning (cs.LG)
SEARCH_QUERY = 'cat:cs.CL OR cat:cs.AI OR cat:cs.LG'
MAX_RESULTS = 20  # 每天处理的最大论文数

# 4. LLM 分析配置
# 为不同提供商选择合适的模型
MODEL_CONFIG = {
    "google": "gemini-2.5-flash",
    "openai": "gpt-5-2025-08-07"
}

PROMPT_TEMPLATE = """
You are a senior AI researcher specializing in Large Language Models.
Based on the title and abstract of the following paper, please perform these tasks:

**Paper Title:** {title}
**Paper Abstract:** {abstract}

**Tasks:**
1.  **Categorize** the paper into ONE of the following categories: 
    [Model Architecture, Training & Optimization, Data & Pre-training, Fine-tuning & Adaptation, Evaluation & Benchmarking, Multimodality, Applications, Safety & Ethics, Theory & Analysis, Other].
2.  **Summarize the main contribution** in a single, concise sentence.
3.  **Rate its potential novelty** on a scale of 1 to 5 (1=Incremental, 3=Interesting, 5=Potential Breakthrough).

Provide your response in a valid JSON format, like this:
{{"category": "...", "contribution": "...", "novelty": ...}}
"""

# 5. 输出文件
OUTPUT_FILE = "daily_arxiv_digest.md"
OUTPUT_DIR = "arxiv_digests_md"

# --- 核心功能 ---

def fetch_recent_papers():
    """从 Arxiv 获取过去24小时的论文"""
    print("Fetching recent papers from arXiv...")
    # BUGFIX: 使用带时区的 UTC 时间进行比较
    yesterday_utc = datetime.now(timezone.utc) - timedelta(days=1)
    
    search = arxiv.Search(
        query=SEARCH_QUERY,
        max_results=MAX_RESULTS,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    recent_papers = []
    for result in search.results():
        if result.published > yesterday_utc:
            recent_papers.append(result)
            
    print(f"Found {len(recent_papers)} new papers from the last 24 hours.")
    return recent_papers

def _analyze_with_google(model, paper):
    """使用 Google Gemini 分析论文"""
    prompt = PROMPT_TEMPLATE.format(title=paper.title, abstract=paper.summary)
    response = model.generate_content(prompt)
    # 清理并解析 LLM 可能返回的 markdown 代码块
    cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
    return json.loads(cleaned_response)

def _analyze_with_openai(client, model_name, paper):
    """使用 OpenAI GPT 分析论文"""
    prompt = PROMPT_TEMPLATE.format(title=paper.title, abstract=paper.summary)
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are a helpful research assistant providing JSON output."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"} # 确保返回JSON
    )
    return json.loads(response.choices[0].message.content)

def analyze_paper(provider, client, model_name, paper):
    """根据提供商选择分析函数"""
    print(f"  Analyzing with {provider}: {paper.title[:60]}...")
    try:
        if provider == 'google':
            return _analyze_with_google(client, paper)
        elif provider == 'openai':
            return _analyze_with_openai(client, model_name, paper)
    except Exception as e:
        print(f"    [!] Error analyzing paper: {e}")
        return None

def generate_markdown_report(analyzed_papers):
    """生成 Markdown 格式的报告"""
    if not analyzed_papers:
        return "# Daily arXiv LLM Digest\n\nNo new papers found today."

    analyzed_papers.sort(key=lambda x: x['analysis'].get('novelty', 0), reverse=True)
    
    recommendation = analyzed_papers[0]
    other_papers = analyzed_papers[1:]
    
    report_date = datetime.now().strftime("%Y-%m-%d")
    md_content = f"# Daily arXiv LLM Digest - {report_date}\n\n"
    md_content += f"Your daily summary of new papers on LLMs, analyzed by **{LLM_PROVIDER}**.\n\n"
    
    md_content += "## 🔥 Today's Top Recommendation\n\n"
    p = recommendation['paper']
    a = recommendation['analysis']
    md_content += f"### [{p.title}]({p.entry_id})\n"
    md_content += f"- **Authors**: {', '.join(author.name for author in p.authors)}\n"
    md_content += f"- **Category**: `{a.get('category', 'N/A')}`\n"
    md_content += f"- **Novelty Score**: `{a.get('novelty', 'N/A')}/5`\n"
    md_content += f"- **Contribution**: {a.get('contribution', 'N/A')}\n\n"
    # BUGFIX: 使用 '\n' 替换换行符，而不是字母 'n'
    clean_summary = p.summary.replace('\n', ' ')
    md_content += f"**Abstract**: *{clean_summary}*\n\n"
    
    if other_papers:
        md_content += "---\n\n## 📚 Other Papers Today\n\n"
        for item in other_papers:
            p = item['paper']
            a = item['analysis']
            md_content += f"### [{p.title}]({p.entry_id})\n"
            md_content += f"- **Category**: `{a.get('category', 'N/A')}` | **Novelty**: `{a.get('novelty', 'N/A')}/5`\n"
            md_content += f"- **Contribution**: {a.get('contribution', 'N/A')}\n\n"
            
    return md_content

def main():
    """主执行函数"""
    client = None
    model_name = MODEL_CONFIG[LLM_PROVIDER]

    print(f"Using LLM provider: {LLM_PROVIDER}")
    if LLM_PROVIDER == 'google':
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable not set.")
        genai.configure(api_key=GOOGLE_API_KEY)
        client = genai.GenerativeModel(model_name)
    elif LLM_PROVIDER == 'openai':
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
    else:
        raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")

    papers = fetch_recent_papers()
    if not papers:
        print("No new papers to process. Exiting.")
        return

    analyzed_papers = []
    for paper in papers:
        analysis = analyze_paper(LLM_PROVIDER, client, model_name, paper)
        if analysis:
            analyzed_papers.append({"paper": paper, "analysis": analysis})
    
    report = generate_markdown_report(analyzed_papers)

    # 创建输出目录（如果不存在）
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # 生成带日期的文件名
    report_date = datetime.now().strftime("%Y-%m-%d")
    output_filename = os.path.join(OUTPUT_DIR, f"digest_{report_date}.md")

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"\n✅ Digest report generated successfully: {output_filename}")
    if analyzed_papers:
        print("\n--- Today's Recommendation ---")
        # 提取报告的推荐部分进行打印
        recommendation_part = report.split("## 📚 Other Papers Today")[0]
        print(recommendation_part)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")