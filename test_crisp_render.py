import os
import base64
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "C:/Users/Prasa/fc-posters/dist/today"
HTML_PATH = "file:///C:/Users/Prasa/fc-posters/index.html"

def test_crisp():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 1080x1350 with high-DPI rendering
        page = browser.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        page.goto(HTML_PATH, wait_until="networkidle")
        time.sleep(2)
        
        # Test Slide 0 (Cover) and Slide 1
        for i in range(2):
            # Extract the raw SVG string from the page
            svg_string = page.evaluate(f"renderDispatchSlide({i})")
            
            # Create a clean page with ONLY this SVG at 1080x1350
            render_page = browser.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
            render_page.set_content(f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Plus+Jakarta+Sans:wght@500;600;700;800;900&family=JetBrains+Mono:wght@600;700;800&display=swap" rel="stylesheet">
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
            time.sleep(1) # Font layout
            
            out_file = os.path.join(OUTPUT_DIR, f"Slide-0{i+1}-CRISP.png")
            render_page.screenshot(path=out_file, type="png")
            render_page.close()
            print(f"Saved crisp render: {out_file} (Size: {os.path.getsize(out_file)} bytes)")
            
        browser.close()

if __name__ == "__main__":
    test_crisp()
