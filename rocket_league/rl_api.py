import os
import json
import requests
from dotenv import load_dotenv
from google.adk.tools.tool_context import ToolContext

# Load env variables
load_dotenv('/home/raspberrypi4/ADK/rocket_league/.env')
API_KEY = os.getenv('RLSTATS_API_KEY')

PLATFORM_MAP = {
    'steam': 1,
    'ps4': 2,
    'xbox': 3,
    'switch': 4,
    'epic': 5
}

PLAYLIST_MAP = {
    '0': 'Unranked',
    '10': 'Duel (1v1)',
    '11': 'Doubles (2v2)',
    '12': 'Solo Standard',
    '13': 'Standard (3v3)',
    '27': 'Hoops',
    '28': 'Rumble',
    '29': 'Dropshot',
    '30': 'Snow Day',
    '34': 'Tournament',
    '61': 'Chaos (4v4)',
    '63': 'Heatseeker'
}

PLAYLIST_MMR_KEY_MAP = {
    '10': '1v1',
    '11': '2v2',
    '13': '3v3',
    '27': 'hoops',
    '28': 'rumble',
    '29': 'dropshot',
    '30': 'snowday',
    '34': 'tournament',
    '61': '4v4',
    '63': 'heatseeker'
}

F2P_SEASON_OFFSET = 14

