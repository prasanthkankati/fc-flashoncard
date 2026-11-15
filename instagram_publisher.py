import os
import json
import time
from pathlib import Path
import requests
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent.resolve()
CONFIG_PATH = str(BASE_DIR / "config.json")
SLIDES_DIR = str(BASE_DIR / "dist" / "today")
SESSION_PATH = str(BASE_DIR / "ig_session.json")

def load_config():
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}
    for key in ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "INSTAGRAM_POSTING_METHOD", "INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_ACCOUNT_ID"]:
        if os.environ.get(key):
            cfg[key] = os.environ[key]
    return cfg

# METHOD A: Meta Instagram Graph API
def publish_via_graph_api(image_urls, caption):
    """
    Publishes a carousel via Meta Graph API using public image URLs.
    Requires an Instagram Business Account connected to Facebook.
    """
    cfg = load_config()
    token = cfg.get("INSTAGRAM_ACCESS_TOKEN")
    ig_user_id = cfg.get("INSTAGRAM_ACCOUNT_ID")
    
    if not token or not ig_user_id:
        print("Graph API credentials missing in config.json.")
        return False
        
    print(f"Creating carousel containers on Instagram Graph API for {ig_user_id}...")
    item_container_ids = []
    
    for url in image_urls:
        res = requests.post(
            f"https://graph.facebook.com/v21.0/{ig_user_id}/media",
            data={
                "image_url": url,
                "is_carousel_item": "true",
                "access_token": token
            }
        ).json()
        item_id = res.get("id")
        if not item_id:
            print(f"Failed to create carousel item: {res}")
            return False
        item_container_ids.append(item_id)
        
    # Create Carousel Container
    carousel_res = requests.post(
        f"https://graph.facebook.com/v21.0/{ig_user_id}/media",
        data={
            "media_type": "CAROUSEL",
            "children": ",".join(item_container_ids),
            "caption": caption,
            "access_token": token
        }
    ).json()
    carousel_id = carousel_res.get("id")
    if not carousel_id:
        print(f"Failed to create carousel container: {carousel_res}")
        return False
        
    # Publish
    time.sleep(3)
    pub_res = requests.post(
        f"https://graph.facebook.com/v21.0/{ig_user_id}/media_publish",
        data={
            "creation_id": carousel_id,
            "access_token": token
        }
    ).json()
    
    post_id = pub_res.get("id")
    print(f"Successfully published carousel to Instagram! Post ID: {post_id}")
    return post_id

# METHOD B: Playwright Automated Web Publishing
def setup_instagram_session():
    """
    Opens a visible browser once so the user can log in to Instagram.
    Saves authentication cookies to ig_session.json for fully headless posting afterwards.
    """
    import base64
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            storage_state=SESSION_PATH if os.path.exists(SESSION_PATH) else None,
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()
        page.goto("https://www.instagram.com/")
        print("\n" + "="*60)
        print("A browser window has opened. Please log in to your Instagram account.")
        print("The script will automatically detect your login and save the session.")
        print("="*60 + "\n")

        # Loop checking for completed login (sessionid + home feed Create button)
        logged_in = False
        start_time = time.time()
        while time.time() - start_time < 300:  # 5 minute window
            try:
                cookies = context.cookies()
                cookie_names = [c["name"] for c in cookies]
                url_ok = all(
                    bad not in page.url
                    for bad in ["accounts/login", "auth_platform", "challenge", "emailsignup"]
                )
                has_create = page.locator("svg[aria-label='New post'], svg[aria-label='Create']").count() > 0
                if "sessionid" in cookie_names and url_ok and has_create:
                    logged_in = True
                    print("Authenticated home session detected! Finalizing login state...")
                    time.sleep(3)
                    break
            except Exception:
                pass
            time.sleep(1)

        if logged_in:
            context.storage_state(path=SESSION_PATH)
            with open(SESSION_PATH, "rb") as rf:
                b64_data = base64.b64encode(rf.read()).decode("ascii")
            with open(BASE_DIR / "ig_session_base64.txt", "w", encoding="utf-8") as wf:
                wf.write(b64_data)
            print(f"\n✔ Instagram session successfully saved to: {SESSION_PATH} (and ig_session_base64.txt)!")
        else:
            print("\n❌ Login timed out or cancelled.")

        browser.close()

