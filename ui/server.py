import os
import sys
from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load unified environment configuration
repo_root = Path(__file__).resolve().parents[1]
load_dotenv(repo_root / ".env")
load_dotenv(Path(__file__).parent / ".env")

if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")

sys.path.insert(0, str(repo_root))

from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Import the unified host agent powered by ADK Skills
from my_gaming_assistant.agent import root_agent as gaming_agent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Resolve chart serving directories for inline image viewing
static_chart_dir = repo_root / "ui" / "static"
static_chart_dir.mkdir(parents=True, exist_ok=True)
app.mount("/dev-ui", StaticFiles(directory=str(static_chart_dir)), name="static")

session_service = InMemorySessionService()

# Single unified runner for the gaming assistant
gaming_runner = Runner(agent=gaming_agent, app_name="gaming_assistant_app", session_service=session_service)

class MessageRequest(BaseModel):
    message: str
    session_id: str = "default"
    agent: str = "gaming_assistant"

@app.post("/api/chat")
async def chat_endpoint(req: MessageRequest):
    # Namespace session key by agent selection to preserve separate tab histories
    session_key = f"{req.agent}_{req.session_id}"
    
    session = await session_service.get_session(app_name="gaming_assistant_app", user_id="local_user", session_id=session_key)
    if session is None:
        session = await session_service.create_session(app_name="gaming_assistant_app", user_id="local_user", session_id=session_key)
        
    user_content = types.Content(role="user", parts=[types.Part(text=req.message)])
    events = gaming_runner.run_async(user_id="local_user", session_id=session_key, new_message=user_content)
    
    final_text = ""
    async for event in events:
        if event.is_final_response():
            if event.content and event.content.parts:
                final_text = event.content.parts[0].text
            
    return {"reply": final_text}

@app.get("/")
async def get_index():
    return FileResponse(os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "index.html"))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9999)
