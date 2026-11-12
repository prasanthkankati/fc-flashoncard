import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = str(BASE_DIR / "dist" / "today")
HTML_PATH = (BASE_DIR / "index.html").as_uri()

def render_all_slides():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Load main studio HTML to execute JavaScript state and SVG builder functions
        main_page = browser.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        
        print("Loading studio HTML...")
        main_page.goto(HTML_PATH, wait_until="networkidle")
        time.sleep(2)
        
        # Render all 6 slides in native 1080x1350 ultra-crisp resolution
        for i in range(6):
            print(f"Rendering Slide {i+1} of 6 (Native 1080×1350 HD)...")
            svg_string = main_page.evaluate(f"renderDispatchSlide({i})")
            
            # Render dedicated 1080x1350 frame with zero downscaling
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
            time.sleep(0.8) # Let fonts settle
            
            out_file = os.path.join(OUTPUT_DIR, f"Slide-0{i+1}.png")
            frame_page.screenshot(path=out_file, type="png")
            frame_page.close()
            print(f"Saved: {out_file} ({os.path.getsize(out_file):,} bytes)")
            
        main_page.close()
        browser.close()
        print(f"✓ All 6 slides successfully rendered to {OUTPUT_DIR} in razor-sharp 1080×1350 resolution!")

if __name__ == "__main__":
    render_all_slides()
