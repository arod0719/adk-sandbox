#!/usr/bin/env python3
"""
Deterministic scraper and metric calculator for Battlefield 6 via Tracker.gg API.
Can be executed as an ADK Skill script or via CLI.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from curl_cffi import requests

DEFAULT_PROFILE_ID = "2770616530"
DEFAULT_PLATFORM = "steam"
CACHE_DIR = Path("/tmp/bf6_cache")

def get_cache_file(platform: str, profile_id: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{platform}_{profile_id}.json"

def get_bundled_reference_profile() -> Path:
    # Check relative to script location, current working dir, or temporary extraction dir
    candidates = [
        Path("references/sample_profile.json"),
        Path(__file__).parent.parent / "references" / "sample_profile.json",
        Path("/home/raspberrypi4/ADK/my_gaming_assistant/skills/bf6-tracker/references/sample_profile.json")
    ]
    for p in candidates:
        if p.exists():
            return p
    return None

def fetch_raw_profile(platform: str = DEFAULT_PLATFORM, profile_id: str = DEFAULT_PROFILE_ID, refresh: bool = False) -> tuple[dict, str]:
    """
    Fetches raw profile data from Tracker.gg using Chrome TLS fingerprint impersonation.
    Gracefully falls back to cached or bundled profile data if Cloudflare blocks or rates limit.
    """
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

    # Fallback to local cache if available
    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f), "disk_cache_fallback"
        except Exception:
            pass

    # Fallback to bundled sample profile reference
    sample_ref = get_bundled_reference_profile()
    if sample_ref and sample_ref.exists():
        try:
            with open(sample_ref, "r", encoding="utf-8") as f:
                return json.load(f), "bundled_reference_fallback"
        except Exception:
            pass

    raise RuntimeError(f"Unable to fetch profile for {profile_id} on {platform} (Tracker.gg blocked or unavailable).")

def extract_stat_value(segments: list, segment_key: str, stat_name: str) -> int:
    """Helper to extract stat value from segment by key or metadata name."""
    for segment in segments:
        if segment.get("attributes", {}).get("key") == segment_key or \
           segment.get("metadata", {}).get("name") == segment_key:
            return segment.get("stats", {}).get(stat_name, {}).get("value", 0)
    return 0

def calculate_achievements(stats_data: dict) -> list[dict]:
    """
    Calculates progress for 'A Joyful Nurse' and 'Rise from Your Grave'.
    Adjusts for seasonal/temporary event revives vs persistent multiplayer modes.
    """
    segments = stats_data.get("segments", [])

    # 1. Support kit revives (tracks standard Multiplayer & Casual PvE)
    support_revives = extract_stat_value(segments, "kit_support", "revives")

    # 2. Subtract temporary/seasonal event revives (e.g. Operation Angur)
    persistent_modes = [
        "gm_cq", "gm_bt", "gm_rush", "gm_esc", "gm_tdm", "gm_sdm",
        "gm_dom", "gm_strike", "gm_koth", "gm_sabotage", "gm_oblit", "gm_sqdoblit"
    ]
    sum_persistent = sum(extract_stat_value(segments, mode, "revives") for mode in persistent_modes)
    mp_revives = extract_stat_value(segments, "gm_mp", "revives")
    seasonal_revives = max(0, mp_revives - sum_persistent)

    # A Joyful Nurse: Support kit revives excluding temporary seasonal modes
    joyful_nurse_current = max(0, support_revives - seasonal_revives)

    # Rise from Your Grave: Redsec/Granite mode revives
    granite_revives = extract_stat_value(segments, "gm_granite", "revives")

    raw_metrics = [
        {"name": "A Joyful Nurse", "current": joyful_nurse_current, "target": 1996, "description": "Support kit revives in persistent multiplayer modes"},
        {"name": "Rise from Your Grave", "current": granite_revives, "target": 1988, "description": "Revives completed in Granite / Redsec gamemode"}
    ]

    results = []
    for item in raw_metrics:
        current = item["current"]
        target = item["target"]

        if current == -1:
            item["visual_bar"] = "⚠️ API LIMITATION"
            item["numbers_display"] = "API Limitation"
            item["status"] = "untrackable"
            item["percent"] = 0
        else:
            pct = min((current / target), 1.0) if target > 0 else 0.0
            filled = int(pct * 10)
            bar = "🟩" * filled + "⬛" * (10 - filled)
            item["percent"] = round(pct * 100, 1)
            item["visual_bar"] = f"{bar} {int(pct * 100)}%"

            if current >= target:
                item["numbers_display"] = f"{current} / {target} (Completed!)"
                item["status"] = "completed"
            else:
                item["numbers_display"] = f"{current} / {target}"
                item["status"] = "in_progress"

        results.append(item)

    return results

def main():
    parser = argparse.ArgumentParser(description="Fetch BF6 stats and calculate achievements")
    parser.add_argument("--action", choices=["stats", "achievements"], default="achievements", help="Action to perform")
    parser.add_argument("--profile_id", default=DEFAULT_PROFILE_ID, help="Tracker.gg player profile ID or username")
    parser.add_argument("--platform", default=DEFAULT_PLATFORM, help="Platform (steam, origin, psn, xbox)")
    parser.add_argument("--refresh", action="store_true", help="Force fresh fetch from Tracker.gg")
    args = parser.parse_args()

    try:
        data, source = fetch_raw_profile(platform=args.platform, profile_id=args.profile_id, refresh=args.refresh)

        if args.action == "achievements":
            metrics = calculate_achievements(data)
            output = {
                "player_id": args.profile_id,
                "platform": args.platform,
                "data_source": source,
                "achievements": metrics
            }
            print(json.dumps(output, indent=2))
        else:
            # Stats & Mastery overview
            overview_segment = next((s for s in data.get("segments", []) if s.get("type") == "overview"), {})
            overview_stats = overview_segment.get("stats", {})

            summary = {
                "player_id": args.profile_id,
                "platform": args.platform,
                "data_source": source,
                "overview": {k: v.get("displayValue") for k, v in overview_stats.items()},
                "segments_count": len(data.get("segments", []))
            }
            print(json.dumps(summary, indent=2))

    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
