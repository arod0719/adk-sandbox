---
name: rocket-league
description: Track Rocket League player stats, rank distributions, season-by-season MMR and match progression charting, dynamic coaching analysis, and official news recaps.
---

# Rocket League Coach & Stat Tracker

This skill provides comprehensive statistical tracking, multi-player comparisons, season-by-season MMR progression line charts, dynamic playstyle coaching, and official game news.

## Identity & Profile Defaults
- **Identity Assumption:** If the user refers to themselves ("me", "my stats", "myself", "I", "my rank"), assume Steam user **`karmajuney`**.
- **Platform Default:** If a username is provided without a platform, assume **`steam`**.
- **Seasons Rule:** 
  - User-facing numbers (e.g. "Season 24", "Season 10") imply Free-to-Play seasons.
  - "OG", "legacy", or "first" seasons imply legacy seasons (`--is_legacy`).

## Reference Materials
- `references/rank_tiers.json`: Active MMR boundaries, divisions, and player base percentiles for all competitive and extra playlists.
- `references/coaching_rules.md`: Diagnostic rules for evaluating shot accuracy, defensive ratios, and playmaker stats.

## Execution Workflows

### 1. Stats & Player Comparison
To retrieve player rank, MMR, matches played, or compare two players:
- **Single Player:** Run `scripts/rl_stats.py` with `args={"action": "stats", "player": "<id>", "platform": "<platform>", "season": <season>}`.
- **Comparison:** Run `scripts/rl_stats.py` with `args={"action": "compare", "player": "<p1>", "platform": "<plat1>", "player2": "<p2>", "player2_platform": "<plat2>"}`.
- Always report the playlist percentile (e.g. "Top 1.18%") alongside rank and MMR.

### 2. Season Progression Graphing (Matplotlib Charts)
When asked to chart, plot, or visualize MMR or matches played across seasons:
1. Run `scripts/graph_ranks.py`:
   - `args`:
     - `gamemode`: target playlist (e.g. `"3v3"`, `"2v2"`, `"1v1"`, `"rumble"`, etc. Default: `"3v3"`).
     - `player`: primary player ID (e.g. `"karmajuney"`).
     - `players`: for multiple players, pass comma-separated `"player1:platform,player2:platform"`.
     - `metric`: `"mmr"` (default) or `"matches"`.
     - `limit_seasons`: optional integer (e.g. `5` for last 5 seasons).
     - `seasons`: optional season range string (e.g. `"10-15"`).
2. The script outputs a markdown image reference pointing to the local static asset (e.g. `![MMR Chart](/dev-ui/mmr_graph_1234567.png)`).
3. **MANDATORY:** Include this exact markdown image string in your response so the chart displays inline.

### 3. Dynamic Coaching Advice
When the user asks for coaching advice or how to rank up:
1. Run `scripts/rl_stats.py` with `args={"action": "coaching", "player": "<player>", "gamemode": "<gamemode>"}`.
2. Read `references/coaching_rules.md` to evaluate:
   - **Shot Accuracy %:** Below 40% (needs power shot packs) vs above 48% (clinical finisher).
   - **Defensive Ratios:** Saves per Win > 1.8 indicates player is trapped on defense / rotating too passively.
   - **Playmaking:** Assists per Win > 0.8 demonstrates backboard presence and center passes.
3. Call `google_search_agent` to retrieve 2-3 specific custom training pack codes for their rank and weakness (e.g. `"Rocket League Champion 3 shooting training pack codes"`).
4. Recommend curated YouTube video guides or tutorial titles matching their target gamemode.
5. Deliver a structured, encouraging coaching session report.

### 4. News & Patch Notes
- **Recap News:** Run `scripts/rl_news.py` with `args={"action": "list", "count": 5, "offset": 0}`. Output the returned text with embedded cover thumbnails inline.
- **Article Details:** Run `scripts/rl_news.py` with `args={"action": "details", "url": "<article_url>"}`.
