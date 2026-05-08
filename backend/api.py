"""
backend/api.py - FastAPI REST API for Chess Game
Handles authentication, achievements, game history, and leaderboard.

Run:  uvicorn backend.api:app --port 8000 --reload
"""

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt, JWTError
import bcrypt
import time
import os
import asyncio
import uuid
import random

from backend.database import Database

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
JWT_SECRET = os.getenv("CHESS_JWT_SECRET", "chess-game-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 72

# ---------------------------------------------------------------------------
# Matchmaking & WebSocket Manager
# ---------------------------------------------------------------------------
class ConnectionManager:
    def __init__(self):
        # Dictionary of active websockets: ws -> user_dict
        self.active_connections = {}
        # Matchmaking pools: variant -> list of user_dicts
        self.waiting_pools = {"Standard": [], "Chess960": []}
        # Active games: game_id -> {"white": user_dict, "black": user_dict, "moves": []}
        self.active_games = {}
        # Map user_id to game_id
        self.user_to_game = {}

    async def connect(self, websocket: WebSocket, user: dict, variant: str):
        await websocket.accept()
        user["ws"] = websocket
        self.active_connections[websocket] = user
        
        # Add to matchmaking pool
        pool = self.waiting_pools.get(variant, self.waiting_pools["Standard"])
        pool.append(user)
        await self.try_matchmake(variant)

    def disconnect(self, websocket: WebSocket):
        user = self.active_connections.pop(websocket, None)
        if user:
            # Remove from waiting pools
            for pool in self.waiting_pools.values():
                if user in pool:
                    pool.remove(user)
            
            # If in game, notify opponent
            game_id = self.user_to_game.get(user["id"])
            if game_id and game_id in self.active_games:
                game = self.active_games[game_id]
                opponent = game["white"] if game["black"]["id"] == user["id"] else game["black"]
                if opponent["ws"] in self.active_connections:
                    # Can't await directly in disconnect, so we use asyncio.create_task
                    asyncio.create_task(opponent["ws"].send_json({"type": "opponent_disconnected"}))
                
                # We could potentially handle reconnects, but for now just end game
                del self.active_games[game_id]
                self.user_to_game.pop(game["white"]["id"], None)
                self.user_to_game.pop(game["black"]["id"], None)

    async def try_matchmake(self, variant: str):
        pool = self.waiting_pools[variant]
        if len(pool) >= 2:
            p1 = pool.pop(0)
            p2 = pool.pop(0)
            
            # Create game
            game_id = str(uuid.uuid4())
            
            # Randomize colors
            if random.choice([True, False]):
                white, black = p1, p2
            else:
                white, black = p2, p1
                
            # Generate seed for variants that need synchronization (like Chess960)
            seed = random.randint(0, 1000000) if variant == "Chess960" else None

            self.active_games[game_id] = {
                "white": white,
                "black": black,
                "variant": variant,
                "moves": [],
                "seed": seed
            }
            self.user_to_game[white["id"]] = game_id
            self.user_to_game[black["id"]] = game_id
            
            # Notify players
            await white["ws"].send_json({
                "type": "match_found",
                "color": "white",
                "opponent": black["username"],
                "opponent_elo": black.get("elo_rating", 1200),
                "variant": variant,
                "seed": seed
            })
            await black["ws"].send_json({
                "type": "match_found",
                "color": "black",
                "opponent": white["username"],
                "opponent_elo": white.get("elo_rating", 1200),
                "variant": variant,
                "seed": seed
            })

    async def broadcast_game_message(self, game_id: str, message: dict, exclude_user_id: int):
        if game_id in self.active_games:
            game = self.active_games[game_id]
            for player in [game["white"], game["black"]]:
                if player["id"] != exclude_user_id and player["ws"] in self.active_connections:
                    await player["ws"].send_json(message)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
JWT_SECRET = os.getenv("CHESS_JWT_SECRET", "chess-game-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 72

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="Chess Game API", version="0.3")
security = HTTPBearer(auto_error=False)
db = Database()
manager = ConnectionManager()

@app.on_event("startup")
def startup():
    """Connect to DB and initialize schema on startup."""
    if db.connect():
        db.init_schema()
        # Seed achievements
        from achievements import ACHIEVEMENTS
        db.seed_achievements(ACHIEVEMENTS)
        print("[API] Database ready, achievements seeded")
    else:
        print("[API] WARNING: Running without database!")

@app.websocket("/ws/play")
async def websocket_endpoint(websocket: WebSocket, token: str, variant: str = "Standard"):
    # Authenticate token manually for WS
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload["sub"])
        user = db.get_user_by_id(user_id)
        if not user:
            await websocket.close(code=1008)
            return
    except JWTError:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, user, variant)
    
    try:
        while True:
            data = await websocket.receive_json()
            game_id = manager.user_to_game.get(user["id"])
            if not game_id:
                continue
                
            msg_type = data.get("type")
            
            if msg_type == "move":
                # Save move to history memory if needed, then broadcast
                manager.active_games[game_id]["moves"].append(data["move"])
                # Broadcast entire message to ensure metadata like board_hash is sent
                await manager.broadcast_game_message(game_id, data, exclude_user_id=user["id"])
                
            elif msg_type == "sync_state" or msg_type == "request_sync":
                # Forward synchronization messages to the other player
                await manager.broadcast_game_message(game_id, data, exclude_user_id=user["id"])

            elif msg_type == "resign":
                winner = "black" if manager.active_games[game_id]["white"]["id"] == user["id"] else "white"
                await manager.broadcast_game_message(game_id, {
                    "type": "resign",
                    "winner": winner
                }, exclude_user_id=user["id"])
                
                _handle_game_over(game_id, winner, "resign")
                
            elif msg_type == "game_over":
                # Triggered by checkmate/stalemate
                winner = data.get("winner") # 'white', 'black', or 'draw'
                reason = data.get("reason", "checkmate")
                _handle_game_over(game_id, winner, reason)
                
            elif msg_type == "chat":
                await manager.broadcast_game_message(game_id, {
                    "type": "chat",
                    "message": data.get("message", ""),
                    "sender": user["username"]
                }, exclude_user_id=user["id"])
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

