---
name: player-mappings
description: Resolve friendly player names and aliases (e.g. Alex/me, Will/Priesty, Erik/Rumble, David, Emilio) to platform-specific usernames and player IDs for Rocket League and Battlefield 6.
---

# Player Identity & Friendly Name Mapping

This skill provides seamless translation from personal friendly names and aliases to verified gaming platform IDs and usernames without requiring the user to specify platform or exact handles.

## Known Player Database

### Rocket League
| Friendly Name / Aliases | Gamer Handle / Steam ID | Platform | In-Game Display |
| :--- | :--- | :--- | :--- |
| **me**, **alex**, **karmajuney** | `karmajuney` | Steam | Karmajuney |
| **will**, **priesty**, **itspriesty** | `itspriesty` | Steam | Priesty |
| **erik**, **rumble**, **tweenty7** | `tweenty7` | Steam | Rumble |
| **david** | `76561198053263580` (Steam ID64) | Steam | BlackWraith |
| **emilio**, **flux**, **fluxrl** | `FluxRL` | Steam | Flux |

*Note on David:* The RLStats API natively accepts David's 64-bit Steam ID `76561198053263580` directly under platform `steam`.

### Battlefield 6
| Friendly Name / Aliases | Gamer Handle / ID | Platform | In-Game Display |
| :--- | :--- | :--- | :--- |
| **me**, **alex** | `2770616530` | Steam | Alex |
| **will**, **priesty** | `1002157303178` | Steam | Priesty |

## Execution Guidelines
1. Whenever the user refers to a friend by first name or nickname (e.g., "compare me and will", "graph erik's 2s", "show david's rank", "check will's bf6 stats"), run `scripts/resolve_player.py` or inspect `references/friends.json` to get their exact username/ID and platform.
2. If a user provides an unrecognized name without a platform, assume platform **`steam`** by default.
