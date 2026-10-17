#!/usr/bin/env python3
"""
Deterministic stats retrieval, player comparison, and coaching ratio evaluator for Rocket League.
Interacts with the RLStats API and references/rank_tiers.json.
"""

import os
import sys
import json
import argparse
from pathlib import Path
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

def get_rank_name_from_mmr(mmr: float, playlist_key: str):
    tiers_path = get_rank_tiers_path()
    if not tiers_path or not tiers_path.exists():
        return ("Unknown", "N/A")
    try:
        with open(tiers_path, "r", encoding="utf-8") as f:
            brain_data = json.load(f)
        ranges = brain_data.get(playlist_key, brain_data.get("3v3", []))
        for rank in ranges:
            if rank["min_mmr"] <= mmr <= rank["max_mmr"]:
                return (rank["name"], f"{rank['percent']}%")
        return ("Unranked", "N/A")
    except Exception:
        return ("Unknown", "N/A")

def fetch_player_data(player_id: str, platform: str = "steam") -> dict:
    plat_id = PLATFORM_MAP.get(platform.lower())
    if not plat_id:
        raise ValueError(f"Invalid platform '{platform}'. Choose from: {list(PLATFORM_MAP.keys())}")

    url = "https://api.rlstats.net/v1/profile/stats"
    r = requests.post(url, json={"apikey": API_KEY, "platformid": plat_id, "playerid": player_id}, timeout=10)
    r.raise_for_status()
    data = r.json()
    if not data or data.get("Message") == "Not Found":
        raise ValueError(f"Player '{player_id}' not found on {platform}.")
    return data

def parse_season_stats(data: dict, platform: str, season: int = None, is_legacy: bool = False) -> dict:
    if season is None:
        target_api_season = str(data.get("SeasonInfo", {}).get("SeasonID", "37"))
        api_season_val = int(target_api_season)
        if api_season_val > F2P_SEASON_OFFSET:
            season_display = f"Season {api_season_val - F2P_SEASON_OFFSET}"
        else:
            season_display = f"OG Season {api_season_val}"
    else:
        if is_legacy:
            target_api_season = str(season)
            season_display = f"OG Season {season}"
        else:
            target_api_season = str(season + F2P_SEASON_OFFSET)
            season_display = f"Season {season}"

    ranked_seasons = data.get("RankedSeasons", {})
    if target_api_season not in ranked_seasons:
        raise ValueError(f"Stats for {season_display} not found.")

    season_data = ranked_seasons[target_api_season]
    overall_stats = season_data.get("Stats", {})
    wins = overall_stats.get("Wins", 0)
    goals = overall_stats.get("Goals", 0)
    assists = overall_stats.get("Assists", 0)
    saves = overall_stats.get("Saves", 0)
    shots = overall_stats.get("Shots", 0)
    mvps = overall_stats.get("MVPs", 0)

    shot_accuracy = round((goals / shots * 100), 1) if shots > 0 else 0.0
    saves_per_win = round((saves / wins), 2) if wins > 0 else 0.0
    assists_per_win = round((assists / wins), 2) if wins > 0 else 0.0
    goals_per_win = round((goals / wins), 2) if wins > 0 else 0.0

    playlists = []
    for playlist_id, playlist_name in PLAYLIST_MAP.items():
        pd = season_data.get(playlist_id)
        if pd:
            skill_rating = pd.get("SkillRating", 0)
            matches = pd.get("MatchesPlayed", 0)
            winstreak = pd.get("WinStreak", 0)
            if skill_rating > 100 or matches > 0:
                key = PLAYLIST_MMR_KEY_MAP.get(playlist_id, "3v3")
                rank_name, percent = get_rank_name_from_mmr(skill_rating, key)
                playlists.append({
                    "playlist": playlist_name,
                    "rank": rank_name,
                    "mmr": skill_rating,
                    "percentile": f"Top {percent}" if percent != "N/A" else "N/A",
                    "matches": matches,
                    "winstreak": winstreak
                })

    return {
        "display_name": data.get("DisplayName", "Unknown"),
        "platform": platform,
        "season_display": season_display,
        "metrics": {
            "wins": wins,
            "goals": goals,
            "assists": assists,
            "saves": saves,
            "shots": shots,
            "mvps": mvps,
            "shot_accuracy": shot_accuracy,
            "saves_per_win": saves_per_win,
            "assists_per_win": assists_per_win,
            "goals_per_win": goals_per_win
        },
        "playlists": playlists
    }

def get_coaching_payload(data: dict, gamemode: str = "3v3", season: int = None, is_legacy: bool = False) -> dict:
    gamemode = gamemode if gamemode in ["1v1", "2v2", "3v3"] else "3v3"
    playlist_id = "10" if gamemode == "1v1" else ("11" if gamemode == "2v2" else "13")
    playlist_name = "Duel (1v1)" if gamemode == "1v1" else ("Doubles (2v2)" if gamemode == "2v2" else "Standard (3v3)")

    parsed = parse_season_stats(data, platform="steam", season=season, is_legacy=is_legacy)
    playlist_entry = next((p for p in parsed["playlists"] if p["playlist"] == playlist_name), None)

    current_rank = playlist_entry["rank"] if playlist_entry else "Unranked"
    percentile = playlist_entry["percentile"] if playlist_entry else "N/A"
    mmr = playlist_entry["mmr"] if playlist_entry else 0
    matches = playlist_entry["matches"] if playlist_entry else 0

    return {
        "player": parsed["display_name"],
        "gamemode": gamemode,
        "current_rank": current_rank,
        "rank_percentile": percentile,
        "mmr": mmr,
        "matches_played": matches,
        "metrics": parsed["metrics"]
    }

def main():
    parser = argparse.ArgumentParser(description="Fetch Rocket League Stats, Compare, and Coaching Analysis")
    parser.add_argument("--action", choices=["stats", "compare", "coaching"], default="stats", help="Action")
    parser.add_argument("--player", default="karmajuney", help="Player ID/Username")
    parser.add_argument("--platform", default="steam", help="Platform (steam, ps4, xbox, switch, epic)")
    parser.add_argument("--season", type=int, help="Season number (F2P default, or OG if is_legacy)")
    parser.add_argument("--is_legacy", action="store_true", help="Query legacy OG seasons")
    parser.add_argument("--player2", help="Second player for comparison")
    parser.add_argument("--player2_platform", default="steam", help="Platform for second player")
    parser.add_argument("--gamemode", default="3v3", choices=["1v1", "2v2", "3v3"], help="Gamemode for coaching")
    args = parser.parse_args()

    try:
        if args.action == "stats":
            data = fetch_player_data(args.player, args.platform)
            parsed = parse_season_stats(data, args.platform, season=args.season, is_legacy=args.is_legacy)
            print(json.dumps(parsed, indent=2))

        elif args.action == "compare":
            if not args.player2:
                raise ValueError("--player2 is required for comparison.")
            d1 = fetch_player_data(args.player, args.platform)
            d2 = fetch_player_data(args.player2, args.player2_platform)
            p1 = parse_season_stats(d1, args.platform, season=args.season, is_legacy=args.is_legacy)
            p2 = parse_season_stats(d2, args.player2_platform, season=args.season, is_legacy=args.is_legacy)
            output = {
                "player_1": p1,
                "player_2": p2
            }
            print(json.dumps(output, indent=2))

        elif args.action == "coaching":
            data = fetch_player_data(args.player, args.platform)
            coaching = get_coaching_payload(data, gamemode=args.gamemode, season=args.season, is_legacy=args.is_legacy)
            print(json.dumps(coaching, indent=2))

    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
