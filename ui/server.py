import os
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load local environment config containing API keys safely
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, ".env"))

if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")

sys.path.append('/home/raspberrypi4/ADK')
sys.path.append('/home/raspberrypi4/ADK/rocket_league')
sys.path.append('/home/raspberrypi4/ADK/bf6')

from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Import root agents
from rocket_league.agent import root_agent as rl_agent
from bf6.agent import root_agent as bf6_agent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Resolve browser_dir for Matplotlib charts static serving
import google.adk
adk_dir = os.path.dirname(google.adk.__file__)
browser_dir = os.path.join(adk_dir, 'cli', 'browser')

if os.path.exists(browser_dir):
    app.mount("/dev-ui", StaticFiles(directory=browser_dir), name="static")

session_service = InMemorySessionService()

# Setup runners for both agents
rl_runner = Runner(agent=rl_agent, app_name="rl_app", session_service=session_service)
bf6_runner = Runner(agent=bf6_agent, app_name="bf6_app", session_service=session_service)

class MessageRequest(BaseModel):
    message: str
    session_id: str = "default"
    agent: str = "rocket_league"

@app.post("/api/chat")
async def chat_endpoint(req: MessageRequest):
    app_name = "rl_app" if req.agent == "rocket_league" else "bf6_app"
    runner = rl_runner if req.agent == "rocket_league" else bf6_runner
    
    # Check if session exists in SessionService; if not, create it on-the-fly
    session = await session_service.get_session(app_name=app_name, user_id="local_user", session_id=req.session_id)
    if session is None:
        session = await session_service.create_session(app_name=app_name, user_id="local_user", session_id=req.session_id)
        
    user_content = types.Content(role='user', parts=[types.Part(text=req.message)])
    events = runner.run_async(user_id="local_user", session_id=req.session_id, new_message=user_content)
    
    final_text = ""
    async for event in events:
        if event.is_final_response():
            final_text = event.content.parts[0].text
            
    return {"reply": final_text}

@app.get("/")
async def get_index():
    return FileResponse(os.path.join(current_dir, "templates", "index.html"))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9999)
