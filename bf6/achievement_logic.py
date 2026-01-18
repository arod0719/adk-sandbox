from google.adk.tools.tool_context import ToolContext
import json

def get_achievement_metrics(tool_context: ToolContext) -> str:
    """
    Retrieves progress for the user's REMAINING achievements.
    Returns JSON with a pre-calculated 'visual_bar' string.
    """
    stats_data = tool_context.state.get("latest_bf6_stats")
    
    if not stats_data:
        return json.dumps({"error": "No stats found. Call get_bf6_profile_stats first."})

    def get_val(segment_key, stat_name):
        for segment in stats_data.get('segments', []):
            if segment.get('attributes', {}).get('key') == segment_key or \
               segment.get('metadata', {}).get('name') == segment_key:
                return segment.get('stats', {}).get(stat_name, {}).get('value', 0)
        return 0

    # Logic for Missions (API Limitation check)
    missions_proxy = get_val('gm_granite', 'objectivesCaptured')
    mission_current = missions_proxy if missions_proxy > 0 else -1

    # Define the list
    raw_metrics = [
        {"name": "A Joyful Nurse", "current": get_val('kit_support', 'revives'), "target": 1996},
        {"name": "Rise from Your Grave", "current": get_val('gm_granite', 'revives'), "target": 1988},
        {"name": "Mission Accepted", "current": mission_current, "target": 214}
    ]

    # Process and add Visual Bars
    final_output = []
    for item in raw_metrics:
        if item["current"] == -1:
            item["visual_bar"] = "⚠️ API LIMITATION"
            item["status"] = "untrackable"
        else:
            # Calculate Percentage
            pct = min((item["current"] / item["target"]), 1.0)
            
            # Create Bar (10 blocks)
            filled = int(pct * 10)
            bar = "🟩" * filled + "⬛" * (10 - filled)
            
            item["visual_bar"] = f"{bar} {int(pct*100)}%"
            item["status"] = "valid"
        
        final_output.append(item)
    
    return json.dumps(final_output)