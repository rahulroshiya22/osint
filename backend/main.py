import os
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

import database as db
import userbot

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# Master Password
MASTER_PASSWORD = "#rahul#123"


# ──────────────── Lifespan ────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting up...")
    await db.init_db()
    logger.info("📦 Database initialized")

    # Initialize userbot
    connected = await userbot.init_userbot()
    if connected:
        logger.info("✅ Userbot connected to Telegram")
    else:
        logger.warning("⚠️  Userbot not connected — running in DEMO mode")

    yield

    # Shutdown
    await userbot.disconnect_userbot()
    logger.info("👋 Shutting down...")


# ──────────────── App Setup ────────────────

app = FastAPI(
    title="Telegram OSINT Dashboard API",
    description="Bridge between website and Telegram bots via userbot",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

downloads_dir = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(downloads_dir, exist_ok=True)


# ──────────────── Auth & Dependencies ────────────────

def verify_token(authorization: str = Header(None)):
    """Simple verification using the master password."""
    if not authorization or authorization.replace("Bearer ", "") != f"{MASTER_PASSWORD}_verified":
        raise HTTPException(status_code=401, detail="Invalid access code")
    return True


class VerifyRequest(BaseModel):
    password: str

class LookupRequest(BaseModel):
    input: str


@app.post("/api/verify")
async def verify_password(req: VerifyRequest):
    if req.password == MASTER_PASSWORD:
        return {"success": True}
    return {"success": False}


# ──────────────── Bot Lookup Routes ────────────────

@app.get("/api/bots")
async def list_bots():
    """List all available bots and their info."""
    bots_info = {}
    for key, config in userbot.BOTS.items():
        bots_info[key] = {
            "display_name": config["display_name"],
            "description": config["description"],
            "icon": config["icon"],
            "input_label": config["input_label"],
            "input_placeholder": config["input_placeholder"],
        }
    return {"bots": bots_info, "userbot_connected": userbot.is_connected()}


@app.post("/api/lookup/{bot_key}")
async def lookup(bot_key: str, req: LookupRequest, verified: bool = Depends(verify_token)):
    """Send input to a bot and get the response."""
    if bot_key not in userbot.BOTS:
        raise HTTPException(400, f"Unknown bot: {bot_key}. Available: {list(userbot.BOTS.keys())}")

    if not req.input.strip():
        raise HTTPException(400, "Input cannot be empty")

    # Use chained_lookup for auto Aadhaar follow-up (no cache)
    result = await userbot.chained_lookup(bot_key, req.input.strip())

    return result


# ──────────────── Media Route ────────────────

@app.get("/api/media/{filename}")
async def serve_media(filename: str, verified: bool = Depends(verify_token)):
    filepath = os.path.join(downloads_dir, filename)
    if not os.path.exists(filepath):
        raise HTTPException(404, "File not found")
    return FileResponse(filepath)


# ──────────────── Health Check ────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "userbot_connected": userbot.is_connected(),
        "demo_mode": not userbot.is_connected(),
    }


# ──────────────── Serve Frontend ────────────────

frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


# ──────────────── Run ────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