def _handle_game_over(game_id, winner, reason):
    """
    Handle the end of a game, calculate Elo changes, and update DB.
    winner: 'white', 'black', or 'draw'
    """
    if game_id not in manager.active_games:
        return
        
    game = manager.active_games[game_id]
    white = game["white"]
    black = game["black"]
    
    # 1. Elo Math
    Kw = 32 if white.get("games_played", 0) > 20 else 40 # Higher K for new players
    Kb = 32 if black.get("games_played", 0) > 20 else 40
    
    Rw = 10 ** (white.get("elo_rating", 1200) / 400)
    Rb = 10 ** (black.get("elo_rating", 1200) / 400)
    
    Ew = Rw / (Rw + Rb)
    Eb = Rb / (Rw + Rb)
    
    if winner == 'white':
        Sw, Sb = 1, 0
    elif winner == 'black':
        Sw, Sb = 0, 1
    else: # draw
        Sw, Sb = 0.5, 0.5
    
    new_white_elo = int(white.get("elo_rating", 1200) + Kw * (Sw - Ew))
    new_black_elo = int(black.get("elo_rating", 1200) + Kb * (Sb - Eb))
    
    # 2. Update Database
    # Stats for White
    db.update_user_stats(
        white["id"], 
        games_played=1, 
        games_won=1 if winner == 'white' else 0, 
        games_drawn=1 if winner == 'draw' else 0, 
        new_elo=new_white_elo
    )
    # Stats for Black
    db.update_user_stats(
        black["id"], 
        games_played=1, 
        games_won=1 if winner == 'black' else 0, 
        games_drawn=1 if winner == 'draw' else 0, 
        new_elo=new_black_elo
    )
    
    # 3. Record Game History
    db.record_game(
        white["id"], black["id"], 
        winner,  # 'white', 'black', 'draw'
        reason,  # 'checkmate', 'resign', 'timeout', etc.
        len(game["moves"]), 
        "online_game"
    )
    
    # 4. Cleanup
    del manager.active_games[game_id]
    manager.user_to_game.pop(white["id"], None)
    manager.user_to_game.pop(black["id"], None)


@app.on_event("shutdown")
def shutdown():
    db.close()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str = None

class LoginRequest(BaseModel):
    username: str
    password: str

class UnlockRequest(BaseModel):
    achievement_id: str

