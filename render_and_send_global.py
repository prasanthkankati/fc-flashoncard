import os
import sys
import time
import json
from pathlib import Path
import requests
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = str(BASE_DIR / "dist" / "global")
HTML_PATH = (BASE_DIR / "global_index.html").as_uri()
CONFIG_PATH = str(BASE_DIR / "config.json")

def render_global_slides():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        main_page = browser.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        
        print("Loading Global studio HTML...")
        main_page.goto(HTML_PATH, wait_until="networkidle")
        time.sleep(2)
        
        for i in range(6):
            print(f"Rendering Global Slide {i+1} of 6 (1080×1350 HD)...")
            svg_string = main_page.evaluate(f"renderDispatchSlide({i})")
            
            frame_page = browser.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
            frame_page.set_content(f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <link rel="preconnect" href="https://fonts.googleapis.com">
                    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
                    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Oswald:wght@600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800;900&family=JetBrains+Mono:wght@600;700;800&family=Syne:wght@700;800&display=swap" rel="stylesheet">
                    <style>
                        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                        body {{ width: 1080px; height: 1350px; overflow: hidden; background: #FFFFFF; }}
                        svg {{ width: 1080px; height: 1350px; display: block; }}
                    </style>
                </head>
                <body>
                    {svg_string}
                </body>
                </html>
            """, wait_until="networkidle")
            time.sleep(0.8)
            
            out_file = os.path.join(OUTPUT_DIR, f"Slide-0{i+1}.png")
            frame_page.screenshot(path=out_file, type="png")
            frame_page.close()
            print(f"Saved: {out_file} ({os.path.getsize(out_file):,} bytes)")
            
        main_page.close()
        browser.close()
        print(f"✓ All 6 Global slides successfully rendered to {OUTPUT_DIR}!")

def send_global_approval_pack():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
        
    token = cfg["TELEGRAM_BOT_TOKEN"]
    chat_id = cfg["TELEGRAM_CHAT_ID"]
    api_url = f"https://api.telegram.org/bot{token}"
    
    print(f"\nConnecting to Telegram Bot for Global Dispatch (Chat ID: {chat_id})...")
    
    media = []
    files = {}
    opened_files = []
    
    for i in range(1, 7):
        path = os.path.join(OUTPUT_DIR, f"Slide-0{i}.png")
        if os.path.exists(path):
            f = open(path, "rb")
            opened_files.append(f)
            files[f"photo{i}"] = f
            media.append({"type": "photo", "media": f"attach://photo{i}"})
            
    if media:
        res = requests.post(f"{api_url}/sendMediaGroup", data={
            "chat_id": chat_id,
            "media": json.dumps(media)
        }, files=files)
        print("✓ Global 6-slide photo album delivered to Telegram!")
        
    for f in opened_files:
        f.close()

    caption = (
        "🌍 *FC GLOBAL TECH & COMPUTE DISPATCH • APPROVAL GATE*\n\n"
        "Key developments unfolding globally today:\n"
        "• *Anthropic Inks $3.4B Gas-Powered AI Data Center Deal* (Grid Independence)\n"
        "• *AI Cloud Demand Surges Past $100B+* (CoreWeave & Nvidia GPU Trade Rally)\n"
        "• *OpenAI Reasoning Models Independently Confirm Major Physics Breakthrough*\n"
        "• *TSMC Accelerates 2nm Silicon Foundry Dominance & Packaging Lead*\n\n"
        "📱 *Format:* 1080×1350 px (4:5 Carousel)\n"
        "🎨 *Design:* Minimalist White Studio • High-Impact Editorial Typography\n\n"
        "👇 *Tap an action below to proceed:*"
    )
    
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ APPROVE & POST GLOBAL", "callback_data": "approve_global"},
                {"text": "❌ REJECT", "callback_data": "reject_global"}
            ]
        ]
    }
    
    requests.post(f"{api_url}/sendMessage", data={
        "chat_id": chat_id,
        "text": caption,
        "parse_mode": "Markdown",
        "reply_markup": json.dumps(keyboard)
    })
    print("✓ Global approval prompt with action buttons sent to phone!")

if __name__ == "__main__":
    render_global_slides()
    send_global_approval_pack()
