#!/usr/bin/env python3
"""
Deterministic stats retrieval, player comparison, and coaching ratio evaluator for Rocket League.
Interacts with the RLStats API and references/rank_tiers.json.
Supports friend name resolution, dynamic latest season detection, and gamemode aliases.
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

GAMEMODE_ALIAS_MAP = {
    "1v1": "10", "1s": "10", "ranked1s": "10", "duel": "10", "duel1v1": "10", "solo": "10", "ones": "10",
    "2v2": "11", "2s": "11", "ranked2s": "11", "doubles": "11", "doubles2v2": "11", "twos": "11",
    "3v3": "13", "3s": "13", "ranked3s": "13", "standard": "13", "standard3v3": "13", "threes": "13",
    "hoops": "27", "dunk": "27",
    "rumble": "28", "rng": "28",
    "dropshot": "29", "drop": "29",
    "snowday": "30", "hockey": "30",
    "tournament": "34", "tourney": "34",
    "quads": "61", "chaos": "61", "4v4": "61", "4s": "61",
    "heatseeker": "63"
}

F2P_SEASON_OFFSET = 14

PLAYER_NAME_MAPPINGS = {
    "me": {"player_id": "karmajuney", "platform": "steam"},
    "alex": {"player_id": "karmajuney", "platform": "steam"},
    "karmajuney": {"player_id": "karmajuney", "platform": "steam"},
    "will": {"player_id": "itspriesty", "platform": "steam"},
    "priesty": {"player_id": "itspriesty", "platform": "steam"},
    "itspriesty": {"player_id": "itspriesty", "platform": "steam"},
    "erik": {"player_id": "tweenty7", "platform": "steam"},
    "rumble": {"player_id": "tweenty7", "platform": "steam"},
    "tweenty7": {"player_id": "tweenty7", "platform": "steam"},
    "david": {"player_id": "76561198053263580", "platform": "steam"},
    "76561198053263580": {"player_id": "76561198053263580", "platform": "steam"},
    "emilio": {"player_id": "FluxRL", "platform": "steam"},
    "flux": {"player_id": "FluxRL", "platform": "steam"},
    "fluxrl": {"player_id": "FluxRL", "platform": "steam"}
}

def resolve_player(raw_id: str, raw_platform: str = "steam") -> tuple[str, str]:
    clean_id = raw_id.strip().lower()
    if clean_id in PLAYER_NAME_MAPPINGS:
        mapping = PLAYER_NAME_MAPPINGS[clean_id]
        return mapping["player_id"], mapping["platform"]
    return raw_id.strip(), (raw_platform.strip().lower() if raw_platform else "steam")

def get_rank_tiers_path() -> Path:
    candidates = [
        Path("references/rank_tiers.json"),
        Path(__file__).parent.parent / "references" / "rank_tiers.json",
        Path("/home/raspberrypi4/ADK/gaming_assistant/skills/rocket-league/references/rank_tiers.json")
    ]
    for p in candidates:
        if p.exists():
            return p
    return None

TIER_NAMES = [
    "Unranked",
    "Bronze I", "Bronze II", "Bronze III",
    "Silver I", "Silver II", "Silver III",
    "Gold I", "Gold II", "Gold III",
    "Platinum I", "Platinum II", "Platinum III",
    "Diamond I", "Diamond II", "Diamond III",
    "Champion I", "Champion II", "Champion III",
    "Grand Champion I", "Grand Champion II", "Grand Champion III",
    "Supersonic Legend"
]

def get_percent_for_tier(playlist_key: str, rank_name: str) -> str:
    tiers_path = get_rank_tiers_path()
    if not tiers_path or not tiers_path.exists():
        return "N/A"
    try:
        with open(tiers_path, "r", encoding="utf-8") as f:
            brain_data = json.load(f)
        ranges = brain_data.get(playlist_key, brain_data.get("3v3", []))
        for r in ranges:
            if r.get("name") == rank_name:
                return f"{r.get('percent', 'N/A')}%"
    except Exception:
        pass
    return "N/A"

def get_rank_name_from_mmr(mmr: float, playlist_key: str):
    tiers_path = get_rank_tiers_path()
    if not tiers_path or not tiers_path.exists():
        return ("Unknown", "N/A")
    try:
        with open(tiers_path, "r", encoding="utf-8") as f:
            brain_data = json.load(f)
        ranges = brain_data.get(playlist_key, brain_data.get("3v3", []))
        # Check from highest to lowest rank
        for rank in reversed(ranges):
            divs = rank.get("divisions", {})
            if divs:
                for d_key, d_label in [("div_4", "Div IV"), ("div_3", "Div III"), ("div_2", "Div II"), ("div_1", "Div I")]:
                    interval = divs.get(d_key)
                    if interval and interval[0] <= mmr <= interval[1]:
                        return (f"{rank['name']} ({d_label})", f"{rank['percent']}%")
            elif rank.get("min_mmr", 0) <= mmr <= rank.get("max_mmr", 9999):
                return (rank["name"], f"{rank.get('percent', 'N/A')}%")
        for rank in reversed(ranges):
            if rank.get("min_mmr", 0) <= mmr <= rank.get("max_mmr", 9999):
                return (rank["name"], f"{rank.get('percent', 'N/A')}%")
        return ("Unranked", "N/A")
    except Exception:
        return ("Unknown", "N/A")

def fetch_player_data(player_id: str, platform: str = "steam") -> dict:
    resolved_id, resolved_plat = resolve_player(player_id, platform)
    plat_id = PLATFORM_MAP.get(resolved_plat.lower())
    if not plat_id:
        raise ValueError(f"Invalid platform '{resolved_plat}'. Choose from: {list(PLATFORM_MAP.keys())}")

    url = "https://api.rlstats.net/v1/profile/stats"
    r = requests.post(url, json={"apikey": API_KEY, "platformid": plat_id, "playerid": resolved_id}, timeout=10)
    r.raise_for_status()
    data = r.json()
    if not data or data.get("Message") == "Not Found":
        raise ValueError(f"Player '{resolved_id}' not found on {resolved_plat}.")
    return data

def parse_season_stats(data: dict, platform: str, season: int = None, is_legacy: bool = False) -> dict:
    # Dynamically determine the latest active season
    if season is None:
        api_seasons = [int(k) for k in data.get("RankedSeasons", {}).keys() if k.isdigit()]
        season_id_info = data.get("SeasonInfo", {}).get("SeasonID")
        if season_id_info:
            target_api_season = str(season_id_info)
        elif api_seasons:
            target_api_season = str(max(api_seasons))
        else:
            target_api_season = "38"
        
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
                tier_id = pd.get("Tier", 0)
                div_idx = pd.get("Division", 0)
                if tier_id and 0 < tier_id < len(TIER_NAMES):
                    base_rank = TIER_NAMES[tier_id]
                    if tier_id == 22:
                        rank_name = base_rank
                    else:
                        roman = ["Div I", "Div II", "Div III", "Div IV"][div_idx] if 0 <= div_idx < 4 else f"Div {div_idx+1}"
                        rank_name = f"{base_rank} ({roman})"
                    percent = get_percent_for_tier(key, base_rank)
                else:
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
    clean_mode = gamemode.lower().replace(" ", "").replace("_", "").replace("-", "")
    playlist_id = GAMEMODE_ALIAS_MAP.get(clean_mode, "13")
    playlist_name = PLAYLIST_MAP.get(playlist_id, "Standard (3v3)")

    parsed = parse_season_stats(data, platform="steam", season=season, is_legacy=is_legacy)
    playlist_entry = next((p for p in parsed["playlists"] if p["playlist"] == playlist_name), None)

    current_rank = playlist_entry["rank"] if playlist_entry else "Unranked"
    percentile = playlist_entry["percentile"] if playlist_entry else "N/A"
    mmr = playlist_entry["mmr"] if playlist_entry else 0
    matches = playlist_entry["matches"] if playlist_entry else 0

    return {
        "player": parsed["display_name"],
        "gamemode": playlist_name,
        "current_rank": current_rank,
        "rank_percentile": percentile,
        "mmr": mmr,
        "matches_played": matches,
        "metrics": parsed["metrics"]
    }

def main():
    parser = argparse.ArgumentParser(description="Fetch Rocket League Stats, Compare, and Coaching Analysis")
    parser.add_argument("--action", choices=["stats", "compare", "coaching"], default="stats", help="Action")
    parser.add_argument("--player", default="karmajuney", help="Player ID, username, or friend alias")
    parser.add_argument("--platform", default="steam", help="Platform (steam, ps4, xbox, switch, epic)")
    parser.add_argument("--season", type=int, help="Season number (F2P default, or OG if is_legacy)")
    parser.add_argument("--is_legacy", action="store_true", help="Query legacy OG seasons")
    parser.add_argument("--player2", help="Second player for comparison")
    parser.add_argument("--player2_platform", default="steam", help="Platform for second player")
    parser.add_argument("--gamemode", default="3v3", help="Gamemode (e.g. 2v2, 2s, ranked 2s, 3v3, 1v1)")
    args = parser.parse_args()

    try:
        r1_id, r1_plat = resolve_player(args.player, args.platform)

        if args.action == "stats":
            data = fetch_player_data(r1_id, r1_plat)
            parsed = parse_season_stats(data, r1_plat, season=args.season, is_legacy=args.is_legacy)
            print(json.dumps(parsed, indent=2))

        elif args.action == "compare":
            if not args.player2:
                raise ValueError("--player2 is required for comparison.")
            r2_id, r2_plat = resolve_player(args.player2, args.player2_platform)
            d1 = fetch_player_data(r1_id, r1_plat)
            d2 = fetch_player_data(r2_id, r2_plat)
            p1 = parse_season_stats(d1, r1_plat, season=args.season, is_legacy=args.is_legacy)
            p2 = parse_season_stats(d2, r2_plat, season=args.season, is_legacy=args.is_legacy)
            output = {
                "player_1": p1,
                "player_2": p2
            }
            print(json.dumps(output, indent=2))

        elif args.action == "coaching":
            data = fetch_player_data(r1_id, r1_plat)
            coaching = get_coaching_payload(data, gamemode=args.gamemode, season=args.season, is_legacy=args.is_legacy)
            print(json.dumps(coaching, indent=2))

    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
