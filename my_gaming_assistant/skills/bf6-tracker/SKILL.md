---
name: bf6-tracker
description: Track Battlefield 6 stats, weapon/class mastery, and calculate progress toward final achievements (A Joyful Nurse and Rise from Your Grave) using Tracker.gg data.
---

# Battlefield 6 Achievement Coach & Tracker

This skill empowers the agent to track player statistics, analyze class and weapon mastery, and compute exact progress toward target trophies and achievements in Battlefield 6.

## Identity & Profile Defaults
- **Default User ID:** `2770616530`
- **Default Platform:** `steam`
- If the user specifies an alternative player ID or platform (e.g. Origin/EA, PSN, Xbox), pass those explicitly into the script arguments.

## Tracker.gg Gotchas & Data Rules
1. **Cloudflare & API Throttling:** Tracker.gg employs strict anti-bot and rate-limiting measures. The deterministic script `scripts/fetch_bf6.py` uses TLS fingerprint impersonation (`curl_cffi`) and maintains a local cache to prevent 403 errors.
2. **Segment Isolation (True Totals):** Kit and class statistics in Tracker.gg track standard Multiplayer and Casual PvE modes, but do not count Granite/Redsec revives.
3. **"A Joyful Nurse" Achievement Logic:**
   - Requires Support kit revives in persistent multiplayer modes (Target: `1996`).
   - Seasonal/event revives (e.g. Operation Angur) are included in overall multiplayer (`gm_mp`) but NOT in persistent modes. The script subtracts these temporary revives to compute the exact achievement count.
4. **"Rise from Your Grave" Achievement Logic:**
   - Requires Granite / Redsec mode revives (Target: `1988`).
   - Tracked strictly by the `gm_granite` gamemode segment.

## Execution Workflows

### 1. Checking Achievement Progress
When the user asks about achievement progress, trophies, or the "Final Push":
1. Run the script via `run_skill_script`:
   - `skill_name`: `"bf6-tracker"`
   - `file_path`: `"scripts/fetch_bf6.py"`
   - `args`: `{"action": "achievements", "profile_id": "<ID or 2770616530>", "platform": "<platform or steam>"}`
2. Parse the returned JSON payload.
3. Format the response as a **Markdown Dashboard Table**:
   | Target Achievement | Progress Meter | Numbers | Status |
   | :--- | :--- | :--- | :--- |
   | **A Joyful Nurse** | 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% | 2670 / 1996 (Completed!) | 🏆 Completed |
   | **Rise from Your Grave** | 🟩🟩🟩🟩🟩🟩🟩🟩⬛⬛ 88% | 1766 / 1988 | 🔄 In Progress |
4. Follow the table with concise, motivational coaching advice on the remaining requirement.

### 2. Checking General Stats & Mastery
When the user asks about kills, deaths, K/D ratio, wins, time played, or weapon/class mastery:
1. Run the script via `run_skill_script`:
   - `skill_name`: `"bf6-tracker"`
   - `file_path`: `"scripts/fetch_bf6.py"`
   - `args`: `{"action": "stats", "profile_id": "<ID>", "platform": "<platform>"}`
2. Present the key combat metrics cleanly (K/D, Kills/Min, Win %, Damage/Match).

### 3. Tactical Guides & Search Grounding
If the user asks for strategies, optimal loadouts, map revive rotations, or gameplay tips to complete their revives, call the `google_search_agent` tool to retrieve the latest community guides and summarize the best tactics.
