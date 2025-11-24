import sqlite3
import logging
from datetime import datetime
from config import DB_PATH

logger = logging.getLogger(__name__)

def get_connection():
    """מחזיר חיבור למסד הנתונים"""
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def log_user_activity(user_id, username, first_name, last_name, action_type, action_details=""):
    """רישום פעילות משתמש במסד הנתונים"""
    try:
        conn = get_connection()
        c = conn.cursor()
        
        # עדכון/הוספת משתמש
        c.execute('''INSERT OR REPLACE INTO users 
                     (user_id, username, first_name, last_name, last_activity, total_actions)
                     VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, COALESCE((SELECT total_actions FROM users WHERE user_id = ?), 0) + 1)
                  ''', (user_id, username, first_name, last_name, user_id))
        
        # רישום פעילות
        c.execute('''INSERT INTO activity_log 
                     (user_id, action_type, action_details)
                     VALUES (?, ?, ?)''', (user_id, action_type, action_details))
        
        # עדכון סטטיסטיקות יומיות
        today = datetime.now().strftime('%Y-%m-%d')
        if action_type == 'start':
            c.execute('''INSERT OR REPLACE INTO daily_stats (date, new_users, total_actions)
                         VALUES (?, COALESCE((SELECT new_users FROM daily_stats WHERE date = ?), 0) + 1,
                         COALESCE((SELECT total_actions FROM daily_stats WHERE date = ?), 0) + 1)
                      ''', (today, today, today))
        else:
            c.execute('''INSERT OR REPLACE INTO daily_stats (date, total_actions)
                         VALUES (?, COALESCE((SELECT total_actions FROM daily_stats WHERE date = ?), 0) + 1)
                      ''', (today, today))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Database error in log_user_activity: {e}")

def get_user_language(user_id):
    """מחזיר את שפת המשתמש מהמסד נתונים"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else 'he'
    except Exception as e:
        logger.error(f"Error getting user language: {e}")
        return 'he'

def set_user_language(user_id, language):
    """קובע את שפת המשתמש במסד נתונים"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO users 
                     (user_id, username, first_name, last_name, language, last_activity, total_actions) 
                     VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, COALESCE((SELECT total_actions FROM users WHERE user_id = ?), 0) + 1)''', 
                     (user_id, '', '', '', language, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error setting user language: {e}")
        return False

# פונקציות נוספות של DB יועברו כאן...
# [המשך עם כל פונקציות ה-DB מהקוד המקורי]
