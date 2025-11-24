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

def get_user_stats():
    """קבלת סטטיסטיקות משתמשים"""
    try:
        conn = get_connection()
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM users")
        total_users = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM users WHERE date(last_activity) = date('now')")
        active_today = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM payments WHERE status = 'verified'")
        verified_payments = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM payments WHERE status = 'pending'")
        pending_payments = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM activity_log WHERE date(timestamp) = date('now')")
        actions_today = c.fetchone()[0]
        
        conn.close()
        
        return {
            'total_users': total_users or 0,
            'active_today': active_today or 0,
            'verified_payments': verified_payments or 0,
            'pending_payments': pending_payments or 0,
            'actions_today': actions_today or 0
        }
    except Exception as e:
        logger.error(f"Database error in get_user_stats: {e}")
        return {
            'total_users': 0,
            'active_today': 0,
            'verified_payments': 0,
            'pending_payments': 0,
            'actions_today': 0
        }

def get_recent_activity(limit=10):
    """קבלת פעילות אחרונה"""
    try:
        conn = get_connection()
        c = conn.cursor()
        
        c.execute('''SELECT u.first_name, u.username, al.action_type, al.action_details, al.timestamp
                     FROM activity_log al
                     JOIN users u ON al.user_id = u.user_id
                     ORDER BY al.timestamp DESC LIMIT ?''', (limit,))
        
        activity = c.fetchall()
        conn.close()
        return activity or []
    except Exception as e:
        logger.error(f"Database error in get_recent_activity: {e}")
        return []

def get_pending_payments():
    """קבלת רשימת תשלומים ממתינים"""
    try:
        conn = get_connection()
        c = conn.cursor()
        
        c.execute('''SELECT p.id, u.user_id, u.first_name, u.username, p.payment_type, p.amount, p.proof_text, p.payment_date
                     FROM payments p
                     JOIN users u ON p.user_id = u.user_id
                     WHERE p.status = 'pending'
                     ORDER BY p.payment_date DESC''')
        
        payments = c.fetchall()
        conn.close()
        return payments
    except Exception as e:
        logger.error(f"Database error in get_pending_payments: {e}")
        return []

def get_all_groups():
    """מחזיר את כל הקבוצות מהמסד נתונים"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT group_id, title, type FROM groups WHERE is_active = TRUE ORDER BY last_activity DESC")
        groups = c.fetchall()
        conn.close()
        return groups
    except Exception as e:
        logger.error(f"Error getting groups: {e}")
        return []

def save_group(group_id, title, group_type):
    """שומר קבוצה במסד הנתונים"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO groups 
                     (group_id, title, type, last_activity) 
                     VALUES (?, ?, ?, CURRENT_TIMESTAMP)''', (group_id, title, group_type))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error saving group: {e}")
        return False

def log_payment(user_id, payment_type, amount, proof_text=""):
    """רישום תשלום במסד הנתונים"""
    try:
        conn = get_connection()
        c = conn.cursor()
        
        # חישוב תגמול SLH (39₪ = 1 SLH)
        slh_reward = 1.0
        
        c.execute('''INSERT INTO payments 
                     (user_id, payment_type, amount, proof_text, slh_reward)
                     VALUES (?, ?, ?, ?, ?)''', (user_id, payment_type, amount, proof_text, slh_reward))
        
        payment_id = c.lastrowid
        
        # עדכון סטטיסטיקות תשלומים
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute('''INSERT OR REPLACE INTO daily_stats (date, payments_received)
                     VALUES (?, COALESCE((SELECT payments_received FROM daily_stats WHERE date = ?), 0) + 1)
                  ''', (today, today))
        
        conn.commit()
        conn.close()
        return payment_id
    except Exception as e:
        logger.error(f"Database error in log_payment: {e}")
        return None

def approve_user_payment(user_id, approved_by):
    """אישור תשלום משתמש והוספת SLH tokens"""
    try:
        conn = get_connection()
        c = conn.cursor()
        
        # קבלת פרטי התשלום
        c.execute('''SELECT slh_reward FROM payments 
                     WHERE user_id = ? AND status = 'pending' 
                     ORDER BY payment_date DESC LIMIT 1''', (user_id,))
        result = c.fetchone()
        slh_reward = result[0] if result else 1.0
        
        # עדכון משתמש - אישור תשלום והוספת SLH
        c.execute('''UPDATE users SET 
                     payment_verified = TRUE,
                     approved_by = ?,
                     approved_date = CURRENT_TIMESTAMP,
                     slh_tokens = slh_tokens + ?
                     WHERE user_id = ?''', (approved_by, slh_reward, user_id))
        
        # עדכון תשלום - סימון כמאושר
        c.execute('''UPDATE payments SET 
                     status = 'verified',
                     verified_by = ?,
                     verification_date = CURRENT_TIMESTAMP
                     WHERE user_id = ? AND status = 'pending' ''', (approved_by, user_id))
        
        conn.commit()
        conn.close()
        return True, slh_reward
    except Exception as e:
        logger.error(f"Database error in approve_user_payment: {e}")
        return False, 0

def get_user_slh_balance(user_id):
    """מחזיר את יתרת ה-SLH tokens של משתמש"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT slh_tokens FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        logger.error(f"Error getting user SLH balance: {e}")
        return 0

def get_user_referral_count(user_id):
    """קבלת מספר הרפראלים של משתמש"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT referral_count FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        logger.error(f"Database error in get_user_referral_count: {e}")
        return 0
