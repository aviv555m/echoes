import sqlite3, os
DB_PATH = os.path.join(os.path.dirname(__file__), "aac.db")

SCHEMA = '''
CREATE TABLE IF NOT EXISTS parent_settings(
  id INTEGER PRIMARY KEY, locked INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS blocked_words(
  word TEXT PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS referrals(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  referrer TEXT, joined TEXT UNIQUE
);
'''

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executescript(SCHEMA)
    cur.execute("SELECT COUNT(*) FROM parent_settings")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO parent_settings(locked) VALUES (0)")
    con.commit(); con.close()
