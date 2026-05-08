"""
network_manager.py - Client-side WebSocket networking for online play
Manages connection to game server, sending/receiving moves, matchmaking.
"""

import asyncio
import json
import threading
import queue
import time


class NetworkManager:
    """Client-side network manager for online chess."""

    def __init__(self):
        self.ws = None
        self.connected = False
        self.room_code = None
        self.player_color = None  # "white" or "black"
        self.opponent_name = None
        self.time_control = None

        # Thread-safe queues for cross-thread communication
        self.incoming = queue.Queue()  # messages from server
        self.outgoing = queue.Queue()  # messages to server

        self._thread = None
        self._running = False
        self._server_host = "localhost"
        self._server_port = 8765

    def connect(self, host, port, token, variant):
        """Connect to game server in background thread."""
        self._server_host = host
        self._server_port = port
        self.token = token
        self.variant = variant
        self._running = True

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def disconnect(self):
        """Disconnect from server."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        self.connected = False
        self.room_code = None

    def send_move(self, move_data):
        """Send a move to the server."""
        self.outgoing.put({
            "type": "move",
            "move": move_data,
        })

    def send_resign(self):
        """Send resignation."""
        self.outgoing.put({"type": "resign"})

    def find_game(self, time_control):
        """Join matchmaking queue."""
        self.outgoing.put({
            "type": "find_game",
            "time_control": time_control,
        })

    def create_room(self, time_control):
        """Create a new game room."""
        self.outgoing.put({
            "type": "create_room",
            "time_control": time_control,
        })

    def join_room(self, room_code):
        """Join an existing room."""
        self.outgoing.put({
            "type": "join_room",
            "room_code": room_code,
        })

    def send_chat(self, message):
        """Send a chat message."""
        self.outgoing.put({
            "type": "chat",
            "message": message,
        })

    def leave(self):
        """Leave current room."""
        self.outgoing.put({"type": "leave_room"})

    def send_sync(self, fen):
        """Send current board state (FEN) to opponent."""
        self.outgoing.put({
            "type": "sync_state",
            "fen": fen
        })

    def request_sync(self):
        """Request board state from opponent."""
        self.outgoing.put({"type": "request_sync"})

    def poll_events(self):
        """Poll for incoming events. Returns list of event dicts."""
        events = []
        while not self.incoming.empty():
            try:
                events.append(self.incoming.get_nowait())
            except queue.Empty:
                break
        return events

    def _run_loop(self):
        """Run the asyncio event loop in a background thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._connect_and_listen())
        except Exception as e:
            self.incoming.put({"type": "connection_error", "message": str(e)})
        finally:
            loop.close()
            self.connected = False

    async def _connect_and_listen(self):
        """Connect to server and handle messaging."""
        import websockets

        uri = f"ws://{self._server_host}:{self._server_port}/ws/play?token={self.token}&variant={self.variant}"

        try:
            async with websockets.connect(uri) as ws:
                self.ws = ws
                self.connected = True
                self.incoming.put({"type": "connected"})

                # Run send and receive concurrently
                send_task = asyncio.create_task(self._send_loop(ws))
                recv_task = asyncio.create_task(self._recv_loop(ws))

                done, pending = await asyncio.wait(
                    [send_task, recv_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )

                for task in pending:
                    task.cancel()

        except ConnectionRefusedError:
            self.incoming.put({
                "type": "connection_error",
                "message": "Could not connect to server",
            })
        except Exception as e:
            self.incoming.put({
                "type": "connection_error",
                "message": str(e),
            })

    async def _send_loop(self, ws):
        """Send outgoing messages to server."""
        while self._running:
            try:
                msg = self.outgoing.get_nowait()
                await ws.send(json.dumps(msg))
            except queue.Empty:
                await asyncio.sleep(0.05)
            except Exception:
                break

    async def _recv_loop(self, ws):
        """Receive messages from server."""
        try:
            async for message in ws:
                try:
                    data = json.loads(message)
                    self._process_message(data)
                    self.incoming.put(data)
                except json.JSONDecodeError:
                    pass
        except Exception:
            self.incoming.put({"type": "disconnected"})

    def _process_message(self, data):
        """Process server messages to update local state."""
        msg_type = data.get("type")

        if msg_type == "room_created":
            self.room_code = data.get("room_code")
            self.player_color = data.get("color")
            self.time_control = data.get("time_control")

        elif msg_type == "game_start":
            self.room_code = data.get("room_code")
            self.player_color = data.get("color")
            self.time_control = data.get("time_control")
            self.opponent_name = data.get("opponent", "Opponent")

        elif msg_type == "opponent_left" or msg_type == "opponent_resigned":
            self.room_code = None
