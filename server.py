"""
server.py - Chess Game Online Server
Handles multiplayer matchmaking, room management, and move relay.
Run this on the machine acting as the game server.

Usage:
    python server.py                   # Start on default port 8765
    python server.py --port 8766       # Start on custom port
    python server.py --host 0.0.0.0    # Listen on all interfaces
"""

import asyncio
import json
import argparse
import random
import string
import time
import websockets


class Room:
    """Represents a game room with two players."""

    def __init__(self, room_code, host_ws, time_control):
        self.code = room_code
        self.host = host_ws
        self.guest = None
        self.time_control = time_control
        self.created_at = time.time()
        self.game_started = False
        self.host_color = "white"  # host always plays white
        self.moves = []

    @property
    def is_full(self):
        return self.host is not None and self.guest is not None

    def get_opponent(self, ws):
        if ws == self.host:
            return self.guest
        return self.host


class ChessServer:
    """WebSocket game server for online chess."""

    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.rooms = {}              # room_code -> Room
        self.player_rooms = {}       # websocket -> room_code
        self.matchmaking_queue = []  # list of (ws, time_control) waiting for match
        self.connected = set()

    async def handler(self, websocket):
        """Handle a client connection."""
        self.connected.add(websocket)
        print(f"[+] Client connected. Total: {len(self.connected)}")

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(websocket, data)
                except json.JSONDecodeError:
                    await self._send(websocket, {"type": "error", "message": "Invalid JSON"})
                except Exception as e:
                    print(f"[!] Error handling message: {e}")
                    await self._send(websocket, {"type": "error", "message": str(e)})
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self._handle_disconnect(websocket)
            self.connected.discard(websocket)
            print(f"[-] Client disconnected. Total: {len(self.connected)}")

    async def _handle_message(self, ws, data):
        """Route incoming messages."""
        msg_type = data.get("type")

        if msg_type == "ping":
            await self._send(ws, {"type": "pong", "time": time.time()})

        elif msg_type == "create_room":
            await self._create_room(ws, data)

        elif msg_type == "join_room":
            await self._join_room(ws, data)

        elif msg_type == "find_game":
            await self._find_game(ws, data)

        elif msg_type == "move":
            await self._relay_move(ws, data)

        elif msg_type == "resign":
            await self._handle_resign(ws)

        elif msg_type == "chat":
            await self._relay_chat(ws, data)

        elif msg_type == "leave_room":
            await self._leave_room(ws)

    async def _create_room(self, ws, data):
        """Create a new game room."""
        code = self._generate_room_code()
        time_control = data.get("time_control", "Blitz 5+0")

        room = Room(code, ws, time_control)
        self.rooms[code] = room
        self.player_rooms[ws] = code

        await self._send(ws, {
            "type": "room_created",
            "room_code": code,
            "color": "white",
            "time_control": time_control,
        })
        print(f"[*] Room {code} created")

    async def _join_room(self, ws, data):
        """Join an existing room by code."""
        code = data.get("room_code", "").upper()

        if code not in self.rooms:
            await self._send(ws, {"type": "error", "message": "Room not found"})
            return

        room = self.rooms[code]
        if room.is_full:
            await self._send(ws, {"type": "error", "message": "Room is full"})
            return

        room.guest = ws
        self.player_rooms[ws] = code
        room.game_started = True

        # Notify both players
        await self._send(ws, {
            "type": "game_start",
            "room_code": code,
            "color": "black",
            "time_control": room.time_control,
            "opponent": "Player 1",
        })
        await self._send(room.host, {
            "type": "game_start",
            "room_code": code,
            "color": "white",
            "time_control": room.time_control,
            "opponent": "Player 2",
        })
        print(f"[*] Room {code} - game started!")

    async def _find_game(self, ws, data):
        """Add player to matchmaking queue."""
        time_control = data.get("time_control", "Blitz 5+0")

        # Check if there's someone waiting with same time control
        for i, (queued_ws, queued_tc) in enumerate(self.matchmaking_queue):
            if queued_tc == time_control and queued_ws != ws:
                # Match found!
                self.matchmaking_queue.pop(i)

                code = self._generate_room_code()
                room = Room(code, queued_ws, time_control)
                room.guest = ws
                room.game_started = True
                self.rooms[code] = room
                self.player_rooms[queued_ws] = code
                self.player_rooms[ws] = code

                await self._send(queued_ws, {
                    "type": "game_start",
                    "room_code": code,
                    "color": "white",
                    "time_control": time_control,
                    "opponent": "Opponent",
                })
                await self._send(ws, {
                    "type": "game_start",
                    "room_code": code,
                    "color": "black",
                    "time_control": time_control,
                    "opponent": "Opponent",
                })
                print(f"[*] Matchmaking: paired in room {code}")
                return

        # No match found, add to queue
        self.matchmaking_queue.append((ws, time_control))
        await self._send(ws, {"type": "queue_joined", "position": len(self.matchmaking_queue)})
        print(f"[*] Player queued for {time_control}")

    async def _relay_move(self, ws, data):
        """Relay a move to the opponent."""
        code = self.player_rooms.get(ws)
        if not code or code not in self.rooms:
            return

        room = self.rooms[code]
        opponent = room.get_opponent(ws)
        if opponent:
            room.moves.append(data.get("move"))
            await self._send(opponent, {
                "type": "opponent_move",
                "move": data.get("move"),
            })

    async def _handle_resign(self, ws):
        """Handle player resignation."""
        code = self.player_rooms.get(ws)
        if not code or code not in self.rooms:
            return

        room = self.rooms[code]
        opponent = room.get_opponent(ws)
        if opponent:
            await self._send(opponent, {"type": "opponent_resigned"})

        # Clean up
        await self._cleanup_room(code)

    async def _relay_chat(self, ws, data):
        """Relay chat message to opponent."""
        code = self.player_rooms.get(ws)
        if not code or code not in self.rooms:
            return

        room = self.rooms[code]
        opponent = room.get_opponent(ws)
        if opponent:
            await self._send(opponent, {
                "type": "chat",
                "message": data.get("message", ""),
            })

    async def _leave_room(self, ws):
        """Handle player leaving a room."""
        code = self.player_rooms.get(ws)
        if not code:
            return

        if code in self.rooms:
            room = self.rooms[code]
            opponent = room.get_opponent(ws)
            if opponent:
                await self._send(opponent, {"type": "opponent_left"})
            await self._cleanup_room(code)

        self.player_rooms.pop(ws, None)

    async def _handle_disconnect(self, ws):
        """Handle client disconnect."""
        # Remove from matchmaking queue
        self.matchmaking_queue = [(w, tc) for w, tc in self.matchmaking_queue if w != ws]

        # Leave room
        await self._leave_room(ws)

    async def _cleanup_room(self, code):
        """Clean up a room."""
        room = self.rooms.pop(code, None)
        if room:
            for ws in [room.host, room.guest]:
                if ws:
                    self.player_rooms.pop(ws, None)

    async def _send(self, ws, data):
        """Send JSON message to a client."""
        try:
            await ws.send(json.dumps(data))
        except Exception:
            pass

    def _generate_room_code(self):
        """Generate a unique 6-character room code."""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if code not in self.rooms:
                return code

    async def start(self):
        """Start the WebSocket server."""
        print(f"Chess Game Server starting on ws://{self.host}:{self.port}")
        print(f"Press Ctrl+C to stop")
        async with websockets.serve(self.handler, self.host, self.port):
            await asyncio.Future()  # run forever


def main():
    parser = argparse.ArgumentParser(description="Chess Game Online Server")
    parser.add_argument("--host", default="localhost", help="Host address (default: localhost)")
    parser.add_argument("--port", type=int, default=8765, help="Port number (default: 8765)")
    args = parser.parse_args()

    server = ChessServer(host=args.host, port=args.port)

    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    main()
