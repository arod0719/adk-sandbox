import json
from curl_cffi import requests
from google.adk.tools.tool_context import ToolContext

def get_bf6_profile_stats(
    tool_context: ToolContext, 
    refresh: bool = False, 
    profile_id: str = None, 
    platform: str = None
) -> str:
    """
    Fetches the raw BF6 stats JSON. Handles ID switching and state persistence.
    
    Args:
        refresh (bool): If True, forces a new API call.
        profile_id (str): Optional. Provide this ONLY if the user explicitly asks to change the User ID.
        platform (str): Optional. Provide this ONLY if the user explicitly changes platform (defaults to 'steam').
    """
    
    # --- 1. RESOLVE CONFIGURATION (Args > State > Default) ---
    
    # Defaults
    DEFAULT_ID = "2770616530"
    DEFAULT_PLATFORM = "steam"

    # Load saved config from state, or initialize if missing
    saved_id = tool_context.state.get("current_profile_id", DEFAULT_ID)
    saved_platform = tool_context.state.get("current_platform", DEFAULT_PLATFORM)

    # Determine effective values
    # If the LLM passed a new ID, use it. Otherwise, use the saved one.
    target_id = profile_id if profile_id else saved_id
    target_platform = platform if platform else saved_platform

    # --- 2. DETECT CHANGE & FORCE REFRESH ---
    
    # If the user changed the ID/Platform in this call, we MUST refresh
    config_changed = (target_id != saved_id) or (target_platform != saved_platform)
    
    if config_changed:
        print(f"\n[Tool] 🔄 Configuration changed! Switching to {target_platform}/{target_id}...")
        # Update state for future calls
        tool_context.state["current_profile_id"] = target_id
        tool_context.state["current_platform"] = target_platform
        # Force refresh because the cached data belongs to the old user
        refresh = True

    # --- 3. CACHE HANDLING ---

    # If we have data, didn't change config, and didn't ask for refresh -> Return Cache
    if not refresh and "latest_bf6_stats" in tool_context.state:
        print(f"\n[Tool] 💾 Returning CACHED stats for {target_id}...")
        return json.dumps(tool_context.state["latest_bf6_stats"])

    # --- 4. API CALL ---
    
    url = f"https://api.tracker.gg/api/v2/bf6/standard/profile/{target_platform}/{target_id}"
    print(f"\n[Tool] ⚡ Fetching FRESH stats for {target_id} ({target_platform})...")
    
    try:
        response = requests.get(url, impersonate="chrome", timeout=15)
        if response.status_code == 200:
            data = response.json().get('data', {})
            
            # Save stats to state
            tool_context.state["latest_bf6_stats"] = data
            
            # Ensure config state is synced (in case this was a fresh start)
            tool_context.state["current_profile_id"] = target_id
            tool_context.state["current_platform"] = target_platform
            
            return json.dumps(data)
        else:
            return f"Error: API returned status code {response.status_code} for ID {target_id}"
    except Exception as e:
        return f"Exception occurred: {str(e)}"