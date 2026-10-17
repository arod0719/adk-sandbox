import os
import pathlib
from dotenv import load_dotenv

# Load unified environment configuration
current_dir = pathlib.Path(__file__).parent.resolve()
root_dir = current_dir.parent
load_dotenv(root_dir / ".env")
load_dotenv(current_dir / ".env")

from google.adk.agents.llm_agent import Agent
from google.adk.skills import load_skills_from_dir
from google.adk.tools import skill_toolset
from google.adk.tools.skill_toolset import SkillDiscoveryMode
from google.adk.code_executors.unsafe_local_code_executor import UnsafeLocalCodeExecutor
from google.adk.tools.google_search_agent_tool import create_google_search_agent, GoogleSearchAgentTool

# Google Search grounding tool
search_agent = create_google_search_agent(model="gemini-2.5-flash")
google_search_tool = GoogleSearchAgentTool(agent=search_agent)

# Discover and load skills from skills/ directory
skills_dir = current_dir / "skills"
skills = load_skills_from_dir(skills_dir)

# Initialize SkillToolset with eager discovery and local script execution
gaming_skill_toolset = skill_toolset.SkillToolset(
    skills=skills,
    additional_tools=[google_search_tool],
    code_executor=UnsafeLocalCodeExecutor(),
    discovery_mode=SkillDiscoveryMode.EAGER,
)

system_instruction = """
You are the Gaming Assistant, an elite AI coach and tracker for Rocket League and Battlefield 6.
You leverage your specialized skills in the `skills/` directory to track stats, evaluate player ranks, render progression charts, fetch news, and provide dynamic coaching advice.

### AVAILABLE SKILLS:
1. `player-mappings`:
   - Translates friendly names and friend aliases (e.g., "me" / "Alex", "will" / "priesty", "erik" / "rumble", "david", "emilio") into exact platform IDs.
   - You can pass these friendly names directly to script tools or inspect the player mappings.

2. `rocket-league`:
   - Use for querying Rocket League ranks, stats, season history, multi-player comparisons, MMR/matches charts, coaching advice, and game news.
   - Default player is Steam user `karmajuney`.
   - Supports natural language graphing (e.g. "graph my rank in ranked 2s for the last 5 seasons", "compare me and will in 2s for the last 4 seasons").
   - Automatically determines the latest active season dynamically.
   - When asked to plot or chart, always return the exact markdown image string `![MMR Chart](/dev-ui/...)` returned by `graph_ranks.py`.

3. `bf6-tracker`:
   - Use for querying Battlefield 6 stats, combat performance, K/D ratio, weapon mastery, and class/kit breakdowns.
   - Default player is Steam ID `2770616530`.

### SEARCH GROUNDING:
- Use the `google_search_agent` tool when you need online training pack codes, YouTube video guides, tactical articles, or game mechanics advice.
"""

root_agent = Agent(
    model="gemini-2.5-flash",
    name="gaming_assistant",
    description="A unified gaming coach and tracker for Rocket League and Battlefield 6 powered by ADK Skills.",
    instruction=system_instruction,
    tools=[gaming_skill_toolset],
)
