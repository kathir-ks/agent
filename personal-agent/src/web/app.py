"""FastAPI web application for the personal agent."""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from ..llm import LLMFactory
from ..agent import AgentBrain, UserProfile
from config.settings import settings

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state (in production, use proper state management)
agent_brains = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    logger.info("Starting up web application...")
    yield
    logger.info("Shutting down web application...")
    # Cleanup
    for brain in agent_brains.values():
        await brain.close()


app = FastAPI(
    title="Personal Agent",
    description="A personal AI agent with web interface",
    version="0.1.0",
    lifespan=lifespan
)

# Models
class ChatMessage(BaseModel):
    message: str
    user_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    user_id: str


class DiscoverRequest(BaseModel):
    user_id: str = "default"
    limit: int = 10


class ContentItemResponse(BaseModel):
    title: str
    url: str
    content_type: str
    description: Optional[str]
    score: float


class InterestRequest(BaseModel):
    user_id: str = "default"
    interest: str


class StatusResponse(BaseModel):
    user: str
    interests: List[str]
    topics: List[str]
    total_interactions: int
    discovered_content_count: int


# Helper functions
async def get_or_create_brain(user_id: str) -> AgentBrain:
    """Get or create an agent brain for a user.

    Args:
        user_id: User ID

    Returns:
        AgentBrain instance
    """
    if user_id not in agent_brains:
        # Create LLM
        llm_config = settings.get_llm_config()
        llm = LLMFactory.create(llm_config)
        await llm.initialize()

        # Load or create profile
        data_dir = Path('./data')
        profile_path = data_dir / f"profile_{user_id}.json"

        if profile_path.exists():
            user_profile = UserProfile.load(profile_path)
        else:
            user_profile = UserProfile.create_default(user_id, "User")

        # Create brain
        brain = AgentBrain(llm=llm, user_profile=user_profile, data_dir=data_dir)
        agent_brains[user_id] = brain

    return agent_brains[user_id]


# Routes
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page."""
    html_file = Path(__file__).parent / "static" / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    else:
        # Return inline HTML if static file doesn't exist
        return HTMLResponse(content=get_default_html())


@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Process a chat message.

    Args:
        message: Chat message

    Returns:
        Chat response
    """
    try:
        brain = await get_or_create_brain(message.user_id)
        response = await brain.process_message(message.message)

        return ChatResponse(
            response=response,
            user_id=message.user_id
        )

    except Exception as e:
        logger.error(f"Error processing chat message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/discover", response_model=List[ContentItemResponse])
async def discover_content(request: DiscoverRequest):
    """Discover interesting content.

    Args:
        request: Discovery request

    Returns:
        List of content items
    """
    try:
        brain = await get_or_create_brain(request.user_id)
        items = await brain.discover_content(limit=request.limit)

        return [
            ContentItemResponse(
                title=item.title,
                url=item.url,
                content_type=item.content_type.value,
                description=item.description,
                score=item.score
            )
            for item in items
        ]

    except Exception as e:
        logger.error(f"Error discovering content: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status/{user_id}", response_model=StatusResponse)
async def get_status(user_id: str = "default"):
    """Get agent status.

    Args:
        user_id: User ID

    Returns:
        Status information
    """
    try:
        brain = await get_or_create_brain(user_id)
        status = brain.get_status()

        return StatusResponse(
            user=status["user"],
            interests=status["interests"],
            topics=status["topics"],
            total_interactions=status["memory"]["total_interactions"],
            discovered_content_count=status["discovered_content_count"]
        )

    except Exception as e:
        logger.error(f"Error getting status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/interests/add")
async def add_interest(request: InterestRequest):
    """Add an interest.

    Args:
        request: Interest request

    Returns:
        Success message
    """
    try:
        brain = await get_or_create_brain(request.user_id)
        brain.add_interest(request.interest)

        return {"message": f"Added interest: {request.interest}"}

    except Exception as e:
        logger.error(f"Error adding interest: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/interests/remove")
