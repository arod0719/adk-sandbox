#!/usr/bin/env python3
"""
GameTools Network API Client for Battlefield Series (BF6, BF2042, BFV, BF1, BF4, BF3).
Documentation: https://api.gametools.network/docs#
Provides real-time stats, combat metrics, classes/kits, and weapons.
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
from pathlib import Path

BASE_URL = "https://api.gametools.network"
DEFAULT_PLAYER = "Karmajuney"
DEFAULT_PLATFORM = "pc"
DEFAULT_GAME = "bf6"
CACHE_DIR = Path("/tmp/bf_gametools_cache")

# Built-in player aliases for friends roster
PLAYER_MAPPINGS = {
    "me": {"player_name": "Karmajuney", "platform": "pc", "display_name": "Alex"},
    "alex": {"player_name": "Karmajuney", "platform": "pc", "display_name": "Alex"},
    "karmajuney": {"player_name": "Karmajuney", "platform": "pc", "display_name": "Alex"},
    "karmajuneyxd": {"player_name": "Karmajuney", "platform": "pc", "display_name": "Alex"},
    "2770616530": {"player_name": "Karmajuney", "platform": "pc", "display_name": "Alex"},
    "will": {"player_name": "pri3s7y", "platform": "pc", "display_name": "Priesty"},
    "priesty": {"player_name": "pri3s7y", "platform": "pc", "display_name": "Priesty"},
    "itspriesty": {"player_name": "pri3s7y", "platform": "pc", "display_name": "Priesty"},
    "pri3s7y": {"player_name": "pri3s7y", "platform": "pc", "display_name": "Priesty"},
    "1002157303178": {"player_name": "pri3s7y", "platform": "pc", "display_name": "Priesty"}
}

GAME_ENDPOINTS = {
    "bf6": "/bf6/stats/",
    "bf2042": "/bf2042/stats/",
    "bfv": "/bfv/stats/",
    "bf5": "/bfv/stats/",
    "bf1": "/bf1/stats/",
    "bf4": "/bf4/stats/",
    "bf3": "/bf3/stats/",
    "bfh": "/bfh/stats/",
    "hardline": "/bfh/stats/",
    "bf2": "/bf2/stats/",
}

def resolve_player(raw_id: str, raw_platform: str = DEFAULT_PLATFORM) -> tuple[str, str, str]:
    clean = (raw_id or "").strip().lower()
    if clean in PLAYER_MAPPINGS:
        m = PLAYER_MAPPINGS[clean]
        plat = raw_platform.strip().lower() if raw_platform and raw_platform != DEFAULT_PLATFORM else m["platform"]
        return m["player_name"], plat, m["display_name"]
    plat = raw_platform.strip().lower() if raw_platform else DEFAULT_PLATFORM
    return (raw_id or DEFAULT_PLAYER).strip(), plat, (raw_id or DEFAULT_PLAYER).strip()

def resolve_game(raw_game: str) -> tuple[str, str]:
    clean = (raw_game or DEFAULT_GAME).strip().lower()
    if clean in GAME_ENDPOINTS:
        canonical = "bfv" if clean == "bf5" else ("bfh" if clean == "hardline" else clean)
        return canonical, GAME_ENDPOINTS[clean]
    return DEFAULT_GAME, GAME_ENDPOINTS[DEFAULT_GAME]

def normalize_platform_for_game(game: str, platform: str) -> str:
    plat = platform.lower()
    if game in ("bf1", "bf4", "bfv", "bf3", "bfh", "bf2042", "bf2"):
        if plat in ("psn", "ps5"):
            return "ps4"
        if plat in ("xbox", "xboxseries"):
            return "xboxone"
        if plat in ("steam", "ea"):
            return "pc"
    return plat

def get_cache_file(game: str, platform: str, player_name: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    clean_p = "".join(c for c in player_name if c.isalnum() or c in ("-", "_"))
    return CACHE_DIR / f"{game}_{platform}_{clean_p}.json"

def fetch_gametools_data(game: str, endpoint: str, player_name: str, platform: str, refresh: bool = False) -> tuple[dict, str]:
    norm_platform = normalize_platform_for_game(game, platform)
    cache_path = get_cache_file(game, norm_platform, player_name)
    if not refresh and cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f), "disk_cache"
        except Exception:
            pass

    params = {
        "name": player_name,
        "platform": norm_platform
    }
    url = f"{BASE_URL}{endpoint}?{urllib.parse.urlencode(params)}"
    headers = {
        "User-Agent": "ADK-GamingAssistant/1.0 (Battlefield Stats Tracker)",
        "Accept": "application/json"
    }

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                try:
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump(data, f)
                except Exception:
                    pass
                return data, "gametools_live_api"
    except urllib.error.HTTPError as e:
        err_msg = ""
        try:
            err_msg = e.read().decode('utf-8', errors='ignore')
        except:
            pass
        if cache_path.exists():
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f), "disk_cache_fallback"
        raise RuntimeError(f"GameTools API HTTP {e.code} for {player_name} ({game}): {err_msg or e.reason}")
    except Exception as e:
        if cache_path.exists():
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f), "disk_cache_fallback"
        raise RuntimeError(f"Unable to reach GameTools API for {player_name} ({game}): {str(e)}")

def parse_gametools_stats(raw: dict, game: str, player_name: str, display_name: str, platform: str, source: str) -> dict:
    kills_val = raw.get("kills", 0)
    deaths_val = raw.get("deaths", 0)
    kd_val = raw.get("killDeath", 0.0)
    
    matches_val = raw.get("matchesPlayed") or raw.get("roundsPlayed") or 0
    wins_val = raw.get("wins")
    losses_val = raw.get("loses")
    
    win_pct_str = raw.get("winPercent")
    if win_pct_str is None and wins_val is not None and matches_val:
        win_pct_str = f"{(wins_val / matches_val * 100):.1f}%"
    elif win_pct_str is not None and not str(win_pct_str).endswith("%"):
        win_pct_str = f"{win_pct_str}%"

    time_played_str = raw.get("timePlayed")
    if not time_played_str and raw.get("secondsPlayed"):
        secs = raw.get("secondsPlayed", 0)
        hours = round(secs / 3600, 1)
        time_played_str = f"{hours}h"

    combat_summary = {
        "game": game.upper(),
        "score": str(raw.get("score", raw.get("totalScore", 0))),
        "career_rank": str(raw.get("rank") or raw.get("level") or "N/A"),
        "time_played": str(time_played_str or "0h"),
        "matches_played": str(matches_val),
        "wins": str(wins_val if wins_val is not None else "N/A"),
        "losses": str(losses_val if losses_val is not None else "N/A"),
        "win_pct": str(win_pct_str or "N/A"),
        "kills": f"{kills_val:,}" if isinstance(kills_val, int) else str(kills_val),
        "deaths": f"{deaths_val:,}" if isinstance(deaths_val, int) else str(deaths_val),
        "kd_ratio": str(kd_val),
        "infantry_kd": str(raw.get("infantryKillDeath", "N/A")),
        "human_pct": str(raw.get("humanPrecentage", "100%")),
        "kills_per_minute": str(raw.get("killsPerMinute", "N/A")),
        "kills_per_match": str(raw.get("killsPerMatch", "N/A")),
        "damage_dealt": f"{raw.get('damage', 0):,}" if isinstance(raw.get('damage'), int) else str(raw.get('damage', "N/A")),
        "damage_per_minute": str(raw.get("damagePerMinute", "N/A")),
        "headshot_pct": str(raw.get("headshots", "N/A")),
        "accuracy": str(raw.get("accuracy", "N/A")),
        "revives": f"{raw.get('revives', 0):,}" if isinstance(raw.get('revives'), int) else str(raw.get('revives', "0")),
        "resupplies": f"{raw.get('resupplies', 0):,}" if isinstance(raw.get('resupplies'), int) else str(raw.get('resupplies', "0")),
        "repairs": f"{raw.get('repairs', 0):,}" if isinstance(raw.get('repairs'), int) else str(raw.get('repairs', "0"))
    }

    classes_dict = {}
    for c in raw.get("classes", []):
        cname = c.get("className") or c.get("characterName") or "Unknown"
        if cname == "All":
            continue
        c_kills = c.get("kills", 0)
        c_kd = c.get("killDeath", 0.0)
        c_time = f"{round(c.get('secondsPlayed', 0) / 3600, 1)}h" if c.get("secondsPlayed") else "N/A"
        classes_dict[cname] = {
            "kills": f"{c_kills:,}" if isinstance(c_kills, int) else str(c_kills),
            "kd": str(c_kd),
            "time_played": c_time,
            "kpm": str(c.get("kpm", 0.0)),
            "image": c.get("image", "")
        }

    weapons_list = []
    raw_weapons = [w for w in raw.get("weapons", []) if w.get("kills", 0) > 0]
    raw_weapons.sort(key=lambda w: w.get("kills", 0), reverse=True)
    for w in raw_weapons[:5]:
        w_kills = w.get("kills", 0)
        weapons_list.append({
            "name": w.get("weaponName", "Unknown"),
            "type": w.get("type", "Weapon"),
            "kills": f"{w_kills:,}" if isinstance(w_kills, int) else str(w_kills),
            "accuracy": str(w.get("accuracy", "N/A")),
            "headshots": f"{w.get('headshotKills', 0):,}",
            "kpm": str(w.get("killsPerMinute", "N/A")),
            "image": w.get("image", "")
        })

    vehicles_list = []
    raw_vehicles = [v for v in raw.get("vehicles", []) if v.get("kills", 0) > 0 or v.get("destroyed", 0) > 0]
    raw_vehicles.sort(key=lambda v: v.get("kills", 0), reverse=True)
    for v in raw_vehicles[:5]:
        v_kills = v.get("kills", 0)
        vehicles_list.append({
            "name": v.get("vehicleName", "Unknown"),
            "type": v.get("type", "Vehicle"),
            "kills": f"{v_kills:,}" if isinstance(v_kills, int) else str(v_kills),
            "destroyed": f"{v.get('destroyed', 0):,}",
            "image": v.get("image", "")
        })

    return {
        "player_name": raw.get("userName", player_name),
        "display_name": display_name,
        "platform": platform,
        "game": game.upper(),
        "data_source": source,
        "combat_overview": combat_summary,
        "classes_and_kits": classes_dict,
        "top_weapons": weapons_list,
        "top_vehicles": vehicles_list
    }

def main():
    parser = argparse.ArgumentParser(description="Fetch Battlefield stats via GameTools Network API")
    parser.add_argument("--profile_id", "--player_name", dest="player_name", default=DEFAULT_PLAYER,
                        help="Player username, EA handle, or friend alias (e.g. 'me', 'will', 'priesty')")
    parser.add_argument("--platform", default=DEFAULT_PLATFORM,
                        help="Platform: pc (default), ea, steam, xbox, psn")
    parser.add_argument("--game", default=DEFAULT_GAME,
                        help="Battlefield game: bf6 (default), bf2042, bfv, bf1, bf4, bf3")
    parser.add_argument("--refresh", action="store_true", help="Force fresh fetch bypassing local cache")
    args = parser.parse_args()

    r_player, r_plat, r_disp = resolve_player(args.player_name, args.platform)
    c_game, endpoint = resolve_game(args.game)

    try:
        raw_data, source = fetch_gametools_data(c_game, endpoint, r_player, r_plat, refresh=args.refresh)
        parsed = parse_gametools_stats(raw_data, c_game, r_player, r_disp, r_plat, source=source)
        print(json.dumps(parsed, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
