import os
import sys
import json
from pathlib import Path
import requests

BASE_DIR = Path(__file__).parent.resolve()
sys.path.append(str(BASE_DIR))
from instagram_publisher import publish_via_playwright, SESSION_PATH
from approval_bot import load_config

def publish_now():
    cfg = load_config()
    caption = (
        "TODAY'S HYDERABAD INFRASTRUCTURE & TECH DISPATCH\n\n"
        "Key developments unfolding across the city today:\n"
        "• Hyderabad Hospitals Get Major Upgrades Under District Oversight\n"
        "• Centre Clears ₹425 Crore For Metro Phase 2 Underground & Airport Works\n"
        "• Old City Metro Expansion Gets Fresh Push Alongside Musi Riverfront\n"
        "• IIT Hyderabad Launches New Advanced AI Programs & Tracks\n\n"
        "Swipe through for the full data breakdown on all 4 shifts.\n\n"
        "#HyderabadTech #Telangana #HyderabadMetro #Infrastructure #HITECcity #FCDispatch"
    )
    image_paths = [str(BASE_DIR / "dist" / "today" / f"Slide-0{i}.png") for i in range(1, 7)]
    
    print(f"Publishing {len(image_paths)} slides to Instagram...")
    posted = publish_via_playwright(image_paths, caption)
    
    if posted:
        token = cfg["TELEGRAM_BOT_TOKEN"]
        chat_id = cfg["TELEGRAM_CHAT_ID"]
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={
            "chat_id": chat_id,
            "text": "🎉 *SUCCESS!* Your updated 6-slide editorial dispatch has been published live to Instagram!"
        })
        print("✓ Confirmation sent to Telegram!")
    else:
        print("Publishing returned False.")

if __name__ == "__main__":
    publish_now()
