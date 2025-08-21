import sqlite3
from .db import DB_PATH
PLANS = [('Basic',0),('Basic Plus',3),('Basic Pro',5),('Basic Max',8),('Elite',12)]
class ReferralSystem:
    def __init__(self):
        self.con = sqlite3.connect(DB_PATH, check_same_thread=False)
    def record_referral(self, referrer, joined):
        try:
            cur = self.con.cursor()
            cur.execute("INSERT OR IGNORE INTO referrals(referrer, joined) VALUES(?,?)",(referrer, joined))
            self.con.commit(); return True
        except Exception: return False
    def get_plan_for(self, email):
        cur = self.con.cursor(); cur.execute("SELECT COUNT(*) FROM referrals WHERE referrer=?", (email,)); c = cur.fetchone()[0]
        plan="Basic"
        for name, thr in PLANS:
            if c >= thr: plan = name
        return plan
