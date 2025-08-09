import os
import json
import argparse
import arxiv
import google.generativeai as genai
import openai
from datetime import datetime, timedelta, timezone

# --- 语言和模板配置 (Language & Template Configuration) ---

PROMPTS = {
    "en": {
        "system_message": "You are a helpful research assistant providing JSON output.",
        "template": """
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
    },
    "zh": {
        "system_message": "你是一个乐于助人的研究助理，需提供 JSON 格式的输出。",
        "template": """
你是一位专攻大型语言模型的高级AI研究员。
根据以下论文的标题和摘要，请完成以下任务：

**论文标题:** {title}
**论文摘要:** {abstract}

**任务:**
1.  **分类**: 将论文归入以下类别之一：
    [模型架构, 训练与优化, 数据与预训练, 微调与适配, 评测与基准, 多模态, 应用, 安全与伦理, 理论与分析, 其他]。
2.  **总结核心贡献**: 用一个简洁的句子总结论文的核心贡献。
3.  **评定新颖性**: 在1到5的范围内评价其潜在新颖性 (1=微创新, 3=有趣, 5=潜在突破)。

请以有效的JSON格式提供您的回答，例如：
{{"category": "...", "contribution": "...", "novelty": ...}}
"""
    }
}

REPORT_TEMPLATES = {
    "en": {
        "title": "# Daily arXiv LLM Digest - {report_date}",
        "summary_by": "Your daily summary of new papers on LLMs, analyzed by **{provider}**.",
        "top_recommendation": "## 🔥 Today's Top Recommendation",
        "authors": "- **Authors**: {authors}",
        "category": "- **Category**: `{category}`",
        "novelty_score": "- **Novelty Score**: `{novelty}/5`",
        "contribution": "- **Contribution**: {contribution}",
        "abstract": "**Abstract**: *{abstract}*",
        "other_papers": "---\n\n## 📚 Other Papers Today",
        "other_paper_category": "- **Category**: `{category}` | **Novelty**: `{novelty}/5`",
        "no_papers_found": "# Daily arXiv LLM Digest\n\nNo new papers found today."
    },
    "zh": {
        "title": "# arXiv LLM 每日摘要 - {report_date}",
        "summary_by": "您的 LLM 论文每日摘要，由 **{provider}** 分析。",
        "top_recommendation": "## 🔥 今日最佳推荐",
        "authors": "- **作者**: {authors}",
        "category": "- **类别**: `{category}`",
        "novelty_score": "- **新颖性评分**: `{novelty}/5`",
        "contribution": "- **核心贡献**: {contribution}",
        "abstract": "**摘要**: *{abstract}*",
        "other_papers": "---\n\n## 📚 今日其他论文",
        "other_paper_category": "- **类别**: `{category}` | **新颖性**: `{novelty}/5`",
        "no_papers_found": "# arXiv LLM 每日摘要\n\n今日未发现新论文.",
        "translation_template": "Translate the following English abstract into concise, academic Chinese:\n\n---\n\n{text}"
    }
}


# --- 核心功能 (Core Functions) ---

def fetch_recent_papers(search_query, max_results, days):
    """从 Arxiv 获取过去指定天数的论文"""
    print(f"Fetching recent papers from the last {days} day(s) from arXiv...")
    start_date_utc = datetime.now(timezone.utc) - timedelta(days=days)
    
    search = arxiv.Search(
        query=search_query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    recent_papers = []
    for result in search.results():
        if result.published > start_date_utc:
            recent_papers.append(result)
            
    print(f"Found {len(recent_papers)} new papers from the last {days} day(s).")
    return recent_papers

def _analyze_with_google(model, paper, lang):
    """使用 Google Gemini 分析论文"""
    prompt = PROMPTS[lang]["template"].format(title=paper.title, abstract=paper.summary)
    response = model.generate_content(prompt)
    cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
    return json.loads(cleaned_response)

def _analyze_with_openai_compatible(client, model_name, paper, lang):
    """使用 OpenAI 兼容的 API (OpenAI, DeepSeek) 分析论文"""
    prompt = PROMPTS[lang]["template"].format(title=paper.title, abstract=paper.summary)
    system_message = PROMPTS[lang]["system_message"]
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

def analyze_paper(provider, client, model_name, paper, lang):
    """根据提供商选择分析函数"""
    print(f"  Analyzing with {provider}: {paper.title[:60]}...")
    try:
        if provider == 'google':
            return _analyze_with_google(client, paper, lang)
        elif provider in ['openai', 'deepseek']:
            return _analyze_with_openai_compatible(client, model_name, paper, lang)
    except Exception as e:
        print(f"    [!] Error analyzing paper: {e}")
        return None

def _translate_text(text, provider, client, model_name):
    """使用 LLM 将文本翻译成中文"""
    print("  Translating top recommendation's abstract to Chinese...")
    prompt = REPORT_TEMPLATES["zh"]["translation_template"].format(text=text)
    try:
        if provider == 'google':
            response = client.generate_content(prompt)
            return response.text
        elif provider in ['openai', 'deepseek']:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful translation assistant, translating English to Chinese."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
    except Exception as e:
        print(f"    [!] Error translating text: {e}")
        return None

def generate_markdown_report(analyzed_papers, provider, lang, client, model_name):
    """生成 Markdown 格式的报告"""
    template = REPORT_TEMPLATES[lang]
    if not analyzed_papers:
        return template["no_papers_found"]

    analyzed_papers.sort(key=lambda x: x['analysis'].get('novelty', 0), reverse=True)
    
    recommendation = analyzed_papers[0]
    other_papers = analyzed_papers[1:]
    
    report_date = datetime.now().strftime("%Y-%m-%d")
    md_content = template["title"].format(report_date=report_date) + "\n\n"
    md_content += template["summary_by"].format(provider=provider) + "\n\n"
    
    md_content += template["top_recommendation"] + "\n\n"
    p = recommendation['paper']
    a = recommendation['analysis']
    md_content += f"### [{p.title}]({p.entry_id})\n"
    md_content += template["authors"].format(authors=', '.join(author.name for author in p.authors)) + "\n"
    md_content += template["category"].format(category=a.get('category', 'N/A')) + "\n"
    md_content += template["novelty_score"].format(novelty=a.get('novelty', 'N/A')) + "\n"
    md_content += template["contribution"].format(contribution=a.get('contribution', 'N/A')) + "\n\n"
    
    # 如果是中文报告，翻译最佳推荐的摘要
    abstract_to_display = p.summary.replace('\n', ' ')
    if lang == 'zh':
        translated_abstract = _translate_text(p.summary, provider, client, model_name)
        if translated_abstract:
            abstract_to_display = translated_abstract.replace('\n', ' ')

    md_content += template["abstract"].format(abstract=abstract_to_display) + "\n\n"
    
    if other_papers:
        md_content += template["other_papers"] + "\n\n"
        for item in other_papers:
            p = item['paper']
            a = item['analysis']
            md_content += f"### [{p.title}]({p.entry_id})\n"
            md_content += template["other_paper_category"].format(category=a.get('category', 'N/A'), novelty=a.get('novelty', 'N/A')) + "\n"
            md_content += template["contribution"].format(contribution=a.get('contribution', 'N/A')) + "\n\n"
            
    return md_content

def main():
    """主执行函数"""
    parser = argparse.ArgumentParser(description="Fetch and analyze recent LLM papers from arXiv.")
    parser.add_argument("--provider", type=str, default="deepseek", choices=["google", "openai", "deepseek"], help="The LLM provider to use.")
    parser.add_argument("--max-results", type=int, default=20, help="Maximum number of papers to process.")
    parser.add_argument("-d", "--days", type=int, default=2, help="Number of days back to search for papers.")
    parser.add_argument("--lang", type=str, default="zh", choices=["en", "zh"], help="Language for the output report (en/zh).")
    
    # API Keys - prioritize command-line args, then fall back to environment variables
    parser.add_argument("--google-api-key", type=str, default=os.getenv("GOOGLE_API_KEY"), help="Google API Key.")
    parser.add_argument("--openai-api-key", type=str, default=os.getenv("OPENAI_API_KEY"), help="OpenAI API Key.")
    parser.add_argument("--deepseek-api-key", type=str, default=os.getenv("DEEPSEEK_API_KEY"), help="DeepSeek API Key.")

    args = parser.parse_args()

    # --- 配置 (Configuration) ---
    # Computation and Language (cs.CL); Artificial Intelligence (cs.AI); Machine Learning (cs.LG)
    SEARCH_QUERY = 'cat:cs.CL OR cat:cs.AI OR cat:cs.LG'
    OUTPUT_DIR = "arxiv_digests_md"
    MODEL_CONFIG = {
        "google": "gemini-2.5-flash",
        "openai": "gpt-5",
        "deepseek": "deepseek-chat"
    }

    client = None
    model_name = MODEL_CONFIG[args.provider]

    print(f"Using LLM provider: {args.provider}")
    if args.provider == 'google':
        if not args.google_api_key:
            raise ValueError("Google API Key not provided. Set GOOGLE_API_KEY environment variable or use --google-api-key.")
        genai.configure(api_key=args.google_api_key)
        client = genai.GenerativeModel(model_name)
    
    elif args.provider == 'openai':
        if not args.openai_api_key:
            raise ValueError("OpenAI API Key not provided. Set OPENAI_API_KEY environment variable or use --openai-api-key.")
        client = openai.OpenAI(api_key=args.openai_api_key)

    elif args.provider == 'deepseek':
        if not args.deepseek_api_key:
            raise ValueError("DeepSeek API Key not provided. Set DEEPSEEK_API_KEY environment variable or use --deepseek-api-key.")
        client = openai.OpenAI(api_key=args.deepseek_api_key, base_url="https://api.deepseek.com/v1")

    else:
        raise ValueError(f"Unsupported LLM provider: {args.provider}")

    papers = fetch_recent_papers(SEARCH_QUERY, args.max_results, args.days)
    if not papers:
        print("No new papers to process. Exiting.")
        return

    analyzed_papers = []
    for paper in papers:
        analysis = analyze_paper(args.provider, client, model_name, paper, args.lang)
        if analysis:
            analyzed_papers.append({"paper": paper, "analysis": analysis})
    
    report = generate_markdown_report(analyzed_papers, args.provider, args.lang, client, model_name)

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    report_date = datetime.now().strftime("%Y-%m-%d")
    output_filename = os.path.join(OUTPUT_DIR, f"digest_{report_date}.md")

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"\n✅ Digest report generated successfully: {output_filename}")
    
    if analyzed_papers:
        print("\n--- Today's Recommendation ---")
        recommendation_part = report.split("---")[0]
        print(recommendation_part)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
