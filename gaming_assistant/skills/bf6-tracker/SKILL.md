---
name: bf6-tracker
description: Track Battlefield 6 player statistics, combat performance, K/D ratios, weapon mastery, and class/kit breakdowns using Tracker.gg profile data.
---

# Battlefield 6 Stat Tracker

This skill empowers the agent to retrieve and analyze player statistics, combat efficiency, weapon masteries, and class performance in Battlefield 6.

## Identity & Friend Name Mappings
You can query players by their friendly nicknames or aliases without needing explicit platforms or IDs:
- **me**, **Alex** -> Steam ID `2770616530`
- **will**, **priesty** -> Steam ID `1002157303178`

- **Default Player ID:** `2770616530`
- **Default Platform:** `steam`
- If an alternative player ID or platform is specified, pass it explicitly.

## Capabilities & Metrics Tracked
1. **Combat Overview:**
   - Kills, Deaths, K/D Ratio, KDA Ratio, Kills per Minute (KPM), Kills per Match
   - Wins, Losses, Win %, Matches Played, Time Played
   - Score, Career Rank, Damage Dealt, Damage per Minute
   - Headshot %, Revives, Resupplies, Objectives Captured & Defended
2. **Class & Kit Performance:**
   - Assault, Engineer, Support, and Recon breakdown (Kills, Playtime, Score, KPM)
3. **Top Weapons:**
   - Most used weapons, kill counts, accuracy %, and headshot ratios

## Execution Workflow
When asked about Battlefield 6 stats, K/D, classes, weapon mastery, or playtime:
1. Run `scripts/fetch_bf6.py` via `run_skill_script`:
   - `args`: `{"profile_id": "<name/alias/ID or me>", "platform": "<platform or steam>"}`
2. Summarize the key metrics cleanly using Markdown tables or concise bullet points.
3. If the user asks for loadout recommendations, weapon comparisons, or tactical guides, use `google_search_agent` to retrieve up-to-date community weapon meta and class setups.
