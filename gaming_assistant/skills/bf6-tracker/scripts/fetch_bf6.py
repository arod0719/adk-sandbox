#!/usr/bin/env python3
"""
Deterministic scraper and stat parser for Battlefield 6 via Tracker.gg API.
Can be executed as an ADK Skill script or via CLI.
Focuses strictly on tracking player stats, combat metrics, classes/kits, and weapons.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from curl_cffi import requests
from dotenv import load_dotenv

# Load environment variables safely
for env_path in [
    Path("/home/raspberrypi4/ADK/.env"),
    Path.cwd() / ".env"
]:
    if env_path.exists():
        load_dotenv(env_path)

DEFAULT_PROFILE_ID = "2770616530"
DEFAULT_PLATFORM = "steam"
CACHE_DIR = Path("/tmp/bf6_cache")

# Built-in player mappings for BF6
BF6_NAME_MAPPINGS = {
    "me": {"player_id": "2770616530", "platform": "steam", "display_name": "Alex"},
    "alex": {"player_id": "2770616530", "platform": "steam", "display_name": "Alex"},
    "2770616530": {"player_id": "2770616530", "platform": "steam", "display_name": "Alex"},
    "will": {"player_id": "1002157303178", "platform": "steam", "display_name": "Priesty"},
    "priesty": {"player_id": "1002157303178", "platform": "steam", "display_name": "Priesty"},
    "1002157303178": {"player_id": "1002157303178", "platform": "steam", "display_name": "Priesty"}
}

def resolve_bf6_player(raw_id: str, raw_platform: str = "steam") -> tuple[str, str]:
    clean = raw_id.strip().lower()
    if clean in BF6_NAME_MAPPINGS:
        mapping = BF6_NAME_MAPPINGS[clean]
        return mapping["player_id"], mapping["platform"]
    return raw_id.strip(), (raw_platform.strip().lower() if raw_platform else "steam")

def get_cache_file(platform: str, profile_id: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{platform}_{profile_id}.json"

def get_bundled_reference_profile() -> Path:
    candidates = [
        Path("references/sample_profile.json"),
        Path(__file__).parent.parent / "references" / "sample_profile.json",
        Path("/home/raspberrypi4/ADK/gaming_assistant/skills/bf6-tracker/references/sample_profile.json")
    ]
    for p in candidates:
        if p.exists():
            return p
    return None

def fetch_raw_profile(platform: str = DEFAULT_PLATFORM, profile_id: str = DEFAULT_PROFILE_ID, refresh: bool = False) -> tuple[dict, str]:
    cache_path = get_cache_file(platform, profile_id)
    if not refresh and cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f), "disk_cache"
        except Exception:
            pass

    url = f"https://api.tracker.gg/api/v2/bf6/standard/profile/{platform.lower()}/{profile_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://tracker.gg/"
    }

    try:
        response = requests.get(url, impersonate="chrome120", headers=headers, timeout=12)
        if response.status_code == 200:
            data = response.json().get("data", {})
            try:
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(data, f)
            except Exception:
                pass
            return data, "live_api"
    except Exception:
        pass

    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f), "disk_cache_fallback"
        except Exception:
            pass

    sample_ref = get_bundled_reference_profile()
    if sample_ref and sample_ref.exists():
        try:
            with open(sample_ref, "r", encoding="utf-8") as f:
                return json.load(f), "bundled_reference_fallback"
        except Exception:
            pass

    raise RuntimeError(f"Unable to fetch profile for {profile_id} on {platform} (Tracker.gg blocked or unavailable).")

def extract_stat_value(segments: list, segment_key: str, stat_name: str) -> int:
    for segment in segments:
        if segment.get("attributes", {}).get("key") == segment_key or \
           segment.get("metadata", {}).get("name") == segment_key:
            return segment.get("stats", {}).get(stat_name, {}).get("value", 0)
    return 0

def parse_bf6_stats(data: dict, profile_id: str, platform: str, source: str) -> dict:
    segments = data.get("segments", [])
    overview_segment = next((s for s in segments if s.get("type") == "overview"), {})
    overview_stats = overview_segment.get("stats", {})

    combat_summary = {
        "score": overview_stats.get("score", {}).get("displayValue", "0"),
        "career_rank": overview_stats.get("careerPlayerRank", {}).get("displayValue", "N/A"),
        "time_played": overview_stats.get("timePlayed", {}).get("displayValue", "0h"),
        "matches_played": overview_stats.get("matchesPlayed", {}).get("displayValue", "0"),
        "wins": overview_stats.get("matchesWon", {}).get("displayValue", "0"),
        "losses": overview_stats.get("matchesLost", {}).get("displayValue", "0"),
        "win_pct": overview_stats.get("wlPercentage", {}).get("displayValue", "0%"),
        "kills": overview_stats.get("kills", {}).get("displayValue", "0"),
        "deaths": overview_stats.get("deaths", {}).get("displayValue", "0"),
        "kd_ratio": overview_stats.get("kdRatio", {}).get("displayValue", "0.0"),
        "kda_ratio": overview_stats.get("kdaRatio", {}).get("displayValue", "0.0"),
        "kills_per_minute": overview_stats.get("killsPerMinute", {}).get("displayValue", "0.0"),
        "kills_per_match": overview_stats.get("killsPerMatch", {}).get("displayValue", "0.0"),
        "damage_dealt": overview_stats.get("damageDealt", {}).get("displayValue", "0"),
        "damage_per_minute": overview_stats.get("damagePerMinute", {}).get("displayValue", "0"),
        "headshot_pct": overview_stats.get("headshotPercentage", {}).get("displayValue", "0%"),
        "revives": overview_stats.get("revives", {}).get("displayValue", "0"),
        "resupplies": overview_stats.get("playersResupplied", {}).get("displayValue", "0"),
        "objectives_captured": overview_stats.get("objectivesCaptured", {}).get("displayValue", "0"),
        "objectives_defended": overview_stats.get("defendedObjectives", {}).get("displayValue", "0")
    }

    # Extract Class/Kit mastery stats
    kits = {}
    for seg in segments:
        if seg.get("type") == "kit" or seg.get("attributes", {}).get("key", "").startswith("kit_"):
            name = seg.get("metadata", {}).get("name") or seg.get("attributes", {}).get("key", "Unknown")
            stats = seg.get("stats", {})
            kits[name] = {
                "kills": stats.get("kills", {}).get("displayValue", "0"),
                "time_played": stats.get("timePlayed", {}).get("displayValue", "0h"),
                "score": stats.get("score", {}).get("displayValue", "0"),
                "kpm": stats.get("killsPerMinute", {}).get("displayValue", "0.0")
            }

    # Extract top weapons
    weapons = []
    for seg in segments:
        if seg.get("type") == "weapon":
            w_stats = seg.get("stats", {})
            kills_val = w_stats.get("kills", {}).get("value", 0)
            if kills_val > 0:
                weapons.append({
                    "name": seg.get("metadata", {}).get("name", "Unknown Weapon"),
                    "kills": w_stats.get("kills", {}).get("displayValue", "0"),
                    "kills_val": kills_val,
                    "accuracy": w_stats.get("shotsAccuracy", {}).get("displayValue", "N/A"),
                    "headshots": w_stats.get("headshots", {}).get("displayValue", "0")
                })
    weapons.sort(key=lambda w: w["kills_val"], reverse=True)
    top_weapons = [{k: v for k, v in w.items() if k != "kills_val"} for w in weapons[:5]]

    return {
        "player_id": profile_id,
        "platform": platform,
        "data_source": source,
        "combat_overview": combat_summary,
        "classes_and_kits": kits,
        "top_weapons": top_weapons
    }

def main():
    parser = argparse.ArgumentParser(description="Fetch BF6 stats and combat mastery")
    parser.add_argument("--profile_id", default=DEFAULT_PROFILE_ID, help="Tracker.gg player profile ID, username, or friend alias")
    parser.add_argument("--platform", default=DEFAULT_PLATFORM, help="Platform (steam, origin, psn, xbox)")
    parser.add_argument("--refresh", action="store_true", help="Force fresh fetch from Tracker.gg")
    args = parser.parse_args()

    r_id, r_plat = resolve_bf6_player(args.profile_id, args.platform)

    try:
        data, source = fetch_raw_profile(platform=r_plat, profile_id=r_id, refresh=args.refresh)
        parsed = parse_bf6_stats(data, profile_id=r_id, platform=r_plat, source=source)
        print(json.dumps(parsed, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
