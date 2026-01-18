import json
from curl_cffi import requests
from google.adk.tools.tool_context import ToolContext

def get_bf6_profile_stats(
    tool_context: ToolContext, 
    refresh: bool = False, 
    profile_id: str = "2770616530", 
    platform: str = "steam"
) -> str:
    """
    Fetches the raw BF6 stats JSON.
    
    Args:
        refresh (bool): If True, forces a new API call to get live data. 
                        If False, returns the cached data from memory (if available).
        profile_id (str): The User ID (Defaults to '2770616530').
        platform (str): The platform (Defaults to 'steam').
    """
    
    # 1. CACHE HIT: If we have data and the user didn't ask to refresh, return memory.
    if not refresh and "latest_bf6_stats" in tool_context.state:
        print("\n[Tool] Returning CACHED stats (No API call)...")
        return json.dumps(tool_context.state["latest_bf6_stats"])

    # 2. CACHE MISS or FORCED REFRESH: Hit the API.
    url = f"https://api.tracker.gg/api/v2/bf6/standard/profile/{platform}/{profile_id}"
    print(f"\n[Tool] ⚡ Fetching FRESH stats from API...")
    
    try:
        response = requests.get(url, impersonate="chrome", timeout=15)
        if response.status_code == 200:
            data = response.json().get('data', {})
            
            # Save to state for next time
            tool_context.state["latest_bf6_stats"] = data
            
            return json.dumps(data)
        else:
            return f"Error: API returned status code {response.status_code}"
    except Exception as e:
        return f"Exception occurred: {str(e)}"