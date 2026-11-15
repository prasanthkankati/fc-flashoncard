"""
FC EDITORIAL DISPATCH • MASTER DAILY AUTOMATION RUNNER
Fetches unique news -> Renders 6 4:5 PNGs -> Sends Mobile Telegram Approval -> Publishes to Instagram
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
import json
import requests
from news_engine import extract_unique_stories, save_history, get_history, inject_stories_into_html, generate_caption_for_stories
from render_engine import render_all_slides
from approval_bot import send_approval_pack, wait_for_approval, load_config
from instagram_publisher import publish_via_playwright, SESSION_PATH

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).parent.resolve()
CONFIG_PATH = str(BASE_DIR / "config.json")
SLIDES_DIR = str(BASE_DIR / "dist" / "today")


def _send_telegram_message(cfg, text):
    token = cfg.get("TELEGRAM_BOT_TOKEN")
    chat_id = cfg.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=20,
        )
    except Exception as e:
        print(f"Telegram message warning: {e}")


def _send_telegram_album(cfg, image_paths, caption):
    token = cfg.get("TELEGRAM_BOT_TOKEN")
    chat_id = cfg.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    media = []
    files = {}
    opened_files = []
    try:
        for i, path in enumerate(image_paths, start=1):
            if os.path.exists(path):
                f = open(path, "rb")
                opened_files.append(f)
                files[f"photo{i}"] = f
                item = {"type": "photo", "media": f"attach://photo{i}"}
                if i == 1 and caption:
                    item["caption"] = caption[:1024]
                media.append(item)
        if media:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMediaGroup",
                data={"chat_id": chat_id, "media": json.dumps(media)},
                files=files,
                timeout=60,
            )
            print("✓ 6-slide dispatch album sent to Telegram.")
    except Exception as e:
        print(f"Telegram album warning: {e}")
    finally:
        for f in opened_files:
            f.close()


def run_daily_dispatch():
    print("=" * 60)
    print(f"🚀 STARTING FC EDITORIAL DISPATCH PIPELINE ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print("=" * 60)

    # STEP 1: Fetch fresh unique news
    print("\n[1/4] Fetching 100% unique news stories...")
    stories, new_hashes = extract_unique_stories(4)
    if not stories:
        print("No new unique stories found. Try expanding RSS queries.")
        return False

    print(f"✓ Found {len(stories)} fresh stories.")
    for i, s in enumerate(stories):
        print(f"   {i+1}. {s['title']}")

    # STEP 2: Inject fresh stories into index.html
    print("\n[2/4] Formatting & injecting stories into studio template...")
    inject_stories_into_html(stories)
    caption = generate_caption_for_stories(stories)

    # STEP 3: Headless 1080x1350 slide rendering
    print("\n[3/4] Headlessly rendering all 6 slides via Playwright...")
    render_all_slides()
    print("✓ All 6 slides rendered to dist/today/")

    image_paths = [os.path.join(SLIDES_DIR, f"Slide-0{i}.png") for i in range(1, 7)]
    cfg = load_config()
    auto_approve = os.environ.get("AUTO_APPROVE", "true").lower() != "false" and "--require-approval" not in sys.argv

    if auto_approve:
        print("\n[4/4] Auto-publishing directly (Fetch -> Create -> Post)...")
        _send_telegram_album(cfg, image_paths, caption)

        if not os.path.exists(SESSION_PATH):
            print("⚠ Instagram session not found. Run: python instagram_publisher.py --login")
            _send_telegram_message(
                cfg,
                "⚠️ *PUBLISH SKIPPED:* Slides rendered, but `ig_session.json` is missing. Run `--login` first.",
            )
            return False

        posted = publish_via_playwright(image_paths, caption)
        if posted:
            history = get_history()
            history.extend(new_hashes)
            save_history(history)
            print("✓ Deduplication history updated.")
            _send_telegram_message(
                cfg,
                "🎉 *PUBLISHED!* Your 6-slide FC dispatch has been fetched, rendered, and posted live to Instagram!",
            )
            print("\n🏆 Dispatch cycle complete!")
            return True

        _send_telegram_message(
            cfg,
            "⚠️ *PUBLISH FAILED:* Slides were rendered, but Instagram Playwright upload did not confirm completion. Check ig_session.json.",
        )
        print("\n⚠ Instagram upload did not confirm completion; history not marked as posted.")
        return False

    # Manual approval mode (--require-approval or AUTO_APPROVE=false)
    print("\n[4/4] Pushing approval package to your phone via Telegram...")
    send_approval_pack(custom_caption=caption)

    print("\n[5/5] Awaiting your tap on Telegram: [APPROVE] or [REJECT]...")
    approved = wait_for_approval()

    if approved is True:
        print("\n🎉 DISPATCH APPROVED ON MOBILE! Executing Instagram Publish...")
        posted = False
        if os.path.exists(SESSION_PATH):
            print("Publishing via saved Playwright browser session...")
            posted = publish_via_playwright(image_paths, caption)
            if posted:
                _send_telegram_message(
                    cfg,
                    "🎉 *SUCCESS!* Your 6-slide carousel has been published live to Instagram!",
                )
        else:
            print("⚠ Instagram session not yet connected. Run: python instagram_publisher.py --login")

        if posted:
            history = get_history()
            history.extend(new_hashes)
            save_history(history)
            print("✓ Deduplication history updated.")
            print("\n🏆 Daily dispatch complete!")
        return posted
    elif approved is False:
        print("\n❌ Dispatch was REJECTED from your phone. Nothing was posted.")
        return False
    else:
        print("\n⌛ Approval timed out.")
        return False


if __name__ == "__main__":
    if "--loop" in sys.argv:
        interval_seconds = int(os.environ.get("PUBLISH_INTERVAL_SECONDS", "1800"))
        print(f"⏱ 30-Minute Autonomous Publisher Loop Active (interval={interval_seconds}s)")
        while True:
            try:
                run_daily_dispatch()
            except Exception as exc:
                print(f"❌ Unexpected loop error: {exc}")
            print(f"💤 Sleeping {interval_seconds // 60} minutes until next Fetch -> Create -> Post cycle...")
            time.sleep(interval_seconds)
    else:
        run_daily_dispatch()