def publish_via_playwright(image_paths, caption):
    """
    Headlessly uploads the carousel images and posts using the saved session.
    """
    if not os.path.exists(SESSION_PATH):
        print("Instagram session not found. Please run setup_instagram_session() first.")
        return False

    print("Launching Playwright to publish to Instagram...")
    confirmed = False
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context(
                storage_state=SESSION_PATH,
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            print("Navigating to Instagram...")
            page.goto("https://www.instagram.com/", wait_until="networkidle")
            time.sleep(3)

            if page.locator("input[name='username']").count() > 0 and page.locator("input[name='username']").first.is_visible():
                print("Instagram session is not authenticated (login form shown). Run --login to refresh ig_session.json.")
                return False

            # Dismiss any "Turn on Notifications" or "Save Info" dialogs if present
            for dismiss_text in ["Not Now", "Cancel"]:
                try:
                    btn = page.locator(f"button:has-text('{dismiss_text}')")
                    if btn.count() > 0 and btn.first.is_visible():
                        btn.first.click()
                        time.sleep(1)
                except Exception:
                    pass

            # 1. Verify authenticated UI & click Create / New Post button
            print("Clicking Create...")
            create_btn = page.locator("svg[aria-label='New post'], svg[aria-label='Create']").first
            try:
                create_btn.wait_for(state="visible", timeout=10000)
            except Exception:
                print(f"Create button not visible after 10s (current URL: {page.url}). Session may be expired or challenged.")
                return False
            create_btn.click()
            time.sleep(2)

            post_menu_item = page.locator(
                "span:text-is('Post'), a[role='link']:has-text('Post'), div[role='menuitem']:has-text('Post')"
            ).first
            if page.locator("input[type='file']").count() == 0 and post_menu_item.count() > 0 and post_menu_item.is_visible():
                post_menu_item.click()
                time.sleep(1.5)

            # 2. Upload the 6 images using file input
            print(f"Uploading {len(image_paths)} images...")
            file_input = page.locator("input[type='file']")
            if file_input.count() > 0:
                file_input.set_input_files(image_paths)
            else:
                with page.expect_file_chooser() as fc_info:
                    page.click("button:has-text('Select from computer')")
                fc_info.value.set_files(image_paths)

            time.sleep(3)

            # 3. Select 4:5 Portrait Aspect Ratio
            try:
                crop_btn = page.locator("svg[aria-label='Select crop']").first
                if crop_btn.is_visible():
                    crop_btn.click()
                    time.sleep(0.5)
                    ratio_4_5 = page.locator("button:has-text('4:5'), span:has-text('4:5')").first
                    if ratio_4_5.is_visible():
                        ratio_4_5.click()
                        time.sleep(0.5)
            except Exception as e:
                print(f"Note on crop selector: {e}")

            # 4. Click Next (Filters step)
            print("Moving to Next (Filters)...")
            next_btn = page.locator("div[role='button']:has-text('Next'), button:has-text('Next')").last
            next_btn.click(force=True)
            time.sleep(2)

            # 5. Click Next (Caption step)
            print("Moving to Next (Caption)...")
            next_btn = page.locator("div[role='button']:has-text('Next'), button:has-text('Next')").last
            next_btn.click(force=True)
            time.sleep(2)

            # 6. Fill Caption
            print("Writing caption...")
            caption_area = page.locator("div[aria-label='Write a caption...'], div[contenteditable='true']").first
            caption_area.click(force=True)
            caption_area.fill(caption)
            time.sleep(1.5)

            # 7. Click Share (use force=True and direct DOM dispatch to avoid overlay interception)
            print("Clicking Share...")
            share_btn = page.locator("div[role='button']:has-text('Share'), button:has-text('Share')").last
            try:
                share_btn.click(force=True, timeout=10000)
            except Exception:
                page.evaluate("""() => {
                    const els = Array.from(document.querySelectorAll('div[role="button"], button'));
                    const share = els.filter(e => e.innerText && e.innerText.trim() === 'Share');
                    if (share.length) share[share.length - 1].click();
                }""")

            # 8. Wait for upload confirmation
            print("Waiting for Instagram to process carousel...")
            confirm_locator = page.locator(
                "text='Your post has been shared.', svg[aria-label='Animated checkmark'], h3:has-text('Your post has been shared')"
            )
            for _ in range(35):
                time.sleep(2)
                if confirm_locator.count() > 0:
                    confirmed = True
                    print("✔ Confirmation received: Post successfully shared!")
                    break

            if not confirmed:
                print("❌ Upload confirmation not received within 70s timeout.")
            return confirmed
        except Exception as e:
            print(f"❌ Playwright Instagram publish error: {e}")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    import sys
    if "--login" in sys.argv:
        setup_instagram_session()
    else:
        print("Instagram Publisher Module Ready.")
