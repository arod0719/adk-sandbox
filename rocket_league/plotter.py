import os
import time
import json
import io
import base64
import matplotlib.pyplot as plt
import google.genai.types as types
from google.adk.tools.tool_context import ToolContext
try:
    from .rl_api import PLATFORM_MAP, PLAYLIST_MAP, PLAYLIST_MMR_KEY_MAP, F2P_SEASON_OFFSET
except ImportError:
    from rl_api import PLATFORM_MAP, PLAYLIST_MAP, PLAYLIST_MMR_KEY_MAP, F2P_SEASON_OFFSET
import requests
from dotenv import load_dotenv

# Load env variables
load_dotenv('/home/raspberrypi4/ADK/rocket_league/.env')
API_KEY = os.getenv('RLSTATS_API_KEY')

def get_rank_lines_for_chart(gamemode: str, min_m: int, max_m: int):
    """
    Returns list of (mmr_value, rank_name) to mark on the chart if they fall within the range.
    """
    brain_path = '/home/raspberrypi4/ADK/rocket_league/brain/rank_ranges.json'
    marks = []
    if os.path.exists(brain_path):
        try:
            with open(brain_path, 'r') as f:
                brain_data = json.load(f)
            ranges = brain_data.get(gamemode, [])
            
            for rank in ranges:
                threshold = rank['min_mmr']
                if min_m <= threshold <= max_m:
                    marks.append((threshold, rank['name']))
        except Exception:
            pass
    return sorted(marks)

def parse_seasons_string(seasons_str: str) -> list:
    """
    Parses a string representing seasons into a list of integers.
    Supports comma-separated integers and dash-separated ranges.
    E.g. "1,6,8,10" -> [1, 6, 8, 10]
         "10-16" -> [10, 11, 12, 13, 14, 15, 16]
         "1, 2, 5-8" -> [1, 2, 5, 6, 7, 8]
    """
    if not seasons_str:
        return []
    seasons = set()
    parts = [p.strip() for p in seasons_str.split(',') if p.strip()]
    for part in parts:
        if '-' in part:
            subparts = [sp.strip() for sp in part.split('-') if sp.strip()]
            if len(subparts) == 2:
                try:
                    start = int(subparts[0])
                    end = int(subparts[1])
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

GAMEMODE_TO_PLAYLIST_ID = {
    '1v1': '10', 'duel': '10', 'duel(1v1)': '10',
    '2v2': '11', 'doubles': '11', 'doubles(2v2)': '11',
    '3v3': '13', 'standard': '13', 'standard(3v3)': '13',
    'hoops': '27',
    'rumble': '28',
    'dropshot': '29',
    'snowday': '30',
    'tournament': '34',
    'quads': '61', 'chaos': '61', 'chaos(4v4)': '61',
    'heatseeker': '63'
}

def cleanup_old_charts():
    try:
        import google.adk
        adk_dir = os.path.dirname(google.adk.__file__)
        browser_dir = os.path.join(adk_dir, 'cli', 'browser')
        if os.path.exists(browser_dir):
            for f in os.listdir(browser_dir):
                if f.startswith("mmr_graph_") and f.endswith(".png"):
                    filepath = os.path.join(browser_dir, f)
                    if time.time() - os.path.getmtime(filepath) > 300:
                        os.remove(filepath)
    except Exception:
        pass

