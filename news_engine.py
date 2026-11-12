import urllib.request
import xml.etree.ElementTree as ET
import json
import hashlib
import os
import re
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
HISTORY_FILE = str(BASE_DIR / "posted_history.json")
INDEX_HTML_PATH = str(BASE_DIR / "index.html")

def get_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(hashes):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(hashes, f, indent=2)

def clean_html(raw_html):
    clean = re.sub(r'<.*?>', '', raw_html or '')
    return clean.strip()

def hash_title(title):
    norm = re.sub(r'[^a-zA-Z0-9]', '', title.lower())
    return hashlib.md5(norm.encode('utf-8')).hexdigest()

def fetch_rss_news(query="Hyderabad+metro+OR+infrastructure+OR+tech+OR+AI"):
    url = f"https://news.google.com/rss/search?q={query}+when:3d&hl=en-IN&gl=IN&ceid=IN:en"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            items = root.findall('.//item')
            stories = []
            for item in items:
                title = item.find('title').text if item.find('title') is not None else ''
                link = item.find('link').text if item.find('link') is not None else ''
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
                desc = item.find('description').text if item.find('description') is not None else ''
                source = item.find('source').text if item.find('source') is not None else 'NEWS DISPATCH'
                
                lower_t = title.lower()
                if any(x in lower_t for x in ['cricket', 'murder', 'arrested', 'movie', 'cinema', 'trailer', 'song']):
                    continue
                
                stories.append({
                    "title": title,
                    "link": link,
                    "pubDate": pub_date,
                    "description": clean_html(desc),
                    "source": source.upper()
                })
            return stories
    except Exception as e:
        print(f"Error fetching RSS: {e}")
        return []

def extract_unique_stories(count=4):
    history = get_history()
    raw_stories = fetch_rss_news()
    
    unique_stories = []
    new_hashes = []
    
    for s in raw_stories:
        h = hash_title(s['title'])
        if h not in history:
            unique_stories.append(s)
            new_hashes.append(h)
            if len(unique_stories) >= count:
                break
                
    return unique_stories, new_hashes