class GameRecord(BaseModel):
    opponent_id: int = None
    result: str  # 'white', 'black', 'draw'
    result_reason: str = ""
    moves_count: int = 0
    time_control: str = ""
    played_as_white: bool = True


# ---------------------------------------------------------------------------
# Auth Helpers
# ---------------------------------------------------------------------------
def create_token(user_id: int, username: str) -> str:
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": int(time.time()) + JWT_EXPIRE_HOURS * 3600,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    """Extract user from JWT token."""
    if not creds:
        raise HTTPException(401, "Not authenticated")
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload["sub"])
        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(401, "User not found")
        return user
    except JWTError:
        raise HTTPException(401, "Invalid token")


# ---------------------------------------------------------------------------
# Auth Endpoints
# ---------------------------------------------------------------------------
@app.post("/auth/register")
def register(req: RegisterRequest):
    """Create a new account."""
    if len(req.username) < 3 or len(req.username) > 32:
        raise HTTPException(400, "Username must be 3-32 characters")
    if len(req.password) < 4:
        raise HTTPException(400, "Password must be at least 4 characters")

    pw_hash = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
    user = db.create_user(req.username, pw_hash, req.display_name)

    if not user:
        raise HTTPException(409, "Username already taken")

    token = create_token(user["id"], user["username"])
    return {"token": token, "user": _sanitize_user(user)}


@app.post("/auth/login")
def login(req: LoginRequest):
    """Login with username and password."""
    user = db.get_user_by_username(req.username)
    if not user:
        raise HTTPException(401, "Invalid credentials")

    if not bcrypt.checkpw(req.password.encode(), user["password_hash"].encode()):
        raise HTTPException(401, "Invalid credentials")

    token = create_token(user["id"], user["username"])
    return {"token": token, "user": _sanitize_user(user)}


@app.get("/auth/profile")
def get_profile(user=Depends(get_current_user)):
    """Get current user profile."""
    achievements = db.get_user_achievements(user["id"])
    return {
        "user": _sanitize_user(user),
        "achievements_count": len(achievements),
    }


# ---------------------------------------------------------------------------
# Achievements Endpoints
# ---------------------------------------------------------------------------
@app.get("/achievements/all")
def get_all_achievements():
    """List all achievement definitions."""
    return db.get_all_achievements()


@app.get("/achievements/mine")
def get_my_achievements(user=Depends(get_current_user)):
    """Get achievements unlocked by current user."""
    achs = db.get_user_achievements(user["id"])
    # Convert timestamps to strings for JSON
    for a in achs:
        if a.get("unlocked_at"):
            a["unlocked_at"] = str(a["unlocked_at"])
    return achs


@app.post("/achievements/unlock")
def unlock_achievement(req: UnlockRequest, user=Depends(get_current_user)):
    """Unlock an achievement."""
    newly = db.unlock_achievement(user["id"], req.achievement_id)
    return {"newly_unlocked": newly, "achievement_id": req.achievement_id}


# ---------------------------------------------------------------------------
# Games Endpoints
# ---------------------------------------------------------------------------
@app.post("/games/record")
def record_game(game: GameRecord, user=Depends(get_current_user)):
    """Record a completed game and update stats."""
    white_id = user["id"] if game.played_as_white else game.opponent_id
    black_id = game.opponent_id if game.played_as_white else user["id"]

    db.record_game(white_id, black_id, game.result,
                   game.result_reason, game.moves_count, game.time_control)

    # Update stats
    won = ((game.result == "white" and game.played_as_white) or
           (game.result == "black" and not game.played_as_white))
    drawn = game.result == "draw"
    db.update_user_stats(user["id"],
                         games_played=1,
                         games_won=1 if won else 0,
                         games_drawn=1 if drawn else 0)

    return {"status": "recorded"}


@app.get("/games/history")
def get_game_history(user=Depends(get_current_user)):
    """Get game history for current user."""
    games = db.get_user_games(user["id"])
    for g in games:
        if g.get("played_at"):
            g["played_at"] = str(g["played_at"])
    return games


@app.get("/leaderboard")
def get_leaderboard():
    """Get top players."""
    return db.get_leaderboard()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _sanitize_user(user):
    """Remove sensitive fields from user dict."""
    return {k: v for k, v in user.items()
            if k not in ("password_hash",)}
