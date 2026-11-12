"""
FC EDITORIAL DISPATCH • MASTER DAILY AUTOMATION RUNNER
Fetches unique news -> Renders 6 4:5 PNGs -> Sends Mobile Telegram Approval -> Publishes to Instagram
"""

import os
import sys
import json
import time
from pathlib import Path
from news_engine import extract_unique_stories, save_history, get_history, inject_stories_into_html, generate_caption_for_stories
from render_engine import render_all_slides
from approval_bot import send_approval_pack, wait_for_approval, load_config
from instagram_publisher import publish_via_playwright, publish_via_graph_api, SESSION_PATH

BASE_DIR = Path(__file__).parent.resolve()
CONFIG_PATH = str(BASE_DIR / "config.json")
SLIDES_DIR = str(BASE_DIR / "dist" / "today")

def run_daily_dispatch():
    print("=" * 60)
    print("🚀 STARTING FC DAILY EDITORIAL DISPATCH PIPELINE")
    print("=" * 60)
    
    # STEP 1: Fetch fresh unique news
    print("\n[1/4] Fetching 100% unique news stories...")
    stories, new_hashes = extract_unique_stories(4)
    if not stories:
        print("No new unique stories found. Try expanding RSS queries.")
        return
        
    print(f"✓ Found {len(stories)} fresh stories.")
    for i, s in enumerate(stories):
        print(f"   {i+1}. {s['title']}")
        
    # Inject fresh stories into index.html so render engine draws NEW content
    print("\n[2/4] Formatting & injecting stories into studio template...")
    inject_stories_into_html(stories)
    caption = generate_caption_for_stories(stories)
        
    # STEP 3: Headless 1080x1350 slide rendering
    print("\n[3/4] Headlessly rendering all 6 slides via Playwright...")
    render_all_slides()
    print("✓ All 6 slides rendered to dist/today/")
    
    # STEP 4: Push mobile approval package to Telegram
    print("\n[4/4] Pushing approval package to your phone via Telegram...")
    send_approval_pack(custom_caption=caption)
    
    # STEP 5: Listen for mobile tap
    print("\n[5/5] Awaiting your tap on Telegram: [APPROVE] or [REJECT]...")
    approved = wait_for_approval()
    
    if approved is True:
        print("\n🎉 DISPATCH APPROVED ON MOBILE! Executing Instagram Publish...")
        
        # Prepare file paths
        image_paths = [os.path.join(SLIDES_DIR, f"Slide-0{i}.png") for i in range(1, 7)]
        
        cfg = load_config()
        if cfg.get("INSTAGRAM_POSTING_METHOD") == "graph_api" and cfg.get("INSTAGRAM_ACCESS_TOKEN"):
            print("Publishing via Meta Instagram Graph API...")
            # Note: Graph API requires publicly hosted image URLs
            pass
        elif os.path.exists(SESSION_PATH):
            print("Publishing via saved Playwright browser session...")
            posted = publish_via_playwright(image_paths, caption)
            if posted:
                # Send confirmation to Telegram
                import requests
                token = cfg["TELEGRAM_BOT_TOKEN"]
                chat_id = cfg["TELEGRAM_CHAT_ID"]
                requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={
                    "chat_id": chat_id,
                    "text": "🎉 *SUCCESS!* Your 6-slide carousel has been published live to Instagram!"
                })
        else:
            print("⚠ Instagram session not yet connected. Run: python instagram_publisher.py --login")
            
        # Update history so stories never repeat
        history = get_history()
        history.extend(new_hashes)
        save_history(history)
        print("✓ Deduplication history updated.")
        print("\n🏆 Daily dispatch complete!")
        
    elif approved is False:
        print("\n❌ Dispatch was REJECTED from your phone. Nothing was posted.")
    else:
        print("\n⌛ Approval timed out.")

if __name__ == "__main__":
    run_daily_dispatch()