async def generate_multi_player_graph(tool_context: ToolContext, gamemode: str, players: list[dict], limit_seasons: int = None, seasons: str = None, metric: str = "mmr"):
    """
    Generates a beautiful season-by-season line chart for one or more players.
    Supports metrics: "mmr" (default) or "matches" (matches played).
    Saves the image to the local static directory and registers it in session artifacts.
    """
    cleanup_old_charts()

    if isinstance(players, str):
        try:
            players = json.loads(players)
        except Exception:
            pass
    if isinstance(players, dict):
        players = [players]
    if not isinstance(players, list) or not players:
        return "Error: Invalid players format or empty players list."

    gamemode_clean = gamemode.lower().replace(' ', '').replace('(', '').replace(')', '')
    playlist_id = GAMEMODE_TO_PLAYLIST_ID.get(gamemode_clean, '13')
    playlist_name = PLAYLIST_MAP.get(playlist_id, gamemode.upper())

    player_datasets = []
    playlist_mmr_key = PLAYLIST_MMR_KEY_MAP.get(playlist_id, '3v3')

    for p in players:
        p_id = p.get('player_id')
        p_platform = p.get('platform') or 'steam'
        if not p_id:
            continue

        plat_id = PLATFORM_MAP.get(p_platform.lower())
        if not plat_id:
            continue

        p_data = None
        cached_stats = tool_context.state.get("latest_rl_stats")
        if cached_stats and cached_stats.get("DisplayName", "").lower() == p_id.lower():
            p_data = cached_stats
        else:
            url = "https://api.rlstats.net/v1/profile/stats"
            try:
                r = requests.post(url, json={"apikey": API_KEY, "platformid": plat_id, "playerid": p_id}, timeout=10)
                r.raise_for_status()
                p_data = r.json()
            except Exception:
                pass

        if not p_data or p_data.get('Message') == 'Not Found':
            continue

        p_seasons = []
        p_values = []
        display_name = p_data.get('DisplayName', p_id)

        for api_season, season_data in p_data.get('RankedSeasons', {}).items():
            pd = season_data.get(playlist_id)
            if pd:
                skill_rating = pd.get('SkillRating', 0)
                matches = pd.get('MatchesPlayed', 0)
                val = skill_rating if metric == "mmr" else matches

                if matches > 0 or skill_rating > 100:
                    f2p_season = int(api_season) - F2P_SEASON_OFFSET
                    p_seasons.append(f2p_season)
                    p_values.append(val)

        if p_seasons:
            sorted_p_points = sorted(zip(p_seasons, p_values))
            
            if seasons:
                target_seasons = parse_seasons_string(seasons)
                if target_seasons:
                    sorted_p_points = [pt for pt in sorted_p_points if pt[0] in target_seasons]
            elif limit_seasons and isinstance(limit_seasons, int) and limit_seasons > 0:
                sorted_p_points = sorted_p_points[-limit_seasons:]

            if sorted_p_points:
                player_datasets.append({
                    'display_name': display_name,
                    'points': sorted_p_points
                })

    if not player_datasets:
        return f"No historical stats found in {playlist_name} for the specified players/seasons."

    all_seasons = set()
    all_vals = []
    for dataset in player_datasets:
        for s, v in dataset['points']:
            all_seasons.add(s)
            all_vals.append(v)

    combined_seasons = sorted(list(all_seasons))
    min_val, max_val = min(all_vals), max(all_vals)

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=120)
    fig.patch.set_facecolor('#121212')
    ax.set_facecolor('#1a1a1a')

    colors = ['#00e5ff', '#ff9100', '#00e676', '#d500f9', '#ffea00', '#ff1744']
    markers = ['o', 'x', '^', 's', 'D', 'v']

    for i, dataset in enumerate(player_datasets):
        p_x = [pt[0] for pt in dataset['points']]
        p_y = [pt[1] for pt in dataset['points']]
        p_color = colors[i % len(colors)]
        p_marker = markers[i % len(markers)]

        ax.plot(p_x, p_y, marker=p_marker, color=p_color, linewidth=2.5, markersize=7, label=dataset['display_name'])

        if len(player_datasets) <= 2:
            offset = 10 if i == 0 or len(player_datasets) == 1 else -15
            anno_color = '#ffffff' if len(player_datasets) == 1 else p_color
            for s, v in dataset['points']:
                ax.annotate(f"{v}", (s, v), textcoords="offset points", xytext=(0, offset), ha='center', fontweight='bold', color=anno_color, fontsize=8)

    if metric == "mmr":
        rank_marks = get_rank_lines_for_chart(playlist_mmr_key, min_val - 100, max_val + 100)
        for threshold, rank_name in rank_marks:
            ax.axhline(y=threshold, color='#ff007f', linestyle=':', linewidth=1.5, alpha=0.8)
            ax.text(combined_seasons[0], threshold + 10, f"{rank_name} Bound ({threshold} MMR)", color='#ff007f', alpha=0.8, fontsize=8, fontweight='bold')

    metric_label = "MMR" if metric == "mmr" else "Matches Played"
    playlist_name_clean = playlist_name.replace('(', '').replace(')', '')
    title_players = " vs ".join([d['display_name'] for d in player_datasets])
    ax.set_title(f"{metric_label.upper()} {playlist_name_clean.upper()}:\n{title_players}", fontsize=11, fontweight='bold', pad=25)
    ax.set_xlabel("Season", fontsize=10, labelpad=10)
    ax.set_ylabel(metric_label, fontsize=10, labelpad=10)

    ax.set_xticks(combined_seasons)
    ax.set_xticklabels([f"S{s}" for s in combined_seasons])
    ax.grid(True, linestyle='--', alpha=0.2, color='#ffffff')
    ax.legend(loc='lower left', bbox_to_anchor=(0.0, 1.02), ncol=3, borderaxespad=0, frameon=False, fontsize=9)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor=fig.get_facecolor(), edgecolor='none')
    png_bytes = buf.getvalue()
    plt.close()

    timestamp = int(time.time())
    filename = f"mmr_graph_{timestamp}.png"
    
    try:
        import google.adk
        adk_dir = os.path.dirname(google.adk.__file__)
        browser_dir = os.path.join(adk_dir, 'cli', 'browser')
        if os.path.exists(browser_dir):
            with open(os.path.join(browser_dir, filename), 'wb') as f:
                f.write(png_bytes)
    except Exception:
        pass

    image_artifact = types.Part.from_bytes(data=png_bytes, mime_type="image/png")
    try:
        await tool_context.save_artifact(filename=filename, artifact=image_artifact)
    except Exception:
        pass

    static_url = f"/dev-ui/{filename}"
    return f"![MMR Chart]({static_url})\n\n*Saved to session artifacts as `{filename}`*"
