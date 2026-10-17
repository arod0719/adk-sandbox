# Personal ADK Gaming Assistant & Skills

This repository is a centralized location for storing Agent Development Kit (ADK) agents and skills developed for personal gaming tracking on a Raspberry Pi. It serves as the configuration, code source, and runtime environment for the gaming assistant.

## Architecture

Instead of fragmented standalone agent runtimes, this repository adopts the **ADK Skills Best Practice** architecture: a single host agent process powered by a modular `skills/` directory.

```
gaming_assistant/
├── __init__.py
├── agent.py                 # Single host agent & SkillToolset runner
└── skills/
    ├── bf6-tracker/         # BF6 combat & class/weapon stat tracker
    │   ├── SKILL.md
    │   ├── references/
    │   │   ├── friends.json         # Built-in player and friend IDs
    │   │   └── sample_profile.json
    │   └── scripts/
    │       └── fetch_bf6.py
    └── rocket-league/       # Rocket League coach & multi-player progression tracker
        ├── SKILL.md
        ├── references/
        │   ├── friends.json        # Built-in player and friend IDs
        │   ├── rank_tiers.json     # MMR rank thresholds & player percentiles
        │   └── coaching_rules.md   # Diagnostic ratio benchmarks & guides
        └── scripts/
            ├── graph_ranks.py      # Matplotlib MMR & matches progression charts
            ├── rl_stats.py         # Stats fetcher, comparison & coaching
            └── rl_news.py          # Official news fetcher & scraper
```

---

## Available Skills

### 1. Rocket League Coach & Tracker (`rocket-league`)
- **Native Friend & Identity Mappings:** Seamlessly recognizes nicknames without platform prompts:
  - `me` / `Alex` -> `karmajuney` (Steam)
  - `will` / `priesty` -> `itspriesty` (Steam)
  - `erik` / `rumble` -> `tweenty7` (Steam)
  - `david` -> `76561198053263580` (Steam ID64)
  - `emilio` / `flux` -> `FluxRL` (Steam)
- **Dynamic Season Detection:** Dynamically resolves the latest active season (e.g. Season 24 / API Season 38).
- **Natural Language & Multi-Player Graphing:** Supports queries like *"graph out my rank in ranked 2s for the last 5 seasons"* or *"compare me and itspriesty on steam's ranks in 2s for the last 4 seasons"*.
- **Rank & Percentile Diagnostics:** Reports MMR alongside global player base percentiles (e.g. Top 1.18%).
- **Coaching Engine:** Evaluates shot accuracy %, defensive ratios (saves/win), and playmaker ratios (assists/win) against reference benchmarks.
- **Web Grounding:** Searches for targeted custom training pack codes and curated YouTube tutorial guides.
- **News Feed & Article Summaries:** Fetches the latest official news articles with cover thumbnails and scrapes full article texts.

### 2. Battlefield 6 Tracker (`bf6-tracker`)
- **Native Friend & Identity Mappings:**
  - `me` / `Alex` -> `2770616530` (Steam)
  - `will` / `priesty` -> `1002157303178` (Steam)
- **Pure Combat & Mastery Stats:** Strictly tracks player combat metrics (K/D, KDA, Kills/Min, Win %, Damage/Min, Headshot %, Playtime, Score).
- **Class/Kit Mastery:** Assault, Engineer, Support, and Recon performance breakdowns.
- **Top Weapons:** Highlights top weapons with kill counts, accuracy percentages, and headshots.
- **Anti-Bot Navigation:** Utilizes TLS fingerprint impersonation (`curl_cffi`) and local fallback caching to navigate Cloudflare protection.

---

## Environment Configuration

Environment variables are standardized into a single unified `.env` file at the repository root. A `.env.example` template is provided:

```env
# Google Gemini API Key for Agent Development Kit (ADK)
GOOGLE_API_KEY=your_google_gemini_api_key_here
GOOGLE_GENAI_USE_VERTEXAI=False

# RLStats API Key for Rocket League statistics and leaderboards
RLSTATS_API_KEY=your_rlstats_api_key_here
```

---

## Custom Gemini-Style Front-End (`ui`)

The repository includes a custom web UI styled like **gemini.google.com** running locally on port **`9999`**.

- **FastAPI Backend:** [ui/server.py](file:///home/raspberrypi4/ADK/ui/server.py) loads the unified `gaming_assistant` host agent via `Runner` and serves chat interactions over `/api/chat`.
- **Inline Charts & Media:** Mounts `/dev-ui` to statically serve generated Matplotlib PNG charts inline in chat history.
- **Multi-Player Sessions:** Supports separate chat tab contexts while routing all queries through the unified host agent.
