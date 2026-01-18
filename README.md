# ADK (Agent Development Kit)

This repository contains the ADK server and its associated agents. The ADK server provides a platform for deploying and interacting with various specialized AI agents.

## General ADK Server

The ADK server is hosted and can be accessed locally at:
**[adk.karmajuney.com](http://adk.karmajuney.com)**

### Systemctl Setup

To manage the ADK server as a systemd service on Linux, follow these steps:

```bash
# 1. Refresh systemd to see your new file
sudo systemctl daemon-reload

# 2. Enable it to start automatically on boot
sudo systemctl enable adk

# 3. Start it right now
sudo systemctl start adk
```

---

## Agents

### BF6 Achievement Coach (`bf6`)

The **BF6 Achievement Coach** is a specialized agent designed to help players track their progress in Battlefield 6, specifically focusing on the "Final Push" for specific achievements and mastery goals.

**Key Features:**
*   **Real-time Stat Tracking:** Fetches live data from the Tracker.gg API for player profiles on Steam.
*   **Mastery Tracking:** Monitors Kills, Deaths, Wins, and specific Weapon/Class Mastery.
*   **Achievement Progress:** Calculates and displays visual progress bars for specific achievements, including:
    *   *A Joyful Nurse* (Revives)
    *   *Rise from Your Grave* (Granite Revives)
    *   *Mission Accepted* (Objective Captures)
*   **Smart Data Interpretation:** Automatically handles API limitations and ensures "True Total" statistics by intelligently summing data from various game mode segments (Multiplayer, Redsec/Battle Royale, etc.).

**How to use:**
Interact with the `bf6_stat_tracker` agent to ask about your current stats, progress toward specific trophies, or general mastery level. The agent provides formatted reports with visual bars to help you visualize your journey to completion.
