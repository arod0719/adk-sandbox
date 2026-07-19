import os
import time
import json
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
            
            # Key tiers to label
            target_tiers = ['Diamond I', 'Champion I', 'Grand Champion I', 'Supersonic Legend']
            for rank in ranges:
                if rank['name'] in target_tiers:
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

def generate_mmr_graph(tool_context: ToolContext, gamemode: str, limit_seasons: int = None, seasons: str = None):
    """
    Generates a beautiful season-by-season MMR progression ASCII chart.
    Allows specifying limit_seasons to restrict the number of seasons plotted (e.g. limit_seasons=4 shows only the last 4 played seasons).
    Allows specifying seasons (e.g., seasons="1,6,8,10" or seasons="10-16") to only plot those specific seasons.
    """
    data = tool_context.state.get("latest_rl_stats")
    if not data:
        return "No player profile is loaded. Please run get_player_stats first to retrieve player statistics."
        
    gamemode = gamemode if gamemode in ['1v1', '2v2', '3v3'] else '3v3'
    playlist_id = '10' if gamemode == '1v1' else ('11' if gamemode == '2v2' else '13')
    
    ranked_seasons = data.get('RankedSeasons', {})
    if not ranked_seasons:
        return "No historical season stats found for this player."
        
    # Gather data points
    seasons_list = []
    mmr_values = []
    
    for api_season, season_data in ranked_seasons.items():
        playlist_data = season_data.get(playlist_id)
        if playlist_data:
            skill_rating = playlist_data.get('SkillRating', 0)
            if skill_rating > 100: # exclude unplayed
                f2p_season = int(api_season) - F2P_SEASON_OFFSET
                seasons_list.append(f2p_season)
                mmr_values.append(skill_rating)
                
    if len(seasons_list) < 2:
        return f"Not enough historical data points in {gamemode} to draw a graph (needs at least 2 seasons)."
        
    # Sort by season number chronological
    sorted_points = sorted(zip(seasons_list, mmr_values))
    
    # Filter by specific seasons if provided
    if seasons:
        target_seasons = parse_seasons_string(seasons)
        if target_seasons:
            sorted_points = [pt for pt in sorted_points if pt[0] in target_seasons]
    # Filter by last N seasons if specified
    elif limit_seasons and isinstance(limit_seasons, int) and limit_seasons > 0:
        sorted_points = sorted_points[-limit_seasons:]
        
    seasons_plotted = [pt[0] for pt in sorted_points]
    mmrs = [pt[1] for pt in sorted_points]
    
    min_s, max_s = min(seasons_plotted), max(seasons_plotted)
    min_m, max_m = min(mmrs), max(mmrs)
    
    # Pad MMR range
    m_range = max_m - min_m if max_m != min_m else 100
    min_m_pad = max(0, min_m - int(m_range * 0.15) - 30)
    max_m_pad = max_m + int(m_range * 0.15) + 30
    
    height = 12
    width = len(sorted_points) * 11
    
    # Create empty grid
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    
    # Map points onto grid
    for i, (s, m) in enumerate(sorted_points):
        x = i * 11 + 3
        y = int((m - min_m_pad) / (max_m_pad - min_m_pad) * (height - 1)) if max_m_pad != min_m_pad else 0
        y = max(0, min(height - 1, y))
        grid[y][x] = '*'
        
        # Label the MMR next to the point
        m_str = str(m)
        for j, char in enumerate(m_str):
            if x + 2 + j < width:
                grid[y][x + 2 + j] = char
                
    # Get rank threshold marks
    rank_marks = get_rank_lines_for_chart(gamemode, min_m_pad, max_m_pad)
    
    chart = []
    title = f"MMR PROGRESSION: {data.get('DisplayName')} ({gamemode.upper()})"
    chart.append("```")
    chart.append("=" * (width + 12))
    chart.append(f" {title}")
    chart.append("=" * (width + 12))
    
    # Render rows from top to bottom
    for r in range(height - 1, -1, -1):
        row_mmr = int(min_m_pad + (r / (height - 1)) * (max_m_pad - min_m_pad))
        line_content = ''.join(grid[r])
        
        # Add rank indicator line details if applicable
        indicator = ""
        for threshold, rank_name in rank_marks:
            # If the threshold falls within the range represented by this row
            row_min = row_mmr - int((max_m_pad - min_m_pad) / (height * 2))
            row_max = row_mmr + int((max_m_pad - min_m_pad) / (height * 2))
            if row_min <= threshold <= row_max:
                indicator = f" <--- {rank_name} Bound ({threshold} MMR)"
                break
                
        chart.append(f"{row_mmr:5d} | {line_content}{indicator}")
        
    # Draw X axis line
    chart.append("      +" + "-" * width)
    
    # Draw X axis labels (Seasons)
    labels_line = "        "
    for s in seasons_plotted:
        labels_line += f"S{s:<11d}"
    chart.append(labels_line[:width + 8])
    chart.append("```")
    
    return "\n".join(chart)