async def remove_interest(request: InterestRequest):
    """Remove an interest.

    Args:
        request: Interest request

    Returns:
        Success message
    """
    try:
        brain = await get_or_create_brain(request.user_id)
        brain.remove_interest(request.interest)

        return {"message": f"Removed interest: {request.interest}"}

    except Exception as e:
        logger.error(f"Error removing interest: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/interests/{user_id}")
async def get_interests(user_id: str = "default"):
    """Get user interests.

    Args:
        user_id: User ID

    Returns:
        List of interests
    """
    try:
        brain = await get_or_create_brain(user_id)
        return {
            "interests": brain.user_profile.preferences.interests,
            "topics": brain.user_profile.preferences.topics
        }

    except Exception as e:
        logger.error(f"Error getting interests: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str = "default"):
    """WebSocket endpoint for real-time chat.

    Args:
        websocket: WebSocket connection
        user_id: User ID
    """
    await websocket.accept()
    brain = await get_or_create_brain(user_id)

    try:
        while True:
            # Receive message
            data = await websocket.receive_text()

            # Process message
            response = await brain.process_message(data)

            # Send response
            await websocket.send_text(response)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        await websocket.close()


def get_default_html() -> str:
    """Get default HTML content if static file doesn't exist.

    Returns:
        HTML string
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Personal Agent</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 12px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                max-width: 800px;
                width: 100%;
                padding: 30px;
            }
            h1 {
                color: #667eea;
                margin-bottom: 10px;
            }
            .subtitle {
                color: #666;
                margin-bottom: 30px;
            }
            .chat-container {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                height: 400px;
                overflow-y: auto;
                padding: 20px;
                margin-bottom: 20px;
                background: #f9f9f9;
            }
            .message {
                margin-bottom: 15px;
                padding: 10px 15px;
                border-radius: 8px;
                max-width: 80%;
            }
            .user-message {
                background: #667eea;
                color: white;
                margin-left: auto;
                text-align: right;
            }
            .agent-message {
                background: white;
                color: #333;
                border: 1px solid #e0e0e0;
            }
            .input-group {
                display: flex;
                gap: 10px;
            }
            input, button {
                padding: 12px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                font-size: 14px;
            }
            input {
                flex: 1;
            }
            button {
                background: #667eea;
                color: white;
                border: none;
                cursor: pointer;
                font-weight: 600;
                transition: background 0.3s;
            }
            button:hover {
                background: #5568d3;
            }
            .info {
                margin-top: 20px;
                padding: 15px;
                background: #f0f0f0;
                border-radius: 8px;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Personal Agent</h1>
            <p class="subtitle">Your AI co-pilot for discovery and assistance</p>

            <div class="chat-container" id="chat"></div>

            <div class="input-group">
                <input type="text" id="message" placeholder="Type your message..." />
                <button onclick="sendMessage()">Send</button>
            </div>

            <div class="info">
                <strong>Available features:</strong>
                <ul style="margin-top: 10px; margin-left: 20px;">
                    <li>Ask questions and have conversations</li>
                    <li>Discover interesting content: POST /api/discover</li>
                    <li>Manage interests: POST /api/interests/add</li>
                    <li>View status: GET /api/status/default</li>
                </ul>
            </div>
        </div>

        <script>
            const chatDiv = document.getElementById('chat');
            const messageInput = document.getElementById('message');

            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendMessage();
            });

            async function sendMessage() {
                const message = messageInput.value.trim();
                if (!message) return;

                // Add user message to chat
                addMessage(message, 'user');
                messageInput.value = '';

                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message, user_id: 'default' })
                    });

                    const data = await response.json();
                    addMessage(data.response, 'agent');
                } catch (error) {
                    addMessage('Error: ' + error.message, 'agent');
                }
            }

            function addMessage(text, type) {
                const div = document.createElement('div');
                div.className = `message ${type}-message`;
                div.textContent = text;
                chatDiv.appendChild(div);
                chatDiv.scrollTop = chatDiv.scrollHeight;
            }

            // Initial message
            addMessage('Hello! I am your personal agent. How can I help you today?', 'agent');
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.web_host,
        port=settings.web_port,
        log_level="info"
    )
