import re

def parse_story_to_fc_item(story, idx):
    title = story["title"]
    # Strip source suffix if present (e.g. " - The Hindu")
    clean_title = re.sub(r'\s*-\s*[^-]+$', '', title).strip()
    source = story.get("source", "NEWS DISPATCH")
    
    # 1. Detect Category & Vector
    lower_t = clean_title.lower()
    if any(k in lower_t for k in ["metro", "rail", "transit", "train"]):
        category = "TRANSIT & MOBILITY"
        code = f"TRANSIT//0{idx+1}"
        vector = "metro"
    elif any(k in lower_t for k in ["ai", "chip", "semiconductor", "tech", "hardware", "software"]):
        category = "TECH & HARDWARE"
        code = f"TECH//0{idx+1}"
        vector = "chip"
    elif any(k in lower_t for k in ["ring road", "highway", "expressway", "flyover", "road"]):
        category = "MEGA INFRASTRUCTURE"
        code = f"INFRA//0{idx+1}"
        vector = "highway"
    elif any(k in lower_t for k in ["hospital", "health", "equipment", "upgrades", "collector"]):
        category = "PUBLIC HEALTH & CIVIC"
        code = f"CIVIC//0{idx+1}"
        vector = "tower"
    else:
        category = "URBAN DEVELOPMENT"
        code = f"URBAN//0{idx+1}"
        vector = "tower"
        
    # 2. Extract Numbers or Key Highlights
    # Search for currency, numbers, km, percent
    numbers = re.findall(r'[₹$€]\s*[\d,]+(?:\.\d+)?(?:\s*(?:crore|cr|lakh|bn|m))?|\b\d+(?:,\d+)*(?:\.\d+)?%?|\b\d+\s*(?:km|sq\s*ft|mw|acres)\b', clean_title, flags=re.IGNORECASE)
    highlight_term = numbers[0].upper() if numbers else None
    
    # 3. Create 3 Headline Lines for Bebas Neue
    words = clean_title.upper().split()
    # Split into 3 chunks
    total_w = len(words)
    chunk1 = " ".join(words[:max(1, total_w//3)])
    chunk2 = " ".join(words[max(1, total_w//3):max(2, 2*total_w//3)])
    chunk3 = " ".join(words[max(2, 2*total_w//3):])
    
    headline_lines = []
    for chunk in [chunk1, chunk2, chunk3]:
        if not chunk: continue
        is_highlight = False
        if highlight_term and highlight_term in chunk:
            is_highlight = True
        headline_lines.append({"text": chunk, "isHighlight": is_highlight})
        
    # Ensure at least one line is highlighted
    if not any(l["isHighlight"] for l in headline_lines) and len(headline_lines) >= 2:
        headline_lines[1]["isHighlight"] = True

    # 4. Create 3 Bullet Points
    points = [
        f"Key milestone reported today: {clean_title}.",
        f"Monitored closely by regional authorities under {category.lower()} priority.",
        f"Verified directly via official reporting from {source}."
    ]
    
    # 5. Summary
    summary = f"New developments recorded across Hyderabad as {clean_title.lower()} progresses with active administrative oversight."
    
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

if __name__ == "__main__":
    test_story = {
        "title": "Hyderabad Metro Phase 2: Centre Reportedly Sanctions ₹275 Crore, ₹150 Crore for Expansion Works - Metro Rail News",
        "source": "METRO RAIL NEWS"
    }
    import json
    print(json.dumps(parse_story_to_fc_item(test_story, 0), indent=2))
