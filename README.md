# Personal ADK Agents

This repository is a centralized location for storing Agent Development Kit (ADK) agents developed for personal use on a Raspberry Pi. It serves as the configuration and code source for the agents running in my home environment.

## Available Agents

### BF6 Achievement Coach (`bf6`)

The **BF6 Achievement Coach** is a specialized agent designed to help track progress in *Battlefield 6*, specifically focusing on the "Final Push" for specific achievements and mastery goals.

**Key Features:**
*   **Real-time Stat Tracking:** Fetches live data from the Tracker.gg API for player profiles.
*   **Mastery Tracking:** Monitors Kills, Deaths, Wins, and specific Weapon/Class Mastery.
*   **Achievement Progress:** Calculates and displays visual progress bars for specific target achievements:
    *   *A Joyful Nurse* (Revives)
    *   *Rise from Your Grave* (Granite Revives)
    *   *Mission Accepted* (Objective Captures)
*   **Smart Data Interpretation:** Automatically handles API limitations and ensures "True Total" statistics by intelligently summing data from various game mode segments (Multiplayer, Redsec/Battle Royale, etc.).

**Usage:**
Interact with the `bf6_stat_tracker` agent to ask about stats, progress toward trophies, or mastery levels. The agent provides formatted reports with visual bars.

---

## Deployment Setup

These agents are deployed on a local ADK server running on a Raspberry Pi.

**Access:**
The ADK server is accessible locally at: **[adk.karmajuney.com](http://adk.karmajuney.com)**

### Systemctl Configuration

To manage the ADK server as a systemd service on the Raspberry Pi:

```bash
# 1. Refresh systemd to see your new file
sudo systemctl daemon-reload

# 2. Enable it to start automatically on boot
sudo systemctl enable adk

# 3. Start it right now
sudo systemctl start adk
```
