from google.adk.tools.tool_context import ToolContext
import json
from .get_bf6_stats import load_or_fetch_stats

def get_achievement_metrics(
    tool_context: ToolContext,
    profile_id: str = None,
    platform: str = None
) -> str:
    """
    Retrieves progress for the user's REMAINING achievements.
    Returns JSON with pre-calculated 'visual_bar' and 'numbers_display' strings.
    
    Args:
        profile_id (str): Optional. Provide this if tracking achievements for a different profile.
        platform (str): Optional. Provide this if tracking achievements for a different platform.
    """
    try:
        stats_data = load_or_fetch_stats(tool_context, profile_id=profile_id, platform=platform)
    except Exception as e:
        return json.dumps({"error": f"Error loading stats: {str(e)}"})
    
    def get_val(segment_key, stat_name):
        for segment in stats_data.get('segments', []):
            if segment.get('attributes', {}).get('key') == segment_key or \
               segment.get('metadata', {}).get('name') == segment_key:
                return segment.get('stats', {}).get(stat_name, {}).get('value', 0)
        return 0

    # A Joyful Nurse calculation logic:
    # 1. Start with Support kit revives. Note that class/kit revives track standard Multiplayer
    #    and Casual (PvE) modes, but do not include Redsec/Granite mode revives in the API.
    support_revives = get_val('kit_support', 'revives')
    
    # 2. Subtract temporary/seasonal event revives (like Operation Angur), which are counted in Multiplayer (gm_mp) 
    # but not in any of the persistent multiplayer gamemodes.
    persistent_modes = [
        'gm_cq', 'gm_bt', 'gm_rush', 'gm_esc', 'gm_tdm', 'gm_sdm', 
        'gm_dom', 'gm_strike', 'gm_koth', 'gm_sabotage', 'gm_oblit', 'gm_sqdoblit'
    ]
    sum_persistent = sum(get_val(mode, 'revives') for mode in persistent_modes)
    mp_revives = get_val('gm_mp', 'revives')
    seasonal_revives = max(0, mp_revives - sum_persistent)
    
    # Since Granite (REDSEC) revives are not tracked under standard kit/class stats in the API,
    # we do not subtract granite_revives from support_revives.
    joyful_nurse_current = max(0, support_revives - seasonal_revives)
    
    # Rise from Your Grave count is tracked by the Redsec/Granite gamemode revives.
    granite_revives = get_val('gm_granite', 'revives')

    # Define the list
    raw_metrics = [
        {"name": "A Joyful Nurse", "current": joyful_nurse_current, "target": 1996},
        {"name": "Rise from Your Grave", "current": granite_revives, "target": 1988}
    ]

    # Process and add Visual Bars
    final_output = []
    for item in raw_metrics:
        current = item["current"]
        target = item["target"]
        
        if current == -1:
            item["visual_bar"] = "⚠️ API LIMITATION"
            item["numbers_display"] = "API Limitation"
            item["status"] = "untrackable"
        else:
            # Calculate Percentage
            pct = min((current / target), 1.0) if target > 0 else 0.0
            
            # Create Bar (10 blocks)
            filled = int(pct * 10)
            bar = "🟩" * filled + "⬛" * (10 - filled)
            
            item["visual_bar"] = f"{bar} {int(pct*100)}%"
            
            if current >= target:
                item["numbers_display"] = f"{current} / {target} (Completed!)"
                item["status"] = "completed"
            else:
                item["numbers_display"] = f"{current} / {target}"
                item["status"] = "valid"
        
        final_output.append(item)
    
    return json.dumps(final_output)