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

RSS_QUERIES = [
    "Hyderabad+metro+OR+infrastructure+OR+tech+OR+AI+OR+Telangana",
    "India+semiconductor+OR+ISRO+OR+AI+OR+data+center+OR+expressway",
    "India+fintech+OR+UPI+OR+startup+OR+manufacturing+OR+renewable+energy",
    "OpenAI+OR+Anthropic+OR+Nvidia+OR+TSMC+OR+compute+OR+robotics",
    "Hyderabad+GCC+OR+HITEC+City+OR+pharma+OR+aerospace+OR+investment",
]

VECTOR_POOL = [
    "metro",
    "chip",
    "highway",
    "tower",
    "hospital",
    "currency_sanction",
    "metro_guideway",
    "ai_education",
]


def fetch_rss_news(query=RSS_QUERIES[0]):
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
                if any(x in lower_t for x in [
                    'cricket', 'murder', 'arrested', 'movie', 'cinema', 'trailer', 'song',
                    'gutted', 'fire', 'accident', 'killed', 'died', 'dead', 'rape', 'robbery',
                    'theft', 'cyclothon', 'marathon', 'lok sabha', 'election', 'party worker'
                ]):
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
        print(f"Error fetching RSS ({query}): {e}")
        return []


def extract_unique_stories(count=4):
    seen_hashes = set(get_history())
    unique_stories = []
    new_hashes = []

    for query in RSS_QUERIES:
        raw_stories = fetch_rss_news(query)
        for s in raw_stories:
            h = hash_title(s['title'])
            if h not in seen_hashes:
                seen_hashes.add(h)
                unique_stories.append(s)
                new_hashes.append(h)
                if len(unique_stories) >= count:
                    return unique_stories, new_hashes

    return unique_stories, new_hashes


def _truncate_words(text, max_len):
    text = re.sub(r'\s+', ' ', (text or '')).strip()
    if len(text) <= max_len:
        return text
    words = text.split(' ')
    out = ''
    for w in words:
        candidate = (out + ' ' + w).strip() if out else w
        if len(candidate) <= max_len:
            out = candidate
        else:
            break
    if not out:
        return text[:max_len].strip()
    return out.rstrip(',;:-')


def _build_headline_lines(clean_title, max_chars=14, max_lines=3):
    words = [w for w in re.sub(r'\s+', ' ', clean_title.upper()).strip().split(' ') if w]
    lines = []
    current = ''
    for w in words:
        if len(w) > max_chars:
            w = w[:max_chars]
        candidate = (current + ' ' + w).strip() if current else w
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
                if len(lines) >= max_lines:
                    current = ''
                    break
            current = w
    if current and len(lines) < max_lines:
        lines.append(current)

    fallbacks = ["KEY", "SHIFT", "UPDATE"]
    while len(lines) < max_lines:
        lines.append(fallbacks[len(lines)])

    highlight_idx = next(
        (i for i, text in enumerate(lines) if any(ch.isdigit() or ch in '₹$%' for ch in text)),
        1,
    )
    return [{"text": text, "isHighlight": i == highlight_idx} for i, text in enumerate(lines)]


def _pick_unique_vector(preferred, used_vectors):
    if used_vectors is None:
        return preferred
    if preferred not in used_vectors:
        used_vectors.add(preferred)
        return preferred
    for candidate in VECTOR_POOL:
        if candidate not in used_vectors:
            used_vectors.add(candidate)
            return candidate
    return preferred


def parse_story_to_fc_item(story, idx, used_vectors=None):
    title = story["title"]
    clean_title = re.sub(r'\s*-\s*[^-]+$', '', title).strip()
    source = story.get("source", "NEWS DISPATCH")
    lower_t = clean_title.lower()

    if any(k in lower_t for k in ["hospital", "health", "pharma", "medical", "upgrades"]):
        category = "HEALTHCARE & CIVIC"
        code = f"CIVIC//0{idx+1}"
        preferred_vector = "hospital"
    elif any(k in lower_t for k in ["sanction", "crore", "billion", "million", "₹", "$", "fintech", "upi", "funding", "investment"]):
        category = "CAPITAL & MARKETS"
        code = f"CAPITAL//0{idx+1}"
        preferred_vector = "currency_sanction"
    elif any(k in lower_t for k in ["old city", "metro", "rail", "transit", "airport"]):
        category = "URBAN CONNECTIVITY"
        code = f"TRANSIT//0{idx+1}"
        preferred_vector = "metro_guideway" if idx % 2 == 0 else "metro"
    elif any(k in lower_t for k in ["expressway", "highway", "corridor", "road", "infrastructure"]):
        category = "INFRASTRUCTURE"
        code = f"INFRA//0{idx+1}"
        preferred_vector = "highway"
    elif any(k in lower_t for k in ["iit", "academy", "education", "training", "university"]):
        category = "AI & TALENT"
        code = f"ACADEMY//0{idx+1}"
        preferred_vector = "ai_education"
    elif any(k in lower_t for k in ["chip", "semiconductor", "tsmc", "nvidia", "ai", "openai", "anthropic", "compute", "data center", "isro", "robotics"]):
        category = "AI & DEEP TECH"
        code = f"TECH//0{idx+1}"
        preferred_vector = "chip"
    else:
        category = "URBAN DEVELOPMENT"
        code = f"DISPATCH//0{idx+1}"
        preferred_vector = "tower"

    vector = _pick_unique_vector(preferred_vector, used_vectors)
    headline_lines = _build_headline_lines(clean_title, max_chars=14, max_lines=3)
    summary = _truncate_words(clean_title, 78)
    desc = _truncate_words(story.get("description", ""), 92)
    points = [
        _truncate_words(clean_title, 95),
        desc if len(desc) >= 24 else _truncate_words(f"Key shift tracked under {category.lower()} developments.", 88),
        _truncate_words(f"Verified dispatch reported by {source}.", 88),
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
    used_vectors = set()
    fc_items = [parse_story_to_fc_item(s, i, used_vectors=used_vectors) for i, s in enumerate(stories)]
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
    lines = []
    for s in stories:
        clean = re.sub(r'\s*-\s*[^-]+$', '', s['title']).strip()
        lines.append(f"• {clean}")
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
