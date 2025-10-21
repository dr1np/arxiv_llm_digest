import os
import json
import argparse
import re
import arxiv
import openai
from datetime import datetime, timedelta, timezone


# --- 配置加载函数 (Configuration Loading) ---

def load_config(config_file="config.json"):
    """加载配置文件"""
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        print(f"✓ Configuration loaded from {config_file}")
        return config
    except FileNotFoundError:
        print(f"⚠ Configuration file {config_file} not found. Using command-line arguments only.")
        return {}
    except json.JSONDecodeError as e:
        print(f"✗ Error parsing configuration file: {e}")
        return {}

def extract_keywords_from_query(search_query):
    """从搜索查询中提取关键词用于文件名"""
    # 替换逻辑操作符为下划线
    cleaned = search_query.replace(" AND ", "_").replace(" OR ", "_").replace(" NOT ", "_")
    
    # 移除括号
    cleaned = cleaned.replace("(", "").replace(")", "")
    
    # 移除 arXiv 分类前缀和冒号
    cleaned = re.sub(r'cat:\s*[a-zA-Z.]+', '', cleaned)
    cleaned = re.sub(r'(all|ti|abs|au):', '', cleaned)
    
    # 移除双引号
    cleaned = cleaned.replace('"', '')
    
    # 移除多余空格
    cleaned = re.sub(r'\s+', '_', cleaned.strip())
    
    # 移除多余下划线
    cleaned = re.sub(r'_+', '_', cleaned)
    
    # 移除首尾下划线
    cleaned = cleaned.strip('_')
    
    # 如果为空或太长，返回默认值
    if not cleaned:
        cleaned = "arxiv"
    elif len(cleaned) > 50:
        cleaned = cleaned[:50].rstrip('_')
    
    return cleaned


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

def _analyze_with_llm(client, model_name, paper, lang, prompts):
    """使用 OpenAI 规范的 API 分析论文"""
    prompt = prompts[lang]["template"].format(title=paper.title, abstract=paper.summary)
    system_message = prompts[lang]["system_message"]
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

def analyze_paper(client, model_name, paper, lang, prompts):
    """分析论文"""
    print(f"  Analyzing: {paper.title[:60]}...")
    try:
        return _analyze_with_llm(client, model_name, paper, lang, prompts)
    except Exception as e:
        print(f"    [!] Error analyzing paper: {e}")
        return None

def _translate_text(text, client, model_name, report_templates):
    """使用 LLM 将文本翻译成中文"""
    print("  Translating top recommendation's abstract to Chinese...")
    prompt = report_templates["zh"]["translation_template"].format(text=text)
    try:
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

def generate_markdown_report(analyzed_papers, lang, client, model_name, report_templates):
    """生成 Markdown 格式的报告"""
    template = report_templates[lang]
    if not analyzed_papers:
        return template["no_papers_found"]

    analyzed_papers.sort(key=lambda x: x['analysis'].get('novelty', 0), reverse=True)
    
    recommendation = analyzed_papers[0]
    other_papers = analyzed_papers[1:]
    
    report_date = datetime.now().strftime("%Y-%m-%d")
    md_content = template["title"].format(report_date=report_date) + "\n\n"
    md_content += template["summary_by"] + "\n\n"
    
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
        translated_abstract = _translate_text(p.summary, client, model_name, report_templates)
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
    parser = argparse.ArgumentParser(description="Fetch and analyze recent LLM papers from arXiv using DeepSeek.")
    parser.add_argument("--config", type=str, default="config.json", help="Path to configuration file.")
    parser.add_argument("--max-results", type=int, default=None, help="Maximum number of papers to process.")
    parser.add_argument("-d", "--days", type=int, default=None, help="Number of days back to search for papers.")
    parser.add_argument("--lang", type=str, default=None, choices=["en", "zh"], help="Language for the output report (en/zh).")
    parser.add_argument("--api-key", type=str, default=os.getenv("ARXIV_DIGEST_API_KEY"), help="LLM API Key.")

    args = parser.parse_args()

    # --- 配置 (Configuration) ---
    # Load configuration from file
    config = load_config(args.config)
    
    # Use command-line arguments to override config file settings
    search_query = config.get("search_query", "cat:cs.CL OR cat:cs.AI OR cat:cs.LG")
    output_dir = config.get("output_dir", "arxiv_digests_md")
    max_results = args.max_results if args.max_results is not None else config.get("max_results", 20)
    days = args.days if args.days is not None else config.get("days", 2)
    lang = args.lang if args.lang is not None else config.get("lang", "zh")
    model_name = config.get("model", "deepseek-chat")
    api_base_url = config.get("api_base_url", "https://api.deepseek.com/v1")
    
    # Load prompts and templates from config
    prompts = config.get("prompts", {})
    report_templates = config.get("report_templates", {})
    
    if not prompts or not report_templates:
        print("⚠ Prompts or report templates not found in config file. Please update your configuration.")
        return

    if not args.api_key:
        raise ValueError("DeepSeek API Key not provided. Set DEEPSEEK_API_KEY environment variable or use --api-key.")
    
    # Initialize OpenAI-compatible client for DeepSeek
    client = openai.OpenAI(api_key=args.api_key, base_url=api_base_url)

    print(f"✓ Using model: {model_name}")
    print(f"✓ API base URL: {api_base_url}")

    papers = fetch_recent_papers(search_query, max_results, days)
    if not papers:
        print("No new papers to process. Exiting.")
        return

    analyzed_papers = []
    for paper in papers:
        analysis = analyze_paper(client, model_name, paper, lang, prompts)
        if analysis:
            analyzed_papers.append({"paper": paper, "analysis": analysis})
    
    report = generate_markdown_report(analyzed_papers, lang, client, model_name, report_templates)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 生成包含日期和关键词的文件名
    report_date = datetime.now().strftime("%Y-%m-%d")
    keywords = extract_keywords_from_query(search_query)
    
    # 文件名格式: digest_YYYY-MM-DD_keywords.md
    output_filename = os.path.join(output_dir, f"digest_{report_date}_{keywords}.md")

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
