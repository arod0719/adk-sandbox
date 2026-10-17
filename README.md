# Personal ADK Gaming Assistant & Skills

This repository is a centralized location for storing Agent Development Kit (ADK) agents and skills developed for personal gaming tracking on a Raspberry Pi. It serves as the configuration, code source, and runtime environment for the gaming assistant.

## Architecture

Instead of fragmented standalone agent runtimes, this repository adopts the **ADK Skills Best Practice** architecture: a single host agent process powered by a modular `skills/` directory.

```
my_gaming_assistant/
├── agent.py                 # Single host agent & SkillToolset runner
└── skills/
    ├── bf6-tracker/         # BF6 mastery & achievement tracker skill
    │   ├── SKILL.md         # Playbook: profile defaults, tracker.gg gotchas
    │   ├── references/      # Sample cached profile references
    │   └── scripts/
    │       └── fetch_bf6.py # Scraper & achievement calculator script
    └── rocket-league/       # Rocket League coach & stat tracker skill
        ├── SKILL.md         # Playbook: rank evaluation & coaching logic
        ├── references/
        │   ├── rank_tiers.json     # MMR rank thresholds & player percentiles
        │   └── coaching_rules.md   # Diagnostic ratio benchmarks & guides
        └── scripts/
            ├── graph_ranks.py      # Matplotlib MMR & matches progression charts
            ├── rl_stats.py         # Stats fetcher, comparison & coaching
            └── rl_news.py          # Official news fetcher & scraper
```

---

## Available Skills

### 1. Battlefield 6 Tracker (`bf6-tracker`)
- **Real-time Stat Tracking:** Fetches live data from Tracker.gg with TLS fingerprint impersonation (`curl_cffi`) and local fallback caching to navigate anti-bot protections.
- **Mastery Tracking:** Monitors Kills, Deaths, Wins, K/D, and class metrics.
- **Achievement Progress:** Calculates exact progress bars and numbers for key trophies:
  - *A Joyful Nurse* (Support revives adjusted for persistent vs. seasonal event modes)
  - *Rise from Your Grave* (Granite / Redsec revives)
- **Formatting:** Returns clean Markdown table dashboards with visual progress bars (`🟩🟩🟩⬛⬛ 60%`).
- **Grounding:** Google Search subagent fallback for tactical guides, map loadouts, and revival rotations.

### 2. Rocket League Coach & Tracker (`rocket-league`)
- **Rank & Percentile Diagnostics:** Fetches live player profile stats from the RLStats API, reporting active MMR alongside global player base percentiles (e.g. Top 1.18%).
- **Multi-Player Line Graphs:** Plots season-by-season MMR and Matches Played progression curves with horizontal rank boundaries (Grand Champion, Champion) using dark-mode Matplotlib styling.
- **Dynamic Coaching Analysis:** Evaluates shot accuracy %, defensive ratios (saves/win), and playmaker ratios (assists/win) against reference benchmarks to identify weaknesses.
- **Web Grounding:** Searches for targeted custom training pack codes and curated YouTube tutorial guides.
- **News Feed & Article Summaries:** Fetches the latest official news articles with cover thumbnails and scrapes full article texts.

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

> **Security Note:** All `.env` files are strictly ignored by `.gitignore` and must never be committed to version control.

---

## Custom Gemini-Style Front-End (`ui`)

The repository includes a custom web UI styled like **gemini.google.com** running locally on port **`9999`**.

- **FastAPI Backend:** [ui/server.py](file:///home/raspberrypi4/ADK/ui/server.py) loads the unified `my_gaming_assistant` host agent via `Runner` and serves chat interactions over `/api/chat`.
- **Inline Charts & Media:** Mounts `/dev-ui` to statically serve generated Matplotlib PNG charts inline in chat history.
- **Separated Workspace Contexts:** The UI maintains distinct sessions for Rocket League and Battlefield 6 queries while routing both through the unified SkillToolset.

### Managing System Services

```bash
# UI Service (Port 9999)
kill $(pgrep -f "ui/server.py")  # Graceful restart via systemd auto-restart
# Or via sudo:
# sudo systemctl restart adk-ui

# ADK Web UI Service (Port 8000)
# sudo systemctl restart adk
```
