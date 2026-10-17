#!/usr/bin/env python3
"""
Deterministic player identity resolver for gaming assistant.
Maps friend aliases (e.g. Alex/me, Will/Priesty, Erik/Rumble, David, Emilio) to platform IDs.
"""

import sys
import json
import argparse
from pathlib import Path

def get_friends_db_path() -> Path:
    candidates = [
        Path("references/friends.json"),
        Path(__file__).parent.parent / "references" / "friends.json",
        Path("/home/raspberrypi4/ADK/gaming_assistant/skills/player-mappings/references/friends.json")
    ]
    for p in candidates:
        if p.exists():
            return p
    return None

def resolve_player_identity(name: str, game: str = "rocket-league") -> dict:
    clean_name = name.strip().lower()
    game_key = "rocket_league" if "rocket" in game.lower() or "rl" in game.lower() else "bf6"

    db_path = get_friends_db_path()
    if db_path and db_path.exists():
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                db = json.load(f)
            game_db = db.get(game_key, {})
            if clean_name in game_db:
                res = dict(game_db[clean_name])
                res["resolved"] = True
                return res
        except Exception:
            pass

    # Fallback default: assume raw name as username on steam
    return {
        "player_id": name.strip(),
        "platform": "steam",
        "display_name": name.strip(),
        "resolved": False
    }

def main():
    parser = argparse.ArgumentParser(description="Resolve friendly name to gamer tag and platform")
    parser.add_argument("--name", required=True, help="Friendly name or alias (e.g. will, me, erik, david)")
    parser.add_argument("--game", default="rocket-league", choices=["rocket-league", "bf6", "rl"], help="Target game")
    args = parser.parse_args()

    result = resolve_player_identity(args.name, game=args.game)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
