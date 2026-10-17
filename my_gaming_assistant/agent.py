import os
import pathlib
from dotenv import load_dotenv

# Load unified environment configuration from repository root and agent directory
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

# Google Search sub-agent grounding tool
search_agent = create_google_search_agent(model="gemini-2.5-flash")
google_search_tool = GoogleSearchAgentTool(agent=search_agent)

# Discover and load skills from the skills/ directory
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
You leverage your specialized skills in the `skills/` directory to track stats, evaluate player ranks, calculate achievement progression, render progression charts, fetch news, and provide dynamic coaching advice.

### AVAILABLE SKILLS:
1. `rocket-league`:
   - Use for querying Rocket League ranks, stats, season history, multi-player comparisons, MMR/matches charts, coaching advice, and game news.
   - Default player is Steam user `karmajuney`.
   - When a Rocket League request is made, load and follow the `rocket-league` skill instructions.

2. `bf6-tracker`:
   - Use for querying Battlefield 6 stats, mastery, and tracking the "Final Push" toward remaining achievements ("A Joyful Nurse" and "Rise from Your Grave").
   - Default player is Steam ID `2770616530`.
   - When a Battlefield 6 request is made, load and follow the `bf6-tracker` skill instructions.

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
