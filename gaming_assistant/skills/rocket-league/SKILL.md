---
name: rocket-league
description: Track Rocket League player stats, rank distributions, season-by-season MMR and match progression charting, dynamic coaching analysis, and official news recaps.
---

# Rocket League Coach & Stat Tracker

This skill provides comprehensive statistical tracking, multi-player comparisons, season-by-season MMR progression line charts, dynamic playstyle coaching, and official game news.

## Identity & Friend Name Mappings
You can query players by their friendly nicknames or aliases without needing explicit platforms or IDs:
- **me**, **Alex** -> Steam `karmajuney`
- **will**, **priesty** -> Steam `itspriesty`
- **erik**, **rumble** -> Steam `tweenty7`
- **david** -> Steam ID64 `76561198053263580`
- **emilio**, **flux** -> Steam `FluxRL`

If the user refers to themselves ("me", "my rank", "I"), default to **`karmajuney`** on **`steam`**.
If any other username is specified without a platform, assume **`steam`** by default.

## Season Handling
- Always defaults to the **latest active season** dynamically from the API (currently Season 24 / Season ID 38).
- User numbers ("Season 24", "Season 10") imply Free-to-Play seasons.
- "OG", "legacy", or "first" seasons imply legacy seasons (`--is_legacy`).

## Execution Workflows

### 1. Stats & Player Comparison
- **Single Player:** Run `scripts/rl_stats.py` with `args={"action": "stats", "player": "<name/alias/ID>", "platform": "<platform>", "season": <season>}`.
- **Comparison:** Run `scripts/rl_stats.py` with `args={"action": "compare", "player": "<p1>", "player2": "<p2>", "platform": "<plat1>", "player2_platform": "<plat2>"}`.
  - Supports friendly names: e.g. `player="me"`, `player2="will"`.
- Always report the playlist percentile (e.g. "Top 1.18%") alongside rank and MMR.

### 2. Season Progression Graphing (Matplotlib Charts)
When asked to chart, plot, compare, or visualize MMR or matches played across seasons (e.g. *"graph out my rank in ranked 2s for the last 5 seasons"*, *"compare me and itspriesty on steam in 2s for the last 4 seasons"*):
1. Run `scripts/graph_ranks.py` with:
   - `gamemode`: Playlist or natural alias (e.g. `"2s"`, `"ranked 2s"`, `"2v2"`, `"3v3"`, `"3s"`, `"1s"`, `"rumble"`, `"hoops"`).
   - `players`: Can be a list of player dicts, comma-separated names (e.g. `"me,will"` or `"karmajuney:steam,itspriesty:steam"`), or pass `player="me"` and `player2="will"`.
   - `metric`: `"mmr"` (default) or `"matches"`.
   - `limit_seasons`: Count of seasons if specified (e.g. `5` for "last 5 seasons", `4` for "last 4 seasons").
   - `seasons`: Season range string if specified (e.g. `"10-15"`).
2. The script outputs a markdown image reference pointing to the local static asset (e.g. `![MMR Chart](/dev-ui/mmr_graph_TIMESTAMP.png)`).
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
