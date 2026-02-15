import requests
import datetime
import os
from deep_translator import GoogleTranslator

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

def translate_titles(stories):
    """Translates the titles of the filtered stories to Japanese."""
    print("Translating titles...")
    translator = GoogleTranslator(source='auto', target='ja')
    for story in stories:
        try:
            original_title = story.get('title', '')
            translated = translator.translate(original_title)
            story['title_ja'] = translated
        except Exception as e:
            print(f"Error translating {story.get('id')}: {e}")
            story['title_ja'] = story.get('title', '') # Fallback
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
        
        report += f"### {title_ja}\n"
        report += f"- **英語タイトル**: {title}\n"
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
    translated_stories = translate_titles(ai_stories)

    # 4. Report
    report = generate_report(translated_stories)
    
    # Output report to file (for GitHub Actions to pick up)
    # The GH Action will read this file to populate the issue body
    with open('daily_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("Report generated: daily_report.md")

if __name__ == "__main__":
    main()