def compare_players_graph(tool_context: ToolContext, player1_id: str, player1_platform: str, player2_id: str, player2_platform: str, gamemode: str, limit_seasons: int = None, seasons: str = None):
    """
    Generates a beautiful season-by-season MMR comparison ASCII chart for two players.
    Allows specifying limit_seasons to restrict the number of seasons plotted (e.g. limit_seasons=4 shows only the last 4 played seasons).
    Allows specifying seasons (e.g., seasons="1,6,8,10" or seasons="10-16") to only plot those specific seasons.
    """
    gamemode = gamemode if gamemode in ['1v1', '2v2', '3v3'] else '3v3'
    playlist_id = '10' if gamemode == '1v1' else ('11' if gamemode == '2v2' else '13')
    
    # Fetch player 1 stats
    plat1_id = PLATFORM_MAP.get(player1_platform.lower())
    plat2_id = PLATFORM_MAP.get(player2_platform.lower())
    if not plat1_id or not plat2_id:
        return "Error: Invalid platform selected."
        
    url = "https://api.rlstats.net/v1/profile/stats"
    
    try:
        r1 = requests.post(url, json={"apikey": API_KEY, "platformid": plat1_id, "playerid": player1_id}, timeout=10)
        r2 = requests.post(url, json={"apikey": API_KEY, "platformid": plat2_id, "playerid": player2_id}, timeout=10)
        r1.raise_for_status()
        r2.raise_for_status()
        p1_data = r1.json()
        p2_data = r2.json()
    except Exception as e:
        return f"Error loading comparison data: {e}"
        
    if p1_data.get('Message') == 'Not Found' or p2_data.get('Message') == 'Not Found':
        return "Error: One or both players were not found."
        
    # Process Player 1 points
    p1_seasons, p1_mmr = [], []
    for api_season, season_data in p1_data.get('RankedSeasons', {}).items():
        pd = season_data.get(playlist_id)
        if pd and pd.get('SkillRating', 0) > 100:
            p1_seasons.append(int(api_season) - F2P_SEASON_OFFSET)
            p1_mmr.append(pd.get('SkillRating'))
            
    # Process Player 2 points
    p2_seasons, p2_mmr = [], []
    for api_season, season_data in p2_data.get('RankedSeasons', {}).items():
        pd = season_data.get(playlist_id)
        if pd and pd.get('SkillRating', 0) > 100:
            p2_seasons.append(int(api_season) - F2P_SEASON_OFFSET)
            p2_mmr.append(pd.get('SkillRating'))
            
    if not p1_seasons and not p2_seasons:
        return "Not enough historical data points to construct a comparison graph."
        
    # Sort and slice Player 1
    s1 = sorted(zip(p1_seasons, p1_mmr))
    if seasons:
        target_seasons = parse_seasons_string(seasons)
        if target_seasons:
            s1 = [pt for pt in s1 if pt[0] in target_seasons]
    elif limit_seasons and isinstance(limit_seasons, int) and limit_seasons > 0:
        s1 = s1[-limit_seasons:]
        
    # Sort and slice Player 2
    s2 = sorted(zip(p2_seasons, p2_mmr))
    if seasons:
        target_seasons = parse_seasons_string(seasons)
        if target_seasons:
            s2 = [pt for pt in s2 if pt[0] in target_seasons]
    elif limit_seasons and isinstance(limit_seasons, int) and limit_seasons > 0:
        s2 = s2[-limit_seasons:]
        
    p1_active_seasons = [pt[0] for pt in s1]
    p2_active_seasons = [pt[0] for pt in s2]
    
    # Combined active seasons chronologically
    combined_seasons = sorted(list(set(p1_active_seasons + p2_active_seasons)))
    if not combined_seasons:
         return "No active seasons to compare."
         
    all_mmrs = [pt[1] for pt in s1] + [pt[1] for pt in s2]
    min_m, max_m = min(all_mmrs), max(all_mmrs)
    m_range = max_m - min_m if max_m != min_m else 100
    min_m_pad = max(0, min_m - int(m_range * 0.15) - 30)
    max_m_pad = max_m + int(m_range * 0.15) + 30
    
    height = 12
    width = len(combined_seasons) * 11
    
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    
    # Map Player 1 onto grid as 'x'
    p1_dict = dict(s1)
    p2_dict = dict(s2)
    
    for i, s in enumerate(combined_seasons):
        x = i * 11 + 3
        m1 = p1_dict.get(s)
        m2 = p2_dict.get(s)
        
        if m1 and m2:
            # Overlap row mapped
            y1 = max(0, min(height - 1, int((m1 - min_m_pad) / (max_m_pad - min_m_pad) * (height - 1))))
            y2 = max(0, min(height - 1, int((m2 - min_m_pad) / (max_m_pad - min_m_pad) * (height - 1))))
            if y1 == y2:
                grid[y1][x] = '@' # Overlap point representation
                lbl = f"x:{m1} o:{m2}"
                for j, char in enumerate(lbl):
                    if x + 2 + j < width:
                        grid[y1][x + 2 + j] = char
            else:
                grid[y1][x] = 'x'
                grid[y2][x] = 'o'
                lbl1 = f"{m1}"
                lbl2 = f"{m2}"
                for j, char in enumerate(lbl1):
                    if x + 2 + j < width:
                        grid[y1][x + 2 + j] = char
                for j, char in enumerate(lbl2):
                    if x + 2 + j < width:
                        grid[y2][x + 2 + j] = char
        elif m1:
            y1 = max(0, min(height - 1, int((m1 - min_m_pad) / (max_m_pad - min_m_pad) * (height - 1))))
            grid[y1][x] = 'x'
            lbl1 = f"{m1}"
            for j, char in enumerate(lbl1):
                if x + 2 + j < width:
                    grid[y1][x + 2 + j] = char
        elif m2:
            y2 = max(0, min(height - 1, int((m2 - min_m_pad) / (max_m_pad - min_m_pad) * (height - 1))))
            grid[y2][x] = 'o'
            lbl2 = f"{m2}"
            for j, char in enumerate(lbl2):
                if x + 2 + j < width:
                    grid[y2][x + 2 + j] = char
                    
    chart = []
    p1_name = p1_data.get('DisplayName')
    p2_name = p2_data.get('DisplayName')
    title = f"MMR COMPARISON: {p1_name} (x) vs {p2_name} (o) in {gamemode.upper()}"
    
    chart.append("```")
    chart.append("=" * (width + 12))
    chart.append(f" {title}")
    chart.append("=" * (width + 12))
    
    # Render rows from top to bottom
    for r in range(height - 1, -1, -1):
        row_mmr = int(min_m_pad + (r / (height - 1)) * (max_m_pad - min_m_pad))
        line_content = ''.join(grid[r])
        chart.append(f"{row_mmr:5d} | {line_content}")
        
    chart.append("      +" + "-" * width)
    
    # Draw X axis labels (Seasons)
    labels_line = "        "
    for s in combined_seasons:
        labels_line += f"S{s:<11d}"
    chart.append(labels_line[:width + 8])
    chart.append("```")
    
    return "\n".join(chart)
