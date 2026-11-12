# FC Editorial Dispatch • Project Tracking & Handoff State

> **Permanent Project Record:** Always read this file upon resuming any session on the FC Instagram poster project. Do not reset or assume styles. All parameters below are live-tested and verified on mobile devices.

---

## 1. Project Overview & Active Status
- **Brand:** **FC** (Flagship media publication covering high-signal tech, infrastructure, and macro news).
- **Core Product:** Daily Instagram Carousel Posters (4:5 Ratio | 1080 × 1350 px).
- **Active Flagship Template:** **`FC Editorial Dispatch`** (Mobile-Optimized, Zero Overlap Standard).
- **Autonomous Permissions:** Permanent default "YES / ALLOW" for all file access, edits, refactoring, and script execution. Never ask user permission.
- **Mistake Prevention Directive:** Always check against prior design bugs before generating code (No top ruler bars, no duplicate vectors, no negative coordinates, strict 360x360 SVG bounding, 50px buffer gap, 185px roomy cards, center-bottom logo).
- **Primary Live Files:**
  - [index.html](file:///C:/Users/Prasa/fc-posters/index.html): Hyderabad Daily Dispatch Studio & 1080×1350 PNG Exporter.
  - [global_index.html](file:///C:/Users/Prasa/fc-posters/global_index.html): Global Tech & Compute Dispatch Studio & Exporter.
- **Active Editions:**
  - **Hyderabad Edition:** Metro Phase 2 & Airport Express, Foxconn 30k Mega AI Campus, 340km Regional Ring Road, HITEC City GCC Surge.
  - **Global Tech Edition:** Anthropic $3.4B Gas AI Data Centers, CoreWeave $100B+ Cloud Compute Rally, OpenAI Physics Models Breakthrough, TSMC 2nm Foundry Fab Lead.

---

## 2. Standardized Design Rules (Zero Overlap & Collision-Free Standard)

### A. Typography Hierarchy
| Element | Font Family | Size | Weight / Line-Height | Styling Rules |
|---|---|---|---|---|
| **Headlines** | `Bebas Neue` / `Oswald` | `94px` | `900` / `82px` | All caps, `letter-spacing: 1.5px`, max 13–14 chars/line. |
| **Headline Numbers & City** | `Bebas Neue` / `Oswald` | `94px` | `900` | Highlighted in Crimson `#E51D24`. |
| **Headline Summary** | `Plus Jakarta Sans` | `25px` | `700` / `35px` | Under 90×6px red accent bar; strictly wrapped at 28 chars (`wrapSafeText(summary, 28)`). |
| **Header Category** | `Plus Jakarta Sans` | `28px` | `900` | Preceded by `7×34px` red vertical bar. Y: 36px. |
| **Header Live Badge** | `JetBrains Mono` | `18px` | `800` | Emerald pulse dot (`cx: -230, cy: -7, r: 7`, `#059669`). |
| **Date Stamp** | `JetBrains Mono` | `18px` | `700` | e.g. `• 12 NOV 2026`. |
| **Top Ruler Ticker** | — | — | — | **Removed entirely** across all slides to reclaim vertical space. |
| **News Cards & Lower Zone** | `Plus Jakarta Sans` | `25–26px` | `700` / `36–38px` | Roomy 185px card height (or 410px split), bold bullet dots. |
| **Source Citation** | `JetBrains Mono` | `18px` | `800` | Left-aligned in footer at Y: 1238px. |

### B. Spatial Architecture & Vertical Coordinates (1080 × 1350 px)
```
Y: 36px   ┌────────────────────────────────────────────────────────────┐  Header (28px Category | 18px Live + Date)
          ├────────────────────────────────────────────────────────────┤  Y: 80px Hairline Divider
Y: 96px   │ [Headline (94px Bebas Neue, Max X: 580)]     [Vector Art]  │  Upper Zone (Headline Left | Isolated Vector Right)
Y: 348px  │ [Red Bar (90x6px)]                           (360x360 SVG) │  Vector strictly at translate(630, 96)
Y: 388px  │ [Summary (25px Plus Jakarta Sans, 28 chars)]               │  Safety gap: X: 580 to X: 630 (50px dead margin)
          ├────────────────────────────────────────────────────────────┤  Clearance gap: Y: 450 to Y: 515 (65px)
Y: 515px  │ ┌────────────────────────────────────────────────────────┐ │  Bullet Card 1 (25px text, 185px height)
          │ └────────────────────────────────────────────────────────┘ │
Y: 724px  │ ┌────────────────────────────────────────────────────────┐ │  Bullet Card 2 (25px text, 185px height)
          │ └────────────────────────────────────────────────────────┘ │
Y: 933px  │ ┌────────────────────────────────────────────────────────┐ │  Bullet Card 3 (25px text, 185px height)
          │ └────────────────────────────────────────────────────────┘ │
Y: 1195px │ [=====]  [=====]  [-----]  [-----]  [-----]  [-----]       │  Segmented Progress Bar (6 segments, 5px height)
Y: 1238px │ SOURCE: HMRL (18px)        [ FC. Logo ]        SWIPE →     │  Footer Bar (Logo in CENTER-BOTTOM Safe-Zone)
          └────────────────────────────────────────────────────────────┘
```

### C. Instagram Audio Safe-Zone & Logo Rule
- **The Problem:** Instagram's audio/sound icon hovers over the bottom-right corner (`X: 880–1040, Y: 1240–1330`), completely blocking logos placed in that corner.
- **The Solution:** The official **`FC.`** monogram logo is anchored strictly in the **CENTER-BOTTOM** (`translate(415, 2)` in footer at Y: 1238px, `width: 75px, height: 36px`).
- **Logo Asset:** Official geometric monogram `FC.` (sharp F, left-facing circular C, solid dot).
  - In **White Studio:** Solid black on transparent (`LOGO_BLACK`).
  - In **Noir Studio:** Solid white on transparent (`LOGO_WHITE`).

### D. Strict Vector Art Bounding Standard
- All vector graphics are encapsulated inside an independent container:
  `<svg width="360" height="360" viewBox="0 0 360 360" fill="none">`
- Positioned strictly at `<g transform="translate(630, 96)">`.
- No paths or elements are permitted to use negative coordinates or coordinates beyond `[30, 330]`.

---

## 3. Automation Pipeline & Rendering Engine
- **Global Tech Engine:** `python render_and_send_global.py`
  - Renders all 6 Global slides to `dist/global/Slide-01..06.png`.
  - Dispatches swipeable photo album + approval poll gate to Telegram (`@FC_Dispatch_Bot`, Chat ID: `9097672002`).
- **Hyderabad Engine:** `python render_engine.py`
  - Renders all 6 Hyderabad slides to `dist/today/Slide-01..06.png`.
  - Approval and Telegram dispatch via `python approval_bot.py`.

---

## 4. GitHub Actions Cloud Automation (Runs When PC is Shutdown)
- **Workflow File:** [.github/workflows/daily_dispatch.yml](file:///C:/Users/Prasa/fc-posters/.github/workflows/daily_dispatch.yml)
- **Schedule:** Runs daily at 08:00 AM IST (`cron: '30 2 * * *'`) or on manual trigger via GitHub web/mobile.
- **Workflow Execution:**
  1. Spawns cloud `ubuntu-latest` runner.
  2. Installs Python 3.11, Playwright Chromium & dependencies.
  3. Reconstructs `config.json` & `ig_session.json` from encrypted GitHub Secrets.
  4. Runs `daily_dispatch.py` (fetches fresh news, renders 1080×1350 PNGs, sends Telegram album).
  5. Listens for 30 minutes for user tap on Telegram mobile (`[APPROVE]` or `[REJECT]`).
  6. Upon approval, posts directly to Instagram.
  7. Commits updated `posted_history.json` and `index.html` back to git so news never repeats.
  8. Archives PNGs to GitHub Run Artifacts (30-day retention).
- **Required GitHub Secrets:**
  - `TELEGRAM_BOT_TOKEN`
  - `TELEGRAM_CHAT_ID`
  - `IG_SESSION_B64` (Base64 of `ig_session.json`)