def get_player_stats(tool_context: ToolContext, playerid: str, platform: str, season: int = None, is_legacy: bool = False, refresh: bool = True):
    """
    Retrieves Rocket League stats for a specific player and platform.
    If season is specified (e.g., F2P season 23), it fetches stats for that season.
    By default, it gets the most recent season.
    The is_legacy flag should be set to True if querying original/OG seasons (e.g., Legacy seasons 1-14).
    Always refreshes state to get the latest statistics when called.
    """
    platform = platform.lower()
    platformid = PLATFORM_MAP.get(platform)
    
    if not platformid:
        return f"Error: Invalid platform '{platform}'. Valid platforms are: {', '.join(PLATFORM_MAP.keys())}"
        
    # Check cache if refresh is False and stats are already in state
    if not refresh and "latest_rl_stats" in tool_context.state:
        saved_player = tool_context.state.get("current_player")
        saved_platform = tool_context.state.get("current_platform")
        if saved_player == playerid and saved_platform == platform:
            return format_stats_output(tool_context.state["latest_rl_stats"], platform, season, is_legacy)

    url = "https://api.rlstats.net/v1/profile/stats"
    payload = {
        "apikey": API_KEY,
        "platformid": platformid,
        "playerid": playerid
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        return f"Error fetching data from API: {e}"
        
    # Check if the player exists
    if not data or data.get('Message') == 'Not Found':
        return f"Error: Player '{playerid}' not found on {platform}."
        
    # Save raw data to state context to refresh it
    tool_context.state["latest_rl_stats"] = data
    tool_context.state["current_player"] = playerid
    tool_context.state["current_platform"] = platform
    
    return format_stats_output(data, platform, season, is_legacy)

def format_stats_output(data: dict, platform: str, season: int = None, is_legacy: bool = False):
    # Identify the target season
    if season is None:
        target_api_season = str(data.get('SeasonInfo', {}).get('SeasonID', '37'))
        api_season_val = int(target_api_season)
        if api_season_val > F2P_SEASON_OFFSET:
            target_f2p_season = api_season_val - F2P_SEASON_OFFSET
            season_display = f"Season {target_f2p_season}"
        else:
            season_display = f"OG Season {api_season_val}"
    else:
        if is_legacy:
            target_api_season = str(season)
            season_display = f"OG Season {season}"
        else:
            target_api_season = str(season + F2P_SEASON_OFFSET)
            season_display = f"Season {season}"
        
    ranked_seasons = data.get('RankedSeasons', {})
    
    if target_api_season not in ranked_seasons:
        return f"Error: Stats for {season_display} not found for this player."
        
    season_data = ranked_seasons[target_api_season]
    
    result = [f"--- Stats for {data.get('DisplayName')} ({platform.capitalize()}) - {season_display} ---"]
    
    # Season aggregate stats
    overall_stats = season_data.get('Stats', {})
    wins = overall_stats.get('Wins', 0)
    goals = overall_stats.get('Goals', 0)
    assists = overall_stats.get('Assists', 0)
    saves = overall_stats.get('Saves', 0)
    shots = overall_stats.get('Shots', 0)
    mvps = overall_stats.get('MVPs', 0)
    
    result.append(f"Wins: {wins} | Goals: {goals} | Assists: {assists} | Saves: {saves} | Shots: {shots} | MVPs: {mvps}")
    
    # Calculate Ratios
    shot_accuracy = (goals / shots * 100) if shots > 0 else 0
    saves_per_win = (saves / wins) if wins > 0 else 0
    assists_per_win = (assists / wins) if wins > 0 else 0
    result.append(f"Shot Accuracy: {shot_accuracy:.1f}% | Saves per Win: {saves_per_win:.2f} | Assists per Win: {assists_per_win:.2f}")
    
    result.append("\n--- Ranked Playlists ---")
    found_ranked = False
    for playlist_id, playlist_name in PLAYLIST_MAP.items():
        playlist_data = season_data.get(playlist_id)
        if playlist_data:
            skill_rating = playlist_data.get('SkillRating', 0)
            matches = playlist_data.get('MatchesPlayed', 0)
            if skill_rating > 100 or matches > 0:
                found_ranked = True
                winstreak = playlist_data.get('WinStreak', 0)
                
                # Select correct MMR ranges based on the playlist type
                playlist_key = PLAYLIST_MMR_KEY_MAP.get(playlist_id, '3v3')
                rank_name, percent = get_rank_name_from_mmr(skill_rating, playlist_key)
                
                if matches > 0:
                    result.append(f"{playlist_name}: Rank: {rank_name} (MMR: {skill_rating}) [Top {percent}] | Matches: {matches} | Win Streak: {winstreak}")
                else:
                    result.append(f"{playlist_name}: Rank: {rank_name} (MMR: {skill_rating}) [Top {percent}] | [Not Played]")
            
    if not found_ranked:
        result.append("No ranked matches played in this season.")
        
    return "\n".join(result)

def compare_players(tool_context: ToolContext, player1_id: str, player1_platform: str, player2_id: str, player2_platform: str, season: int = None, is_legacy: bool = False):
    """
    Compares stats for two different players.
    """
    stats1 = get_player_stats(tool_context, player1_id, player1_platform, season, is_legacy, refresh=True)
    stats2 = get_player_stats(tool_context, player2_id, player2_platform, season, is_legacy, refresh=True)
    
    return f"=== PLAYER 1 ===\n{stats1}\n\n=== PLAYER 2 ===\n{stats2}"

def get_rank_name_from_mmr(mmr: float, playlist_key: str):
    brain_path = '/home/raspberrypi4/ADK/rocket_league/brain/rank_ranges.json'
    if not os.path.exists(brain_path):
        return ("Unknown", "N/A")
        
    try:
        with open(brain_path, 'r') as f:
            brain_data = json.load(f)
            
        ranges = brain_data.get(playlist_key, brain_data.get('3v3', []))
        for rank in ranges:
            if rank['min_mmr'] <= mmr <= rank['max_mmr']:
                return (rank['name'], f"{rank['percent']}%")
        return ("Unranked", "N/A")
    except Exception:
        return ("Unknown", "N/A")

def get_coaching_advice(tool_context: ToolContext, gamemode: str = None, season: int = None, is_legacy: bool = False):
    """
    Analyzes the loaded player profile state and provides dynamic coaching advice.
    """
    data = tool_context.state.get("latest_rl_stats")
    if not data:
        return "No player profile is loaded. Please run get_player_stats first to retrieve player information."
        
    # Default to current active season in API
    if season is None:
        target_api_season = str(data.get('SeasonInfo', {}).get('SeasonID', '37'))
        api_season_val = int(target_api_season)
        if api_season_val > F2P_SEASON_OFFSET:
            target_f2p_season = api_season_val - F2P_SEASON_OFFSET
            season_display = f"Season {target_f2p_season}"
        else:
            season_display = f"OG Season {api_season_val}"
    else:
        if is_legacy:
            target_api_season = str(season)
            season_display = f"OG Season {season}"
        else:
            target_api_season = str(season + F2P_SEASON_OFFSET)
            season_display = f"Season {season}"
        
    ranked_seasons = data.get('RankedSeasons', {})
    if target_api_season not in ranked_seasons:
        return f"Could not find season stats to construct coaching advice."
        
    season_data = ranked_seasons[target_api_season]
    overall_stats = season_data.get('Stats', {})
    
    wins = overall_stats.get('Wins', 0)
    goals = overall_stats.get('Goals', 0)
    assists = overall_stats.get('Assists', 0)
    saves = overall_stats.get('Saves', 0)
    shots = overall_stats.get('Shots', 0)
    
    # Calculate ratios
    shot_accuracy = (goals / shots * 100) if shots > 0 else 0
    saves_per_win = (saves / wins) if wins > 0 else 0
    assists_per_win = (assists / wins) if wins > 0 else 0
    goals_per_win = (goals / wins) if wins > 0 else 0
    
    # Determine the playlist and rank
    gamemode = gamemode if gamemode in ['1v1', '2v2', '3v3'] else '3v3'
    playlist_id = '10' if gamemode == '1v1' else ('11' if gamemode == '2v2' else '13')
    
    playlist_data = season_data.get(playlist_id, {})
    skill_rating = playlist_data.get('SkillRating', 0)
    
    playlist_key = PLAYLIST_MMR_KEY_MAP.get(playlist_id, '3v3')
    rank_name, percent = get_rank_name_from_mmr(skill_rating, playlist_key)
    
    # Read the brain template
    brain_path = '/home/raspberrypi4/ADK/rocket_league/brain/rank_ranges.json'
    baseline_advice = "Keep practicing and review your game positioning."
    if os.path.exists(brain_path):
        try:
            with open(brain_path, 'r') as f:
                brain_data = json.load(f)
            baseline_advice = brain_data.get('coaching_advice_templates', {}).get(gamemode, {}).get(rank_name, baseline_advice)
        except Exception:
            pass
            
    # Compile a rich stats payload for the LLM to process dynamically
    advice_payload = {
        "PlayerName": data.get("DisplayName"),
        "Gamemode": gamemode,
        "CurrentRank": rank_name,
        "RankPercent": percent,
        "MMR": skill_rating,
        "MatchesPlayed": playlist_data.get("MatchesPlayed", 0),
        "WinStreak": playlist_data.get("WinStreak", 0),
        "Metrics": {
            "Wins": wins,
            "Goals": goals,
            "Assists": assists,
            "Saves": saves,
            "Shots": shots,
            "ShotAccuracyPercentage": round(shot_accuracy, 1),
            "GoalsPerWin": round(goals_per_win, 2),
            "SavesPerWin": round(saves_per_win, 2),
            "AssistsPerWin": round(assists_per_win, 2)
        },
        "BaselineAdvice": baseline_advice
    }
    
    return json.dumps(advice_payload)
