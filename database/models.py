import sqlite3
from datetime import datetime

def init_db():
    """אתחול מסד הנתונים"""
    conn = sqlite3.connect('bot_data.db', check_same_thread=False)
    c = conn.cursor()
    
    # טבלת משתמשים
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER UNIQUE,
                  username TEXT,
                  first_name TEXT,
                  last_name TEXT,
                  language TEXT DEFAULT 'he',
                  join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  total_actions INTEGER DEFAULT 1,
                  status TEXT DEFAULT 'active',
                  referred_by INTEGER DEFAULT 0,
                  referral_count INTEGER DEFAULT 0,
                  total_earned REAL DEFAULT 0,
                  payment_verified BOOLEAN DEFAULT FALSE,
                  approved_by TEXT,
                  approved_date TIMESTAMP,
                  slh_tokens REAL DEFAULT 0)''')
    
    # טבלת תשלומים
    c.execute('''CREATE TABLE IF NOT EXISTS payments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  payment_type TEXT,
                  amount REAL,
                  status TEXT DEFAULT 'pending',
                  proof_text TEXT,
                  payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  verified_by TEXT,
                  verification_date TIMESTAMP,
                  slh_reward REAL DEFAULT 0)''')
    
    # טבלת פעילות
    c.execute('''CREATE TABLE IF NOT EXISTS activity_log
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  action_type TEXT,
                  action_details TEXT,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # טבלת סטטיסטיקות יומיות
    c.execute('''CREATE TABLE IF NOT EXISTS daily_stats
                 (date TEXT PRIMARY KEY,
                  new_users INTEGER DEFAULT 0,
                  total_actions INTEGER DEFAULT 0,
                  payments_received INTEGER DEFAULT 0,
                  payments_verified INTEGER DEFAULT 0)''')
    
    # טבלת רפראלים
    c.execute('''CREATE TABLE IF NOT EXISTS referrals
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  referrer_id INTEGER,
                  referred_id INTEGER,
                  level INTEGER,
                  earned_amount REAL,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # טבלת קבוצות
    c.execute('''CREATE TABLE IF NOT EXISTS groups
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  group_id INTEGER UNIQUE,
                  title TEXT,
                  type TEXT,
                  added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  member_count INTEGER DEFAULT 0,
                  is_active BOOLEAN DEFAULT TRUE)''')
    
    conn.commit()
    conn.close()
