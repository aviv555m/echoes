import sqlite3
from .db import DB_PATH
class ParentControls:
    def __init__(self):
        self.con = sqlite3.connect(DB_PATH, check_same_thread=False)
    def get_blocklist(self):
        cur = self.con.cursor(); cur.execute("SELECT word FROM blocked_words"); return [r[0] for r in cur.fetchall()]
    def block_word(self, w):
        cur = self.con.cursor(); cur.execute("INSERT OR IGNORE INTO blocked_words(word) VALUES(?)",(w,)); self.con.commit()
    def unblock_word(self, w):
        cur = self.con.cursor(); cur.execute("DELETE FROM blocked_words WHERE word=?",(w,)); self.con.commit()
    def lock_settings(self, locked: bool):
        cur = self.con.cursor(); cur.execute("UPDATE parent_settings SET locked=? WHERE id=1",(1 if locked else 0,)); self.con.commit()
    def is_locked(self):
        cur = self.con.cursor(); cur.execute("SELECT locked FROM parent_settings WHERE id=1"); row = cur.fetchone(); return bool(row[0]) if row else False