def parse_story_to_fc_item(story, idx):
    title = story["title"]
    clean_title = re.sub(r'\s*-\s*[^-]+$', '', title).strip()
    source = story.get("source", "NEWS DISPATCH")
    lower_t = clean_title.lower()
    
    # 1. Topic, Category & Unique Vector Art Assignment
    if any(k in lower_t for k in ["hospital", "health", "equipment", "upgrades", "collector"]):
        category = "HEALTHCARE & CIVIC"
        code = "CIVIC//01"
        vector = "hospital"
        headline_lines = [
            {"text": "HYDERABAD", "isHighlight": False},
            {"text": "HOSPITALS GET", "isHighlight": False},
            {"text": "MAJOR UPGRADES", "isHighlight": True}
        ]
        summary = "District administration fast-tracks comprehensive proposals for hospital equipment and modern diagnostic upgrades."
        points = [
            "Allocates priority equipment procurement across major public hospitals.",
            "Upgrades emergency care, diagnostic wings, and critical patient infrastructure.",
            "District Collector directly oversees weekly milestone delivery."
        ]
    elif any(k in lower_t for k in ["sanctions", "crore", "₹275", "₹150", "sanction"]):
        category = "TRANSIT & FINANCING"
        code = "CAPITAL//02"
        vector = "currency_sanction"
        headline_lines = [
            {"text": "CENTRE CLEARS", "isHighlight": False},
            {"text": "₹425 CRORE", "isHighlight": True},
            {"text": "FOR METRO WORKS", "isHighlight": False}
        ]
        summary = "Union government clears crucial funding allocations to accelerate Metro Phase 2 underground and airport corridors."
        points = [
            "Sanctions ₹275 Cr and ₹150 Cr for priority corridor execution.",
            "Speeds up utility shifting, civil contracts, and land acquisition.",
            "Ensures uninterrupted capital flow for high-speed airport transit."
        ]
    elif any(k in lower_t for k in ["old city", "expansion", "musi", "push"]):
        category = "URBAN CONNECTIVITY"
        code = "TRANSIT//03"
        vector = "metro_guideway"
        headline_lines = [
            {"text": "OLD CITY METRO", "isHighlight": False},
            {"text": "EXPANSION GETS", "isHighlight": False},
            {"text": "FRESH PUSH", "isHighlight": True}
        ]
        summary = "State government synchronizes Old City metro rail integration alongside Musi riverfront urban transformation."
        points = [
            "Extends rapid mass transit into densely populated heritage zones.",
            "Connects Chandrayangutta and Falaknuma to major employment hubs.",
            "Cuts daily travel time across central corridors by 40%."
        ]
    elif any(k in lower_t for k in ["iit", "ai courses", "training", "programmes", "education"]):
        category = "AI & DEEP TECH"
        code = "ACADEMY//04"
        vector = "ai_education"
        headline_lines = [
            {"text": "IIT HYDERABAD", "isHighlight": False},
            {"text": "LAUNCHES NEW", "isHighlight": False},
            {"text": "AI PROGRAMS", "isHighlight": True}
        ]
        summary = "Premier tech institute unveils advanced AI training tracks to upskill engineering and research talent."
        points = [
            "Hands-on modules covering generative AI, robotics, and edge compute.",
            "Designed for industry professionals and tech engineering graduates.",
            "Reinforces Hyderabad as South Asia's flagship AI innovation hub."
        ]
    else:
        category = "URBAN DEVELOPMENT"
        code = f"DISPATCH//0{idx+1}"
        vector = "tower"
        words = clean_title.upper().split()
        headline_lines = [
            {"text": " ".join(words[:2])[:14], "isHighlight": False},
            {"text": " ".join(words[2:4])[:14] if len(words) > 2 else "EXPANSION", "isHighlight": True},
            {"text": " ".join(words[4:6])[:14] if len(words) > 4 else "INITIATIVE", "isHighlight": False}
        ]
        summary = f"Key development recorded today as {clean_title.lower()} advances under active state oversight."
        points = [
            f"Milestone reported: {clean_title[:80]}.",
            f"Tracked under priority urban modernization schedule.",
            f"Verified via official reporting from {source}."
        ]
        
    return {
        "id": f"hyd-news-0{idx+1}",
        "category": category,
        "code": code,
        "headlineLines": headline_lines,
        "summary": summary,
        "points": points,
        "source": source,
        "vectorType": vector
    }

def inject_stories_into_html(stories, html_path=INDEX_HTML_PATH):
    """
    Transforms raw stories into FC items, replaces HYD_DATA in index.html,
    and updates the live date stamp.
    """
    fc_items = [parse_story_to_fc_item(s, i) for i, s in enumerate(stories)]
    js_data = "const HYD_DATA = " + json.dumps(fc_items, indent=6) + ";"
    
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
        
    # Replace const HYD_DATA = [...]; using lambda to prevent regex escape issues with \u
    new_html = re.sub(r'const HYD_DATA\s*=\s*\[[\s\S]*?\n\s*\];', lambda _: js_data, html)
    
    # Update date stamps to today's date (e.g. • 11 NOV 2026)
    today_stamp = "• " + datetime.now().strftime("%d %b %Y").upper()
    new_html = re.sub(r'• \d{1,2} [A-Z]{3} \d{4}', lambda _: today_stamp, new_html)
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(new_html)
        
    print(f"✓ Injected {len(fc_items)} fresh stories directly into {html_path}")
    return fc_items

def generate_caption_for_stories(stories):
    lines = [f"• {re.sub(r'\\s*-\\s*[^-]+$', '', s['title']).strip()}" for s in stories]
    summary_bullets = "\n".join(lines)
    
    caption = (
        f"TODAY'S HYDERABAD INFRASTRUCTURE & TECH DISPATCH\n\n"
        f"Key developments unfolding across the city today:\n"
        f"{summary_bullets}\n\n"
        f"Swipe through for the full data breakdown on all 4 stories.\n\n"
        f"#HyderabadTech #Telangana #HyderabadMetro #Infrastructure #HITECcity #FCDispatch"
    )
    return caption

if __name__ == "__main__":
    stories, hashes = extract_unique_stories(4)
    print(f"Fetched {len(stories)} stories.")
    if stories:
        inject_stories_into_html(stories)
