import requests
import datetime
import os
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup

# Configuration
HN_API_BASE = "https://hacker-news.firebaseio.com/v0"
KEYWORDS = [
    'AI', 'LLM', 'GPT', 'Transformer', 'Google', 'Apple', 
    'OpenAI', 'Microsoft', 'NVIDIA', 'Silicon Valley', 
    'Machine Learning', 'Gemini', 'Claude', 'DeepMind',
    'Neural', 'Robot', 'Autonomous'
]

def get_top_stories(limit=100):
    """Fetches top 500 stories IDs and details for the first `limit` items."""
    print(f"Fetching top stories (checking top {limit})...")
    try:
        response = requests.get(f"{HN_API_BASE}/topstories.json")
        response.raise_for_status()
        story_ids = response.json()[:limit]
    except Exception as e:
        print(f"Error fetching story IDs: {e}")
        return []

    stories = []
    for sid in story_ids:
        try:
            item_resp = requests.get(f"{HN_API_BASE}/item/{sid}.json")
            if item_resp.status_code == 200:
                stories.append(item_resp.json())
        except Exception as e:
            print(f"Error fetching story {sid}: {e}")
    return stories

def filter_stories(stories):
    """Filters stories based on keywords in the title."""
    filtered = []
    print("Filtering stories...")
    for story in stories:
        title = story.get('title', '')
        url = story.get('url', '')
        
        # Check if any keyword corresponds
        if any(k.lower() in title.lower() for k in KEYWORDS):
            filtered.append(story)
    return filtered

def fetch_article_summary(url, max_length=500):
    """Fetches the article content and returns a summary."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'lxml')
            paragraphs = soup.find_all('p')
            text_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
            full_text = ' '.join(text_parts)
            if len(full_text) > max_length:
                return full_text[:max_length] + "..."
            elif full_text:
                return full_text
    except Exception as e:
        print(f"Error fetching article summary from {url}: {e}")
    return ""

def translate_stories(stories):
    """Translates the titles and summaries of the filtered stories to Japanese."""
    print("Translating titles and summaries...")
    translator = GoogleTranslator(source='auto', target='ja')
    for story in stories:
        # Translate title
        try:
            original_title = story.get('title', '')
            if original_title:
                translated_title = translator.translate(original_title)
                story['title_ja'] = translated_title
            else:
                story['title_ja'] = ''
        except Exception as e:
            print(f"Error translating title {story.get('id')}: {e}")
            story['title_ja'] = story.get('title', '') # Fallback

        # Fetch and translate summary
        url = story.get('url', '')
        if url:
            summary = fetch_article_summary(url)
            if summary:
                try:
                    translated_summary = translator.translate(summary)
                    story['summary_ja'] = translated_summary
                except Exception as e:
                    print(f"Error translating summary {story.get('id')}: {e}")
                    story['summary_ja'] = ''
            else:
                story['summary_ja'] = ''
        else:
            story['summary_ja'] = ''
    return stories

def generate_report(stories):
    """Generates a Markdown report from the stories."""
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    report = f"# 🤖 今日のAIニュース ({today})\n\n"
    
    if not stories:
        report += "今日のトップニュースに関連記事は見つかりませんでした。\n"
        return report

    for story in stories:
        title = story.get('title', 'No Title')
        title_ja = story.get('title_ja', title)
        url = story.get('url', f"https://news.ycombinator.com/item?id={story.get('id')}")
        score = story.get('score', 0)
        summary_ja = story.get('summary_ja', '')
        
        report += f"### {title_ja}\n"
        report += f"- **英語タイトル**: {title}\n"
        if summary_ja:
            report += f"- **要約**: {summary_ja}\n"
        report += f"- **Score**: {score}\n"
        report += f"- [記事を読む]({url})\n\n"
        
    return report

def main():
    # 1. Get Stories
    stories = get_top_stories(limit=100) # Check top 100 for relevance
    
    # 2. Filter
    ai_stories = filter_stories(stories)
    print(f"Found {len(ai_stories)} AI-related stories out of {len(stories)} scanned.")

    # 3. Translate
    translated_stories = translate_stories(ai_stories)

    # 4. Report
    report = generate_report(translated_stories)
    
    # Output report to file (for GitHub Actions to pick up)
    # The GH Action will read this file to populate the issue body
    with open('daily_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("Report generated: daily_report.md")

if __name__ == "__main__":
    main()
