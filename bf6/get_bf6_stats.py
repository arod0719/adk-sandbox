import json
from curl_cffi import requests
from google.adk.tools.tool_context import ToolContext

def load_or_fetch_stats(
    tool_context: ToolContext,
    refresh: bool = False,
    profile_id: str = None,
    platform: str = None
) -> dict:
    """
    Helper to resolve profile configuration, handle caching, and fetch fresh stats if needed.
    """
    DEFAULT_ID = "2770616530"
    DEFAULT_PLATFORM = "steam"

    saved_id = tool_context.state.get("current_profile_id", DEFAULT_ID)
    saved_platform = tool_context.state.get("current_platform", DEFAULT_PLATFORM)

    target_id = profile_id if profile_id else saved_id
    target_platform = platform.lower() if platform else ("steam" if profile_id else saved_platform)

    config_changed = (target_id != saved_id) or (target_platform != saved_platform)

    if config_changed:
        print(f"\n[Tool] 🔄 Configuration changed! Switching to {target_platform}/{target_id}...")
        tool_context.state["current_profile_id"] = target_id
        tool_context.state["current_platform"] = target_platform
        refresh = True

    if not refresh and "latest_bf6_stats" in tool_context.state:
        print(f"\n[Tool] 💾 Returning CACHED stats for {target_id} ({target_platform})...")
        return tool_context.state["latest_bf6_stats"]

    url = f"https://api.tracker.gg/api/v2/bf6/standard/profile/{target_platform}/{target_id}"
    print(f"\n[Tool] ⚡ Fetching FRESH stats for {target_id} ({target_platform})...")
    
    response = requests.get(url, impersonate="chrome", timeout=15)
    if response.status_code == 200:
        data = response.json().get('data', {})
        tool_context.state["latest_bf6_stats"] = data
        tool_context.state["current_profile_id"] = target_id
        tool_context.state["current_platform"] = target_platform
        return data
    else:
        raise Exception(f"API returned status code {response.status_code} for ID {target_id}")


def get_bf6_profile_stats(
    tool_context: ToolContext, 
    refresh: bool = False, 
    profile_id: str = None, 
    platform: str = 'steam'
) -> str:
    """
    Fetches the raw BF6 stats JSON. Handles ID switching and state persistence.
    
    Args:
        refresh (bool): If True, forces a new API call.
        profile_id (str): Optional. Provide this ONLY if the user explicitly asks to change the User ID.
        platform (str): Optional. Provide this ONLY if the user explicitly changes platform (defaults to 'steam').
    """
    try:
        data = load_or_fetch_stats(tool_context, refresh=refresh, profile_id=profile_id, platform=platform)
        return json.dumps(data)
    except Exception as e:
        return f"Error: {str(e)}"