"""
auth_manager.py - Handles user authentication, token storage, and backend syncing.
"""
import json
import os
import requests
import threading
from config import DATA_DIR, BACKEND_API_URL

AUTH_FILE = os.path.join(DATA_DIR, "auth.json")

class AuthManager:
    def __init__(self, ui_manager, achievement_tracker):
        self.ui = ui_manager
        self.tracker = achievement_tracker
        
    def load_token(self):
        """Load auth token from disk and auto-login."""
        if os.path.exists(AUTH_FILE):
            try:
                with open(AUTH_FILE, "r") as f:
                    data = json.load(f)
                    token = data.get("token")
                    if token:
                        self.ui.auth_token = token
                        self._fetch_profile(token)
            except Exception as e:
                print(f"Error loading auth token: {e}")
                
    def save_token(self, token):
        """Save auth token to disk."""
        try:
            with open(AUTH_FILE, "w") as f:
                json.dump({"token": token}, f)
        except Exception as e:
            print(f"Error saving auth token: {e}")
            
    def clear_token(self):
        """Clear auth token on logout."""
        if os.path.exists(AUTH_FILE):
            try:
                os.remove(AUTH_FILE)
            except Exception:
                pass
        self.ui.auth_token = None
        self.ui.logged_in = False
        self.ui.account_info = None
        self.ui.username = ""
        
    def login_or_register(self, mode, username, password):
        """Attempt to login or register with the backend."""
        endpoint = "/auth/login" if mode == "login" else "/auth/register"
        try:
            resp = requests.post(
                f"{BACKEND_API_URL}{endpoint}",
                json={"username": username, "password": password},
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                token = data["token"]
                self.ui.auth_token = token
                self.ui.account_info = data["user"]
                self.ui.logged_in = True
                self.ui.username = username
                self.ui.account_error = ""
                self.ui.input_password = ""
                self.save_token(token)
                
                # Sync achievements upon successful login
                self.sync_achievements()
                return True
            else:
                detail = resp.json().get("detail", "Error")
                self.ui.account_error = str(detail)
                return False
        except requests.exceptions.ConnectionError:
            self.ui.account_error = "Cannot connect to server"
            return False
        except Exception as e:
            self.ui.account_error = str(e)[:50]
            return False

    def _fetch_profile(self, token):
        """Fetch user profile to verify token and restore session."""
        def fetch():
            try:
                resp = requests.get(
                    f"{BACKEND_API_URL}/profile",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self.ui.account_info = data
                    self.ui.username = data.get("username", "")
                    self.ui.logged_in = True
                    # Auto-sync achievements down from server
                    self.sync_achievements()
                else:
                    self.clear_token()  # Token invalid/expired
            except Exception:
                # Silently fail, user can try manually logging in later
                pass
        
        threading.Thread(target=fetch, daemon=True).start()

    def sync_achievements(self):
        """Sync unlocked achievements to the backend."""
        if not self.ui.logged_in or not self.ui.auth_token:
            return
            
        def sync():
            try:
                # Simple one-way sync for now: push local unlocks to server
                unlocked = list(self.tracker.unlocked.keys())
                for ach_id in unlocked:
                    requests.post(
                        f"{BACKEND_API_URL}/achievements/unlock",
                        json={"achievement_id": ach_id},
                        headers={"Authorization": f"Bearer {self.ui.auth_token}"},
                        timeout=5
                    )
            except Exception as e:
                print(f"Error syncing achievements: {e}")
                
        threading.Thread(target=sync, daemon=True).start()
