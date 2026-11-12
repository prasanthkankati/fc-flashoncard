import os
import json
import time
from pathlib import Path
import requests

BASE_DIR = Path(__file__).parent.resolve()
CONFIG_PATH = str(BASE_DIR / "config.json")
SLIDES_DIR = str(BASE_DIR / "dist" / "today")

def load_config():
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}
    # Environment variables override config.json
    for key in ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "INSTAGRAM_POSTING_METHOD", "INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_ACCOUNT_ID"]:
        if os.environ.get(key):
            cfg[key] = os.environ[key]
    return cfg

def send_approval_pack(custom_caption=None):
    cfg = load_config()
    token = cfg["TELEGRAM_BOT_TOKEN"]
    chat_id = cfg["TELEGRAM_CHAT_ID"]
    api_url = f"https://api.telegram.org/bot{token}"
    
    print(f"Connecting to Telegram (Chat ID: {chat_id})...")
    
    # 1. Send all 6 slides as a swipeable photo album
    print("Uploading 6 slides as album to your phone...")
    media = []
    files = {}
    opened_files = []
    
    for i in range(1, 7):
        path = os.path.join(SLIDES_DIR, f"Slide-0{i}.png")
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
        print("Media album delivered to Telegram!")
        
    for f in opened_files:
        f.close()

    # 2. Send the Executive Caption & Approval Action Buttons
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ APPROVE & POST", "callback_data": "approve_post"},
                {"text": "❌ REJECT", "callback_data": "reject_post"}
            ]
        ]
    }
    
    if custom_caption:
        caption_text = f"🚨 *FC EDITORIAL DISPATCH • APPROVAL GATE*\n\n{custom_caption}\n\n👇 *Tap an action below to proceed:*"
    else:
        caption_text = (
            "🚨 *FC EDITORIAL DISPATCH • APPROVAL GATE*\n\n"
            "*Theme:* White Studio (Mobile-Tested 4:5 • 1080×1350)\n\n"
            "👇 *Tap an action below to proceed:*"
        )
    
    msg_res = requests.post(f"{api_url}/sendMessage", data={
        "chat_id": chat_id,
        "text": caption_text,
        "parse_mode": "Markdown",
        "reply_markup": json.dumps(keyboard)
    })
    
    print("Approval prompt with buttons sent to your phone!")
    return True

def wait_for_approval(timeout_seconds=None):
    cfg = load_config()
    token = cfg["TELEGRAM_BOT_TOKEN"]
    api_url = f"https://api.telegram.org/bot{token}"
    
    if timeout_seconds is None:
        timeout_seconds = int(os.environ.get("APPROVAL_TIMEOUT_SECONDS", "1800")) # Default 30 minutes
        
    offset = None
    print(f"\nListening for your mobile tap... (Window: {timeout_seconds // 60} mins) [APPROVE] or [REJECT] on your phone")
    
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        poll_url = f"{api_url}/getUpdates?timeout=15"
        if offset:
            poll_url += f"&offset={offset}"
            
        try:
            r = requests.get(poll_url, timeout=20)
            res = r.json()
            for update in res.get("result", []):
                offset = update["update_id"] + 1
                if "callback_query" in update:
                    cq = update["callback_query"]
                    data = cq.get("data")
                    cq_id = cq.get("id")
                    
                    if data == "approve_post":
                        requests.post(f"{api_url}/answerCallbackQuery", data={
                            "callback_query_id": cq_id,
                            "text": "✔ Approved! Dispatching to Instagram..."
                        })
                        requests.post(f"{api_url}/sendMessage", data={
                            "chat_id": cfg["TELEGRAM_CHAT_ID"],
                            "text": "🚀 *APPROVED!* Dispatching carousel to Instagram right now..."
                        })
                        return True
                    elif data == "reject_post":
                        requests.post(f"{api_url}/answerCallbackQuery", data={
                            "callback_query_id": cq_id,
                            "text": "✖ Rejected. Dispatch cancelled."
                        })
                        requests.post(f"{api_url}/sendMessage", data={
                            "chat_id": cfg["TELEGRAM_CHAT_ID"],
                            "text": "✖ *REJECTED.* This dispatch will not be posted."
                        })
                        return False
        except Exception:
            time.sleep(1)
            
    print("Approval timeout reached.")
    return None

if __name__ == "__main__":
    send_approval_pack()
    result = wait_for_approval()
    print(f"\nFinal Outcome: {result}")
