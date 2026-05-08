"""Create the chess_game database if it doesn't exist."""
import psycopg

conn = psycopg.connect(
    "host=localhost port=5432 user=chess_user password=chess_pass dbname=postgres connect_timeout=3"
)
conn.autocommit = True
print("Connected to PostgreSQL on port 5432!")

cur = conn.execute("SELECT 1 FROM pg_database WHERE datname = 'chess_game'")
if not cur.fetchone():
    conn.execute("CREATE DATABASE chess_game")
    print("Created database: chess_game")
else:
    print("Database chess_game already exists")

conn.close()

# Now connect to chess_game and init schema
from backend.database import Database
db = Database()
if db.connect():
    print("Connected to chess_game!")
    db.init_schema()
    print("Schema created!")
    from achievements import ACHIEVEMENTS
    db.seed_achievements(ACHIEVEMENTS)
    print(f"Seeded {len(ACHIEVEMENTS)} achievements!")
    db.close()
    print("All done!")
else:
    print("Failed to connect to chess_game")
