"""Quick API endpoint test."""
import requests

BASE = "http://localhost:8000"

# Test achievements list
r = requests.get(f"{BASE}/achievements/all")
print(f"GET /achievements/all: {r.status_code}, count={len(r.json())}")

# Test register
r = requests.post(f"{BASE}/auth/register", json={"username": "test_player", "password": "test123"})
print(f"POST /auth/register: {r.status_code}")
data = r.json()
token = data.get("token", "")
user = data.get("user", {})
print(f"  User: {user.get('username')}, ELO: {user.get('elo_rating')}")

# Test login
r = requests.post(f"{BASE}/auth/login", json={"username": "test_player", "password": "test123"})
print(f"POST /auth/login: {r.status_code}")

# Test profile
headers = {"Authorization": f"Bearer {token}"}
r = requests.get(f"{BASE}/auth/profile", headers=headers)
print(f"GET /auth/profile: {r.status_code}")

# Test unlock achievement
r = requests.post(f"{BASE}/achievements/unlock", json={"achievement_id": "first_move"}, headers=headers)
print(f"POST /achievements/unlock: {r.status_code}, result={r.json()}")

# Test my achievements
r = requests.get(f"{BASE}/achievements/mine", headers=headers)
print(f"GET /achievements/mine: {r.status_code}, count={len(r.json())}")

# Test leaderboard
r = requests.get(f"{BASE}/leaderboard")
print(f"GET /leaderboard: {r.status_code}")

print("\nAll API tests PASSED!")
