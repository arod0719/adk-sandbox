#!/usr/bin/env python3
"""
Deterministic graphing script for Rocket League MMR and Match progression across seasons.
Generates dark-mode charts with rank threshold lines and outputs markdown image references.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import requests
from dotenv import load_dotenv

# Load environment variables safely
for env_path in [
    Path("/home/raspberrypi4/ADK/.env"),
    Path("/home/raspberrypi4/ADK/rocket_league/.env"),
    Path.cwd() / ".env"
]:
    if env_path.exists():
        load_dotenv(env_path)

API_KEY = os.getenv("RLSTATS_API_KEY")

PLATFORM_MAP = {
    "steam": 1,
    "ps4": 2,
    "xbox": 3,
    "switch": 4,
    "epic": 5
}

PLAYLIST_MAP = {
    "0": "Unranked",
    "10": "Duel (1v1)",
    "11": "Doubles (2v2)",
    "12": "Solo Standard",
    "13": "Standard (3v3)",
    "27": "Hoops",
    "28": "Rumble",
    "29": "Dropshot",
    "30": "Snow Day",
    "34": "Tournament",
    "61": "Chaos (4v4)",
    "63": "Heatseeker"
}

PLAYLIST_MMR_KEY_MAP = {
    "10": "1v1",
    "11": "2v2",
    "13": "3v3",
    "27": "hoops",
    "28": "rumble",
    "29": "dropshot",
    "30": "snowday",
    "34": "tournament",
    "61": "4v4",
    "63": "heatseeker"
}

GAMEMODE_TO_PLAYLIST_ID = {
    "1v1": "10", "duel": "10", "duel1v1": "10", "solo": "10",
    "2v2": "11", "doubles": "11", "doubles2v2": "11", "standard2v2": "11",
    "3v3": "13", "standard": "13", "standard3v3": "13",
    "hoops": "27",
    "rumble": "28",
    "dropshot": "29",
    "snowday": "30",
    "tournament": "34",
    "quads": "61", "chaos": "61", "chaos4v4": "61", "4v4": "61",
    "heatseeker": "63"
}

F2P_SEASON_OFFSET = 14

def get_rank_tiers_path() -> Path:
    candidates = [
        Path("references/rank_tiers.json"),
        Path(__file__).parent.parent / "references" / "rank_tiers.json",
        Path("/home/raspberrypi4/ADK/my_gaming_assistant/skills/rocket-league/references/rank_tiers.json"),
        Path("/home/raspberrypi4/ADK/rocket_league/brain/rank_ranges.json")
    ]
    for p in candidates:
        if p.exists():
            return p
    return None

def get_rank_lines_for_chart(gamemode: str, min_m: int, max_m: int):
    tiers_path = get_rank_tiers_path()
    marks = []
    if tiers_path and tiers_path.exists():
        try:
            with open(tiers_path, "r", encoding="utf-8") as f:
                brain_data = json.load(f)
            ranges = brain_data.get(gamemode, [])
            for rank in ranges:
                threshold = rank["min_mmr"]
                if min_m <= threshold <= max_m:
                    marks.append((threshold, rank["name"]))
        except Exception:
            pass
    return sorted(marks)

def parse_seasons_string(seasons_str: str) -> list:
    if not seasons_str:
        return []
    seasons = set()
    parts = [p.strip() for p in seasons_str.split(",") if p.strip()]
    for part in parts:
        if "-" in part:
            subparts = [sp.strip() for sp in part.split("-") if sp.strip()]
            if len(subparts) == 2:
                try:
                    start, end = int(subparts[0]), int(subparts[1])
                    if start <= end:
                        seasons.update(range(start, end + 1))
                    else:
                        seasons.update(range(end, start + 1))
                except ValueError:
                    pass
        else:
            try:
                seasons.add(int(part))
            except ValueError:
                pass
    return sorted(list(seasons))

def cleanup_old_charts(directories: list[Path]):
    now = time.time()
    for directory in directories:
        if directory.exists():
            for f in directory.glob("mmr_graph_*.png"):
                try:
                    if now - f.stat().st_mtime > 600:
                        f.unlink()
                except Exception:
                    pass

def fetch_player_raw_stats(player_id: str, platform: str) -> dict:
    plat_id = PLATFORM_MAP.get(platform.lower(), 1)
    url = "https://api.rlstats.net/v1/profile/stats"
    r = requests.post(url, json={"apikey": API_KEY, "platformid": plat_id, "playerid": player_id}, timeout=10)
    r.raise_for_status()
    return r.json()

def generate_graph(gamemode: str = "3v3", players: list[dict] = None, metric: str = "mmr", seasons_str: str = None, limit_seasons: int = None) -> str:
    if not players:
        players = [{"player_id": "karmajuney", "platform": "steam"}]

    gamemode_clean = gamemode.lower().replace(" ", "").replace("(", "").replace(")", "")
    playlist_id = GAMEMODE_TO_PLAYLIST_ID.get(gamemode_clean, "13")
    playlist_name = PLAYLIST_MAP.get(playlist_id, gamemode.upper())
    playlist_mmr_key = PLAYLIST_MMR_KEY_MAP.get(playlist_id, "3v3")

    player_datasets = []
    for p in players:
        p_id = p.get("player_id")
        p_platform = p.get("platform", "steam").lower()
        if not p_id:
            continue

        try:
            p_data = fetch_player_raw_stats(p_id, p_platform)
        except Exception:
            continue

        if not p_data or p_data.get("Message") == "Not Found":
            continue

        p_seasons = []
        p_values = []
        display_name = p_data.get("DisplayName", p_id)

        for api_season, season_data in p_data.get("RankedSeasons", {}).items():
            pd = season_data.get(playlist_id)
            if pd:
                skill_rating = pd.get("SkillRating", 0)
                matches = pd.get("MatchesPlayed", 0)
                val = skill_rating if metric == "mmr" else matches

                if matches > 0 or skill_rating > 100:
                    f2p_season = int(api_season) - F2P_SEASON_OFFSET
                    p_seasons.append(f2p_season)
                    p_values.append(val)

        if p_seasons:
            sorted_points = sorted(zip(p_seasons, p_values))
            if seasons_str:
                target_seasons = parse_seasons_string(seasons_str)
                if target_seasons:
                    sorted_points = [pt for pt in sorted_points if pt[0] in target_seasons]
            elif limit_seasons and limit_seasons > 0:
                sorted_points = sorted_points[-limit_seasons:]

            if sorted_points:
                player_datasets.append({
                    "display_name": display_name,
                    "points": sorted_points
                })

    if not player_datasets:
        return f"No historical stats found in {playlist_name} for the specified players/seasons."

    all_seasons = set()
    all_vals = []
    for dataset in player_datasets:
        for s, v in dataset["points"]:
            all_seasons.add(s)
            all_vals.append(v)

    combined_seasons = sorted(list(all_seasons))
    min_val, max_val = min(all_vals), max(all_vals)

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=120)
    fig.patch.set_facecolor("#121212")
    ax.set_facecolor("#1a1a1a")

    colors = ["#00e5ff", "#ff9100", "#00e676", "#d500f9", "#ffea00", "#ff1744"]
    markers = ["o", "x", "^", "s", "D", "v"]

    for i, dataset in enumerate(player_datasets):
        p_x = [pt[0] for pt in dataset["points"]]
        p_y = [pt[1] for pt in dataset["points"]]
        p_color = colors[i % len(colors)]
        p_marker = markers[i % len(markers)]

        ax.plot(p_x, p_y, marker=p_marker, color=p_color, linewidth=2.5, markersize=7, label=dataset["display_name"])

        if len(player_datasets) <= 2:
            offset = 10 if i == 0 or len(player_datasets) == 1 else -15
            anno_color = "#ffffff" if len(player_datasets) == 1 else p_color
            for s, v in dataset["points"]:
                ax.annotate(f"{v}", (s, v), textcoords="offset points", xytext=(0, offset), ha="center", fontweight="bold", color=anno_color, fontsize=8)

    if metric == "mmr":
        rank_marks = get_rank_lines_for_chart(playlist_mmr_key, min_val - 80, max_val + 80)
        for threshold, rank_name in rank_marks:
            ax.axhline(y=threshold, color="#ff007f", linestyle=":", linewidth=1.5, alpha=0.8)
            ax.text(combined_seasons[0], threshold + 8, f"{rank_name} Bound ({threshold} MMR)", color="#ff007f", alpha=0.85, fontsize=8, fontweight="bold")

    metric_label = "MMR" if metric == "mmr" else "Matches Played"
    playlist_name_clean = playlist_name.replace("(", "").replace(")", "")
    title_players = " vs ".join([d["display_name"] for d in player_datasets])
    ax.set_title(f"{metric_label.upper()} {playlist_name_clean.upper()}:\n{title_players}", fontsize=11, fontweight="bold", pad=25)
    ax.set_xlabel("Season", fontsize=10, labelpad=10)
    ax.set_ylabel(metric_label, fontsize=10, labelpad=10)

    ax.set_xticks(combined_seasons)
    ax.set_xticklabels([f"S{s}" for s in combined_seasons])
    ax.grid(True, linestyle="--", alpha=0.2, color="#ffffff")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=3, borderaxespad=0, frameon=False, fontsize=9)

    plt.tight_layout()

    timestamp = int(time.time())
    filename = f"mmr_graph_{timestamp}.png"

    # Save to UI static directories
    target_dirs = [
        Path("/home/raspberrypi4/ADK/ui/static"),
        Path("/home/raspberrypi4/ADK/ui/templates/static")
    ]
    try:
        import google.adk
        adk_dir = Path(google.adk.__file__).parent
        browser_dir = adk_dir / "cli" / "browser"
        if browser_dir.exists():
            target_dirs.append(browser_dir)
    except Exception:
        pass

    cleanup_old_charts(target_dirs)

    for d in target_dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
            plt.savefig(d / filename, format="png", facecolor=fig.get_facecolor(), edgecolor="none")
        except Exception:
            pass

    plt.close(fig)

    static_url = f"/dev-ui/{filename}"
    return f"![MMR Chart]({static_url})\n\n*Saved chart `{filename}` for {playlist_name} ({metric_label})*"

def main():
    parser = argparse.ArgumentParser(description="Generate Rocket League Rank & MMR Line Graphs")
    parser.add_argument("--gamemode", default="3v3", help="Gamemode (1v1, 2v2, 3v3, hoops, rumble, dropshot, etc.)")
    parser.add_argument("--player", default="karmajuney", help="Primary player username / ID")
    parser.add_argument("--platform", default="steam", help="Primary player platform")
    parser.add_argument("--players", help="Comma-separated player list in format 'id:platform,id2:platform2'")
    parser.add_argument("--metric", choices=["mmr", "matches"], default="mmr", help="Metric to plot")
    parser.add_argument("--seasons", help="Season range (e.g. '10-15' or '1,3,5')")
    parser.add_argument("--limit_seasons", type=int, help="Limit to last N seasons")
    args = parser.parse_args()

    players_list = []
    if args.players:
        for entry in args.players.split(","):
            if ":" in entry:
                pid, plat = entry.split(":", 1)
                players_list.append({"player_id": pid.strip(), "platform": plat.strip()})
            else:
                players_list.append({"player_id": entry.strip(), "platform": "steam"})
    else:
        players_list.append({"player_id": args.player, "platform": args.platform})

    try:
        result = generate_graph(
            gamemode=args.gamemode,
            players=players_list,
            metric=args.metric,
            seasons_str=args.seasons,
            limit_seasons=args.limit_seasons
        )
        print(result)
    except Exception as e:
        print(f"Error generating chart: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
