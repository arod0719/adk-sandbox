---
name: battlefield-tracker
description: Track Battlefield series player statistics, combat performance, K/D ratios, weapon mastery, and class breakdowns across BF6, BF2042, BFV, BF1, BF4, and BF3 using the GameTools Network API. Defaults to BF6.
---

# Battlefield Stat Tracker (GameTools API)

This skill empowers the agent to retrieve and analyze player statistics, combat efficiency, weapon masteries, vehicle kills, and class performance across the Battlefield franchise (BF6, BF2042, BFV, BF1, BF4, and BF3) powered by the [GameTools Network API](https://api.gametools.network/docs#).

## Identity & Friend Name Mappings
You can query players by their friendly nicknames or aliases without needing explicit platforms:
- **me**, **Alex**, **karmajuney** -> `Karmajuney` (`platform: pc`)
- **will**, **priesty**, **itspriesty**, **pri3s7y** -> `pri3s7y` (`platform: pc`)

- **Default Player:** `Karmajuney`
- **Default Platform:** `pc`
- **Default Game:** `bf6`
- **Additional Users:** Any custom player can be queried by passing their username and platform (e.g. `pc`, `xbox`, `psn`).
- **Multi-Game Support:** Supports `bf6` (default), `bf2042`, `bfv`, `bf1`, `bf4`, and `bf3`. If no game is specified, it defaults to **BF6**.

## Capabilities & Metrics Tracked
1. **Combat Overview:**
   - Kills, Deaths, K/D Ratio, Infantry K/D, Human Kill % (filtering bot lobbies)
   - Kills per Minute (KPM), Kills per Match, Damage Dealt, Damage per Minute
   - Wins, Losses, Win %, Matches Played, Playtime
   - Headshot %, Accuracy %, Revives, Resupplies, Repairs
2. **Class & Kit Performance (BF6):**
   - Assault, Engineer, Support, and Recon breakdown (Kills, K/D, Playtime, KPM, and CDN icons)
3. **Top Weapons:**
   - Top 5 weapons, kill counts, accuracy %, headshots, KPM, and CDN weapon images
4. **Top Vehicles:**
   - Top 5 vehicles, vehicle kills, and vehicles destroyed

## Execution Workflow
When asked about Battlefield stats, K/D, classes, weapon mastery, or playtime:
1. Run `scripts/fetch_battlefield.py` via `run_skill_script`:
   - `args`: `{"player_name": "<name/alias or me>", "platform": "<platform or pc>", "game": "<game or bf6>"}`
2. Summarize key metrics cleanly using Markdown tables or concise bullet points.
3. If the user asks for loadout recommendations, weapon comparisons, or tactical guides, use `google_search_agent` to retrieve up-to-date community weapon meta and class setups.
