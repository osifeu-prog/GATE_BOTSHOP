import os
import logging
import json
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
import threading
import time

# הגדרת משתני הסביבה
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', 'https://web-production-b425.up.railway.app') + '/webhook'
MAIN_GROUP_LINK = "https://t.me/+HIzvM8sEgh1kNWY0"
ADMIN_GROUP_ID = "-1002141887344"  # ID מספרי של קבוצת הניהול
PAYMENT_CONFIRMATION_GROUP = "-1002141887344"  # ID קבוצת אישורי תשלום (אותה קבוצה)
MAIN_COMMUNITY_GROUP = "-1002141887344"  # הקבוצה הראשית להצטרפות
ADMIN_USER_ID = "224223270"  # ID שלך - Osif

# states לשיחת צור קשר
CHOOSING, TYPING_CONTACT = range(2)

# הגדרת הלוגים
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- מילוני תרגום רב-לשוניים ---
TRANSLATIONS = {
    'he': {
        # כפתורים ראשיים
        'ecosystem': "🌟 סלה ללא גבולות - האקוסיסטם",
        'join_community': "💎 הצטרפות לקהילה - 39₪", 
        'investment': "🚀 השקעה בפרויקט SLH",
        'bot_development': "🤖 פיתוח בוטים לעסקים",
        'network_marketing': "📊 שיווק רשתי - 5 דורות",
        'our_projects': "🌐 הפרויקטים שלנו",
        'contact': "📞 צור קשר",
        'help': "🆘 עזרה ראשונה",
        'website': "🌐 אתר האינטרנט",
        
        # הודעות
        'welcome': "🌅 **ברוך הבא {name} למהפכה הכלכלית של סלה ללא גבולות!**\n\n_גילית את האקוסיסטם הטכנולוגי המתקדם ביותר בישראל שמשלב קריפטו, בוטים חכמים, ושיווק רשתי מתקדם_ ✨",
        'welcome_back': "**🏠 חזרת לתפריט הראשי**\n\n**💎 איך נוכל לעזור לך להצליח היום?**",
        
        # תשלומים
        'bank_transfer': "🏦 העברה בנקאית",
        'ton_payment': "💎 תשלום ב-TON", 
        'crypto_payment': "💰 תשלום בקריפטו נוסף",
        'payment_sent': "✅ שלחתי תשלום",
        'joining_bonuses': "🎁 בונוסי הצטרפות",
        
        # פרטי תשלום
        'bank_details': """
🏦 **העברה בנקאית:**
בנק: הפועלים
סניף: כפר גנים (153)
חשבון: 73462
מוטב: קאופמן צביקה
        """,
        'ton_details': """
💎 **תשלום ב-TON:**
`UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp`
        """,
        'crypto_details': """
💰 **תשלום בקריפטו נוסף (Ethereum):**
`0xEc43Fb4819b5DdCb11407DBE46B92a51c7d24B2b`
        """
    },
    'en': {
        # Main buttons
        'ecosystem': "🌟 Sela Without Borders - Ecosystem",
        'join_community': "💎 Join Community - 39₪", 
        'investment': "🚀 Invest in SLH Project",
        'bot_development': "🤖 Bot Development for Businesses",
        'network_marketing': "📊 Network Marketing - 5 Generations", 
        'our_projects': "🌐 Our Projects",
        'contact': "📞 Contact",
        'help': "🆘 Quick Help",
        'website': "🌐 Website",
        
        # Messages
        'welcome': "🌅 **Welcome {name} to the economic revolution of Sela Without Borders!**\n\n_You've discovered the most advanced technological ecosystem in Israel combining crypto, smart bots, and advanced network marketing_ ✨",
        'welcome_back': "**🏠 Back to Main Menu**\n\n**💎 How can we help you succeed today?**",
        
        # Payments
        'bank_transfer': "🏦 Bank Transfer",
        'ton_payment': "💎 Payment in TON", 
        'crypto_payment': "💰 Other Crypto Payment",
        'payment_sent': "✅ I Sent Payment",
        'joining_bonuses': "🎁 Joining Bonuses",
        
        # Payment details
        'bank_details': """
🏦 **Bank Transfer:**
Bank: Hapoalim
Branch: Kfar Ganim (153)
Account: 73462
Recipient: Kaufman Zvika
        """,
        'ton_details': """
💎 **Payment in TON:**
`UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp`
        """,
        'crypto_details': """
💰 **Other Crypto Payment (Ethereum):**
`0xEc43Fb4819b5DdCb11407DBE46B92a51c7d24B2b`
        """
    },
    'ru': {
        # Основные кнопки
        'ecosystem': "🌟 Села без границ - Экосистема",
        'join_community': "💎 Вступить в сообщество - 39₪", 
        'investment': "🚀 Инвестировать в проект SLH",
        'bot_development': "🤖 Разработка ботов для бизнеса",
        'network_marketing': "📊 Сетевой маркетинг - 5 поколений",
        'our_projects': "🌐 Наши проекты", 
        'contact': "📞 Контакты",
        'help': "🆘 Быстрая помощь",
        'website': "🌐 Веб-сайт",
        
        # Сообщения
        'welcome': "🌅 **Добро пожаловать {name} в экономическую революцию Села без границ!**\n\n_Вы открыли самую передовую технологическую экосистему в Израиле, сочетающую крипто, умные боты и продвинутый сетевой маркетинг_ ✨",
        'welcome_back': "**🏠 Вернуться в главное меню**\n\n**💎 Как мы можем помочь вам добиться успеха сегодня?**",
        
        # Платежи
        'bank_transfer': "🏦 Банковский перевод",
        'ton_payment': "💎 Оплата в TON", 
        'crypto_payment': "💰 Другая криптовалюта",
        'payment_sent': "✅ Я отправил платеж",
        'joining_bonuses': "🎁 Бонусы за вступление",
        
        # Детали платежей
        'bank_details': """
🏦 **Банковский перевод:**
Банк: Хапоалим
Филиал: Кфар Ганим (153)
Счет: 73462
Получатель: Кауфман Звика
        """,
        'ton_details': """
💎 **Оплата в TON:**
`UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp`
        """,
        'crypto_details': """
💰 **Оплата другой криптовалютой (Ethereum):**
`0xEc43Fb4819b5DdCb11407DBE46B92a51c7d24B2b`
        """
    },
    'ar': {
        # الأزرار الرئيسية
        'ecosystem': "🌟 سيلا بلا حدود - النظام البيئي",
        'join_community': "💎 الانضمام للمجتمع - 39₪", 
        'investment': "🚀 الاستثمار في مشروع SLH",
        'bot_development': "🤖 تطوير بوتات للأعمال",
        'network_marketing': "📊 التسويق الشبكي - 5 أجيال",
        'our_projects': "🌐 مشاريعنا",
        'contact': "📞 اتصل بنا", 
        'help': "🆘 مساعدة سريعة",
        'website': "🌐 موقع الويب",
        
        # الرسائل
        'welcome': "🌅 **مرحبًا {name} في الثورة الاقتصادية لسيلا بلا حدود!**\n\n_لقد اكتشفت النظام البيئي التكنولوجي الأكثر تقدمًا في إسرائيل الذي يجمع بين العملات المشفرة، البوتات الذكية، والتسويق الشبكي المتقدم_ ✨",
        'welcome_back': "**🏠 العودة إلى القائمة الرئيسية**\n\n**💎 كيف يمكننا مساعدتك على النجاح اليوم?**",
        
        # المدفوعات
        'bank_transfer': "🏦 تحويل بنكي",
        'ton_payment': "💎 الدفع بـ TON", 
        'crypto_payment': "💰 دفع بعملة مشفرة أخرى",
        'payment_sent': "✅ قمت بإرسال الدفع",
        'joining_bonuses': "🎁 مكافآت الانضمام",
        
        # تفاصيل الدفع
        'bank_details': """
🏦 **التحويل البنكي:**
البنك: هبوعليم
الفرع: كفار جانيم (153)
الحساب: 73462
المستلم: كاوفمان زفيكا
        """,
        'ton_details': """
💎 **الدفع بـ TON:**
`UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp`
        """,
        'crypto_details': """
💰 **الدفع بعملة مشفرة أخرى (Ethereum):**
`0xEc43Fb4819b5DdCb11407DBE46B92a51c7d24B2b`
        """
    }
}

def get_translation(lang, key, **kwargs):
    """מחזיר תרגום לפי שפה ומפתח"""
    if lang not in TRANSLATIONS:
        lang = 'he'  # ברירת מחדל לעברית
    translation = TRANSLATIONS[lang].get(key, TRANSLATIONS['he'].get(key, key))
    return translation.format(**kwargs) if kwargs else translation

def get_user_language(user_id):
    """מחזיר את שפת המשתמש מהמסד נתונים"""
    try:
        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
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
        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
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

# --- מסד נתונים מתקדם ---
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
                  slh_tokens REAL DEFAULT 0)''')  # הוספת עמודת SLH tokens
    
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
                  slh_reward REAL DEFAULT 0)''')  # הוספת עמודת תגמול SLH
    
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
                  added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

init_db()

# --- פונקציות מסד נתונים ---
def log_user_activity(user_id, username, first_name, last_name, action_type, action_details=""):
    """רישום פעילות משתמש במסד הנתונים"""
    try:
        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
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

def log_payment(user_id, payment_type, amount, proof_text=""):
    """רישום תשלום במסד הנתונים"""
    try:
        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
        c = conn.cursor()
        
        # חישוב תגמול SLH (39₪ = 1 SLH)
        slh_reward = 1.0  # כל תשלום של 39₪ מזכה ב-1 SLH
        
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

def add_referral(referrer_id, referred_id, level=1, earned_amount=0):
    """הוספת רפראל חדש"""
    try:
        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
        c = conn.cursor()
        
        c.execute('''INSERT INTO referrals 
                     (referrer_id, referred_id, level, earned_amount)
                     VALUES (?, ?, ?, ?)''', (referrer_id, referred_id, level, earned_amount))
        
        # עדכון ספירת הרפראלים עבור המשתתף
        c.execute('''UPDATE users SET referral_count = referral_count + 1, 
                     total_earned = total_earned + ? 
                     WHERE user_id = ?''', (earned_amount, referrer_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database error in add_referral: {e}")
        return False

def get_user_stats():
    """קבלת סטטיסטיקות משתמשים"""
    try:
        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
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
        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
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

def get_user_referral_count(user_id):
    """קבלת מספר הרפראלים של משתמש"""
    try:
        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
        c = conn.cursor()
        
        c.execute("SELECT referral_count FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        conn.close()
        
        return result[0] if result else 0
    except Exception as e:
        logger.error(f"Database error in get_user_referral_count: {e}")
        return 0

def get_user_referrals(user_id):
    """קבלת רשימת הרפראלים של משתמש"""
    try:
        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
        c = conn.cursor()
        
        c.execute('''SELECT u.first_name, u.username, r.timestamp 
                     FROM referrals r
                     JOIN users u ON r.referred_id = u.user_id
                     WHERE r.referrer_id = ?
                     ORDER BY r.timestamp DESC''', (user_id,))
        
        referrals = c.fetchall()
        conn.close()
        return referrals
    except Exception as e:
        logger.error(f"Database error in get_user_referrals: {e}")
        return []

def approve_user_payment(user_id, approved_by):
    """אישור תשלום משתמש והוספת SLH tokens"""
    try:
        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
        c = conn.cursor()
        
        # קבלת פרטי התשלום
        c.execute('''SELECT slh_reward FROM payments 
                     WHERE user_id = ? AND status = 'pending' 
                     ORDER BY payment_date DESC LIMIT 1''', (user_id,))
        result = c.fetchone()
        slh_reward = result[0] if result else 1.0  # ברירת מחדל 1 SLH
        
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

def get_pending_payments():
    """קבלת רשימת תשלומים ממתינים"""
    try:
        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
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

def save_group(group_id, title, group_type):
    """שומר קבוצה במסד הנתונים"""
    try:
        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO groups 
                     (group_id, title, type) 
                     VALUES (?, ?, ?)''', (group_id, title, group_type))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error saving group: {e}")
        return False

def get_all_groups():
    """מחזיר את כל הקבוצות מהמסד נתונים"""
    try:
        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT group_id, title, type FROM groups")
        groups = c.fetchall()
        conn.close()
        return groups
    except Exception as e:
        logger.error(f"Error getting groups: {e}")
        return []

def get_user_slh_balance(user_id):
    """מחזיר את יתרת ה-SLH tokens של משתמש"""
    try:
        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT slh_tokens FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        logger.error(f"Error getting user SLH balance: {e}")
        return 0

# אתחול הבוט וה-dispatcher
try:
    bot = Bot(token=BOT_TOKEN)
    dispatcher = Dispatcher(bot, None, workers=4)
    logger.info("Bot and dispatcher initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize bot: {e}")
    raise

# --- פונקציות מתקדמות לניהול קבוצות ---
def get_bot_all_chats():
    """מחזיר את כל הצ'אטים שהבוט חבר בהם - כולל קבוצות וערוצים"""
    try:
        groups_from_db = get_all_groups()
        return groups_from_db
    except Exception as e:
        logger.error(f"Error getting all bot chats: {e}")
        return []

def send_message_to_group(group_id, message, image_file_id=None):
    """שולח הודעה לקבוצה לפי ID"""
    try:
        if image_file_id:
            bot.send_photo(
                chat_id=group_id, 
                photo=image_file_id, 
                caption=message,
                parse_mode='Markdown'
            )
        else:
            bot.send_message(
                chat_id=group_id, 
                text=message, 
                parse_mode='Markdown'
            )
        logger.info(f"Message sent to group {group_id}: {message[:50]}...")
        return True
    except Exception as e:
        logger.error(f"Failed to send message to group {group_id}: {e}")
        return False

def send_admin_alert(message, image_file_id=None):
    """שולח התראה לקבוצת הניהול"""
    try:
        if image_file_id:
            bot.send_photo(
                chat_id=ADMIN_GROUP_ID, 
                photo=image_file_id, 
                caption=message,
                parse_mode='Markdown'
            )
        else:
            bot.send_message(
                chat_id=ADMIN_GROUP_ID, 
                text=message, 
                parse_mode='Markdown'
            )
        logger.info(f"Admin alert sent: {message[:50]}...")
        return True
    except Exception as e:
        logger.warning(f"Admin alert failed: {e} - Message: {message[:100]}")
        # ננסה לשלוח לאדמין ישירות
        try:
            bot.send_message(
                chat_id=ADMIN_USER_ID,
                text=f"⚠️ Admin group failed: {e}\n\nMessage: {message}",
                parse_mode='Markdown'
            )
        except:
            pass
        return False

def send_payment_confirmation_to_group(user_id, user_name, payment_type, amount, proof_text="", image_file_id=None):
    """שולח אישור תשלום לקבוצת התשלומים"""
    try:
        payment_message = f"💰 **אישור תשלום חדש!**\n👤 ממשתמש: {user_name}\n🆔 ID: `{user_id}`\n💳 סוג: {payment_type}\n💸 סכום: {amount}₪"
        
        if proof_text:
            payment_message += f"\n📝 פרטים: {proof_text}"
        
        # שליחה לקבוצת התשלומים
        success = send_message_to_group(PAYMENT_CONFIRMATION_GROUP, payment_message, image_file_id)
        
        if success:
            logger.info(f"Payment confirmation sent to group for user {user_id}")
        else:
            logger.warning(f"Failed to send payment confirmation to group for user {user_id}")
            
        return success
    except Exception as e:
        logger.error(f"Error in send_payment_confirmation_to_group: {e}")
        return False

def log_user_interaction(chat_id, first_name, last_name, username, action, details=""):
    """רושם פעילות משתמש ושולח התראה לקבוצת הניהול"""
    user_info = f"🆔 ID: `{chat_id}`\n👤 שם: {first_name} {last_name}\n📛 משתמש: @{username if username else 'ללא'}"
    log_message = f"🔔 **פעילות חדשה בבוט**\n{user_info}\n📝 **פעולה:** {action}"
    
    if details:
        log_message += f"\n📋 **פרטים:** {details}"
    
    # רישום במסד הנתונים
    log_user_activity(chat_id, username, first_name, last_name, action, details)
    
    # שליחת התראה לקבוצת הניהול
    try:
        send_admin_alert(log_message)
    except Exception as e:
        logger.warning(f"Failed to send admin alert: {e}")

def send_payment_confirmation(user_id, user_name, payment_type, amount, proof_text="", image_file_id=None):
    """שולח אישור תשלום וקובע במסד נתונים"""
    payment_message = f"💰 **אישור תשלום חדש!**\n👤 ממשתמש: {user_name}\n🆔 ID: `{user_id}`\n💳 סוג: {payment_type}\n💸 סכום: {amount}₪"
    
    if proof_text:
        payment_message += f"\n📝 פרטים: {proof_text}"
    
    # רישום במסד הנתונים
    payment_id = log_payment(user_id, payment_type, amount, proof_text)
    
    # שליחת התראה לקבוצת הניהול
    admin_success = send_admin_alert(payment_message, image_file_id)
    
    # שליחה לקבוצת התשלומים
    group_success = send_payment_confirmation_to_group(user_id, user_name, payment_type, amount, proof_text, image_file_id)
    
    return admin_success or group_success

def send_contact_request(chat_id, user_name, contact_type, message):
    """שולח בקשת קשר לקבוצת הניהול"""
    contact_message = f"📞 **בקשת קשר חדשה!**\n👤 ממשתמש: {user_name}\n🆔 ID: `{chat_id}`\n📋 נושא: {contact_type}\n💬 הודעה: {message}"
    
    # רישום במסד הנתונים
    log_user_activity(chat_id, "", user_name, "", "contact_request", f"{contact_type}: {message}")
    
    # שליחת התראה
    try:
        send_admin_alert(contact_message)
        return True
    except Exception as e:
        logger.warning(f"Failed to send contact request: {e}")
        return False

# --- מקלדות רב-לשוניות ---
def get_main_keyboard(user_id):
    """מחזיר את המקלדת הראשית לפי שפת המשתמש"""
    lang = get_user_language(user_id)
    keyboard = [
        [InlineKeyboardButton(get_translation(lang, 'ecosystem'), callback_data='ecosystem_explanation')],
        [InlineKeyboardButton(get_translation(lang, 'join_community'), callback_data='join_community')],
        [InlineKeyboardButton(get_translation(lang, 'investment'), callback_data='investment')],
        [InlineKeyboardButton(get_translation(lang, 'bot_development'), callback_data='bot_development')],
        [InlineKeyboardButton(get_translation(lang, 'network_marketing'), callback_data='network_marketing')],
        [InlineKeyboardButton(get_translation(lang, 'our_projects'), callback_data='our_projects')],
        [InlineKeyboardButton(get_translation(lang, 'contact'), callback_data='contact'), 
         InlineKeyboardButton(get_translation(lang, 'help'), callback_data='help')],
        [InlineKeyboardButton(get_translation(lang, 'website'), url='https://slh-nft.com/')],
        [InlineKeyboardButton("🌐 שפה / Language", callback_data='change_language')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_language_keyboard():
    """מקלדת בחירת שפה"""
    keyboard = [
        [InlineKeyboardButton("🇮🇱 עברית", callback_data='lang_he')],
        [InlineKeyboardButton("🇺🇸 English", callback_data='lang_en')],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data='lang_ru')],
        [InlineKeyboardButton("🇸🇦 العربية", callback_data='lang_ar')],
        [InlineKeyboardButton("↩️ חזרה", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_payment_keyboard(user_id):
    """מחזיר את מקלדת אפשרויות התשלום לפי שפה"""
    lang = get_user_language(user_id)
    keyboard = [
        [InlineKeyboardButton(get_translation(lang, 'bank_transfer'), callback_data='payment_bank')],
        [InlineKeyboardButton(get_translation(lang, 'ton_payment'), callback_data='payment_ton')],
        [InlineKeyboardButton(get_translation(lang, 'crypto_payment'), callback_data='payment_crypto')],
        [InlineKeyboardButton(get_translation(lang, 'payment_sent'), callback_data='payment_sent')],
        [InlineKeyboardButton(get_translation(lang, 'joining_bonuses'), callback_data='joining_bonuses')],
        [InlineKeyboardButton("↩️ " + ("חזרה" if lang == 'he' else "Back" if lang == 'en' else "Назад" if lang == 'ru' else "رجوع"), callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard(user_id):
    """מקלדת חזרה בלבד"""
    lang = get_user_language(user_id)
    back_text = "חזרה" if lang == 'he' else "Back" if lang == 'en' else "Назад" if lang == 'ru' else "رجوع"
    keyboard = [
        [InlineKeyboardButton(f"↩️ {back_text}", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_network_marketing_keyboard(user_id):
    """מקלדת שיווק רשתי"""
    lang = get_user_language(user_id)
    keyboard = [
        [InlineKeyboardButton("💰 מודל 5 הדורות", callback_data='five_generations')],
        [InlineKeyboardButton("🎯 איך מתחילים להרוויח?", callback_data='how_to_earn')],
        [InlineKeyboardButton("📊 הלינק האישי שלי", callback_data='personal_link')],
        [InlineKeyboardButton("💎 הצטרפות עכשיו", callback_data='join_community')],
        [InlineKeyboardButton("↩️ " + ("חזרה" if lang == 'he' else "Back"), callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_contact_keyboard(user_id):
    """מקלדת צור קשר"""
    lang = get_user_language(user_id)
    keyboard = [
        [InlineKeyboardButton("💼 עסקים ושותפויות", callback_data='contact_business')],
        [InlineKeyboardButton("🚀 השקעה בפרויקט", callback_data='contact_investment')],
        [InlineKeyboardButton("🤖 פיתוח בוט", callback_data='contact_bot')],
        [InlineKeyboardButton("📞 תמיכה טכנית", callback_data='contact_support')],
        [InlineKeyboardButton("↩️ " + ("חזרה" if lang == 'he' else "Back"), callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_slh_balance_keyboard(user_id):
    """מקלדת עם יתרת SLH"""
    lang = get_user_language(user_id)
    slh_balance = get_user_slh_balance(user_id)
    keyboard = [
        [InlineKeyboardButton(f"💎 יתרת SLH: {slh_balance}", callback_data='slh_balance')],
        [InlineKeyboardButton("↩️ חזרה", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- מטבעות הטלגרם רב-לשוניים ---
def start(update: Update, context: CallbackContext) -> None:
    """מטפל בפקודה /start - רב-לשוני"""
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id

        # רישום מפורט של המשתמש ושליחת לוג
        log_user_interaction(
            chat_id=chat_id,
            first_name=user.first_name or "לא צוין",
            last_name=user.last_name or "",
            username=user.username or "לא צוין",
            action="התחיל שיחה עם הבוט (/start)",
            details=f"User ID: {user.id}, Language: {user.language_code}, Chat Type: {update.message.chat.type if update.message else 'callback'}"
        )

        # אם זו קבוצה, נשמור את הקבוצה במסד הנתונים
        if update.message and update.message.chat.type in ['group', 'supergroup']:
            chat = update.message.chat
            save_group(chat.id, chat.title, chat.type)
            
            # הודעה מותאמת לקבוצה - רק אם זו פקודת start מפורשת
            if update.message.text and '/start' in update.message.text:
                update.message.reply_text(
                    "🤖 הבוט פעיל בקבוצה זו!\n\n"
                    f"🆔 **ID הקבוצה:** `{chat.id}`\n"
                    "👑 **לאדמין:** השתמש ב-`/chatid` כדי לראות את כל הקבוצות.\n"
                    "👤 **למשתמשים:** שלחו /start בפרטי כדי להתחיל."
                )
            return

        # שליחת תמונה עם הודעת ברוך הבא
        welcome_image_url = "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2032&q=80"
        
        try:
            if update.message:
                update.message.reply_photo(
                    photo=welcome_image_url,
                    caption=get_translation(get_user_language(user.id), 'welcome', name=user.first_name),
                    parse_mode='Markdown',
                    reply_markup=get_main_keyboard(user.id)
                )
            else:
                update.callback_query.message.reply_photo(
                    photo=welcome_image_url,
                    caption=get_translation(get_user_language(user.id), 'welcome', name=user.first_name),
                    parse_mode='Markdown',
                    reply_markup=get_main_keyboard(user.id)
                )
            return
        except Exception as e:
            logger.warning(f"Could not send welcome image: {e}")

        # אם לא הצליחה התמונה, שולח טקסט בלבד
        if update.message:
            update.message.reply_text(
                get_translation(get_user_language(user.id), 'welcome', name=user.first_name),
                reply_markup=get_main_keyboard(user.id),
                parse_mode='Markdown'
            )
        else:
            update.callback_query.message.reply_text(
                get_translation(get_user_language(user.id), 'welcome', name=user.first_name),
                reply_markup=get_main_keyboard(user.id),
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        if update.message:
            update.message.reply_text("❌ אירעה שגיאה. אנא נסה שוב.")

def chatid(update: Update, context: CallbackContext) -> None:
    """שולח את ה-ID של הקבוצה הנוכחית או רשימת כל הקבוצות"""
    try:
        user = update.effective_user
        
        # בדיקה אם המשתמש הוא אדמין
        if str(user.id) != ADMIN_USER_ID:
            update.message.reply_text("❌ אתה לא מורשה להשתמש בפקודה זו.")
            return

        # אם הפקודה נשלחה בקבוצה, שלח את ה-ID של הקבוצה הנוכחית
        if update.message.chat.type in ['group', 'supergroup']:
            chat_id = update.message.chat.id
            chat_title = update.message.chat.title
            message = f"🆔 **קבוצה:** {chat_title}\n**ID:** `{chat_id}`\n**סוג:** {update.message.chat.type}"
            
            # שמירת הקבוצה במסד הנתונים
            save_group(chat_id, chat_title, update.message.chat.type)
            message += f"\n\n✅ **הקבוצה נשמרה במסד הנתונים!**"
            
            update.message.reply_text(message, parse_mode='Markdown')
        else:
            # אם נשלחה בצ'אט פרטי, שלח את רשימת כל הקבוצות
            all_chats = get_bot_all_chats()
            
            if all_chats:
                message = f"📊 **כל הצ'אטים שהבוט חבר בהם ({len(all_chats)}):**\n\n"
                
                for i, chat in enumerate(all_chats, 1):
                    chat_id = chat[0]
                    chat_title = chat[1] 
                    chat_type = chat[2] if len(chat) > 2 else "unknown"
                    message += f"{i}. **{chat_title}**\n   ID: `{chat_id}` | Type: {chat_type}\n\n"
                
                message += "💡 **הערה:** ייתכן שיש צ'אטים נוספים שהבוט חבר בהם אך עוד לא נרשמו במערכת."
                
            else:
                message = "❌ הבוט לא חבר באף צ'אט שנרשם במערכת.\n\n"
                message += "💡 **טיפים:**\n"
                message += "• הזמן את הבוט לקבוצה ונסה שוב\n"
                message += "• שלח /start בקבוצה כדי לרשום אותה\n"
                message += "• השתמש ב-/chatid בתוך קבוצה כדי לרשום אותה"
            
            update.message.reply_text(message, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Error in chatid command: {e}")
        update.message.reply_text("❌ אירעה שגיאה בקבלת ID הקבוצה.")

def admin(update: Update, context: CallbackContext) -> None:
    """פקודת אדמין - מציגה סטטיסטיקות וניהול"""
    try:
        user = update.effective_user
        
        # בדיקה אם המשתמש הוא אדמין
        if str(user.id) != ADMIN_USER_ID:
            update.message.reply_text("❌ אתה לא מורשה להשתמש בפקודה זו.")
            return

        stats = get_user_stats()
        groups = get_bot_all_chats()
        pending_payments = get_pending_payments()
        
        message = "👑 **פאנל ניהול - SLH Bot**\n\n"
        message += f"**👤 אדמין:** Osif (ID: {ADMIN_USER_ID})\n\n"
        
        message += f"📊 **סטטיסטיקות:**\n"
        message += f"• 👥 משתמשים רשומים: {stats['total_users']}\n"
        message += f"• 🔥 פעילים היום: {stats['active_today']}\n"
        message += f"• 📈 פעולות היום: {stats['actions_today']}\n"
        message += f"• ✅ תשלומים מאושרים: {stats['verified_payments']}\n"
        message += f"• ⏳ תשלומים ממתינים: {stats['pending_payments']}\n\n"
        
        message += f"📁 **קבוצות ({len(groups)}):**\n"
        for group in groups[:8]:  # מציג עד 8 קבוצות
            message += f"• {group[1]} (`{group[0]}`)\n"
        if len(groups) > 8:
            message += f"• ... ועוד {len(groups) - 8} קבוצות\n\n"
        else:
            message += "\n"
        
        message += f"💰 **תשלומים ממתינים:** {len(pending_payments)}\n\n"
        
        message += "🔧 **פקודות ניהול:**\n"
        message += "• `/chatid` - הצג ID קבוצה/רשימת קבוצות\n"
        message += "• `/admin` - פאנל ניהול זה\n"
        message += "• `/broadcast` - שליחת הודעה לכל המשתמשים\n"
        message += "• `/group_broadcast` - שליחת הודעה לכל הקבוצות\n"
        message += "• 🌐 https://web-production-b425.up.railway.app/admin?password=slh2025 - פאנל ניהול מתקדם\n\n"
        
        message += "🚀 **לאסוף צ'אטים נוספים:**\n"
        message += "1. הזמן את הבוט לקבוצה\n"
        message += "2. שלח `/start` או `/chatid` בקבוצה\n"
        message += "3. הקבוצה תירשם אוטומטית\n"
        
        update.message.reply_text(message, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Error in admin command: {e}")
        update.message.reply_text("❌ אירעה שגיאה בפקודת האדמין.")

def broadcast(update: Update, context: CallbackContext) -> None:
    """שליחת הודעה לכל המשתמשים"""
    try:
        user = update.effective_user
        
        # בדיקה אם המשתמש הוא אדמין
        if str(user.id) != ADMIN_USER_ID:
            update.message.reply_text("❌ אתה לא מורשה להשתמש בפקודה זו.")
            return

        # בדיקה אם יש טקסט להודעה
        if not context.args:
            update.message.reply_text("❌ שימוש: /broadcast <הודעה>")
            return

        message = " ".join(context.args)
        
        # קבלת כל המשתמשים
        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT user_id FROM users")
        users = c.fetchall()
        conn.close()
        
        sent_count = 0
        failed_count = 0
        
        for user_tuple in users:
            user_id = user_tuple[0]
            try:
                bot.send_message(
                    chat_id=user_id,
                    text=f"📢 **הודעה מהמערכת:**\n\n{message}",
                    parse_mode='Markdown'
                )
                sent_count += 1
                time.sleep(0.1)  # מניעת הגבלת שיעור
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to send broadcast to {user_id}: {e}")
        
        update.message.reply_text(
            f"✅ **שידור הושלם!**\n\n"
            f"✅ נשלח בהצלחה: {sent_count}\n"
            f"❌ נכשל: {failed_count}\n"
            f"📊 סה\"כ: {len(users)}"
        )
        
    except Exception as e:
        logger.error(f"Error in broadcast command: {e}")
        update.message.reply_text("❌ אירעה שגיאה בשליחת השידור.")

def group_broadcast(update: Update, context: CallbackContext) -> None:
    """שליחת הודעה לכל הקבוצות"""
    try:
        user = update.effective_user
        
        # בדיקה אם המשתמש הוא אדמין
        if str(user.id) != ADMIN_USER_ID:
            update.message.reply_text("❌ אתה לא מורשה להשתמש בפקודה זו.")
            return

        # בדיקה אם יש טקסט להודעה
        if not context.args:
            update.message.reply_text("❌ שימוש: /group_broadcast <הודעה>")
            return

        message = " ".join(context.args)
        
        # קבלת כל הקבוצות
        groups = get_all_groups()
        
        sent_count = 0
        failed_count = 0
        
        for group in groups:
            group_id = group[0]
            group_name = group[1]
            try:
                bot.send_message(
                    chat_id=group_id,
                    text=f"📢 **הודעה מהמערכת:**\n\n{message}",
                    parse_mode='Markdown'
                )
                sent_count += 1
                time.sleep(0.1)  # מניעת הגבלת שיעור
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to send group broadcast to {group_name} ({group_id}): {e}")
        
        update.message.reply_text(
            f"✅ **שידור לקבוצות הושלם!**\n\n"
            f"✅ נשלח בהצלחה: {sent_count}\n"
            f"❌ נכשל: {failed_count}\n"
            f"📊 סה\"כ קבוצות: {len(groups)}"
        )
        
    except Exception as e:
        logger.error(f"Error in group_broadcast command: {e}")
        update.message.reply_text("❌ אירעה שגיאה בשליחת השידור לקבוצות.")

def handle_group_add(update: Update, context: CallbackContext) -> None:
    """מטפל כאשר הבוט מתווסף לקבוצה"""
    try:
        chat = update.effective_chat
        new_members = update.message.new_chat_members
        
        # בדיקה אם הבוט הוא אחד מה-new members
        bot_id = context.bot.id
        if any(member.id == bot_id for member in new_members):
            # רישום הקבוצה במסד הנתונים
            save_group(chat.id, chat.title, chat.type)
            
            # שליחת הודעה לקבוצה
            update.message.reply_text(
                "🤖 תודה שהוספתם אותי לקבוצה! אני כאן כדי לסייע.\n"
                "להפעלתי, שלחו /start בפרטי.\n\n"
                f"🆔 **ID הקבוצה:** `{chat.id}`\n"
                "👑 **לאדמין:** השתמש ב-`/chatid` כדי לראות את כל הקבוצות."
            )
            
            # שליחת התראה לאדמין
            send_admin_alert(f"🚀 הבוט נוסף לקבוצה חדשה: {chat.title} (ID: `{chat.id}`, Type: {chat.type})")
    except Exception as e:
        logger.error(f"Error in handle_group_add: {e}")

def handle_group_activity(update: Update, context: CallbackContext) -> None:
    """מטפל בכל פעילות בקבוצות ורושם את הקבוצה"""
    try:
        if update.message and update.message.chat.type in ['group', 'supergroup']:
            chat = update.message.chat
            # רישום הקבוצה במסד הנתונים
            save_group(chat.id, chat.title, chat.type)
            
            # לוג לצורך ניפוי באגים
            logger.info(f"Group activity detected: {chat.title} (ID: {chat.id})")
            
    except Exception as e:
        logger.error(f"Error in handle_group_activity: {e}")

def language_handler(update: Update, context: CallbackContext) -> None:
    """מטפל בבחירת שפה"""
    query = update.callback_query
    query.answer()
    
    user_id = query.from_user.id
    lang_code = query.data.replace('lang_', '')
    
    # שמירת השפה במסד נתונים
    set_user_language(user_id, lang_code)
    
    # הודעת אישור לפי שפה
    confirmation_messages = {
        'he': "✅ שפת הממשק שונתה לעברית",
        'en': "✅ Interface language changed to English", 
        'ru': "✅ Язык интерфейса изменен на русский",
        'ar': "✅ تم تغيير لغة الواجهة إلى العربية"
    }
    
    query.edit_message_text(
        text=confirmation_messages.get(lang_code, "Language changed"),
        reply_markup=get_main_keyboard(user_id)
    )

def safe_edit_message(query, text, reply_markup=None, parse_mode='Markdown'):
    """פונקציה בטוחה לעריכת הודעה עם טיפול בשגיאות"""
    try:
        # בדיקה אם יש טקסט להודעה
        if not query.message.text and not query.message.caption:
            # אם אין טקסט, שולח הודעה חדשה
            return query.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        
        query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        return True
    except Exception as e:
        if "Message is not modified" in str(e):
            logger.debug("Message not modified - same content")
            return True
        else:
            logger.error(f"Error editing message: {e}")
            # ננסה לשלוח הודעה חדשה במקום
            try:
                query.message.reply_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
                return True
            except Exception as e2:
                logger.error(f"Failed to send new message: {e2}")
                return False

def button_handler(update: Update, context: CallbackContext) -> None:
    """מטפל בלחיצות על כפתורים - רב-לשוני"""
    query = update.callback_query
    
    try:
        query.answer()
    except Exception as e:
        logger.warning(f"Could not answer callback query: {e}")

    try:
        user = query.from_user
        user_id = user.id
        lang = get_user_language(user_id)
        action_details = f"לחץ על: {query.data}"
        
        # רישום פעילות מפורט
        log_user_activity(
            user.id, 
            user.username, 
            user.first_name, 
            user.last_name or "",
            "button_click", 
            action_details
        )

        if query.data == 'change_language':
            language_text = "🌐 **בחר שפה / Choose language**\n\nSelect your preferred language:"
            safe_edit_message(query, language_text, get_language_keyboard())
            return

        elif query.data.startswith('lang_'):
            language_handler(update, context)
            return

        elif query.data == 'refresh_groups':
            # רענון רשימת הקבוצות
            groups = get_all_groups()
            if groups:
                groups_list = "\n".join([f"• {group[1]} (ID: `{group[0]}`, Type: {group[2]})" for group in groups])
                message = f"📊 **קבוצות שהבוט חבר בהן ({len(groups)}):**\n\n{groups_list}"
                
                keyboard = [[InlineKeyboardButton("🔄 רענון", callback_data='refresh_groups')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                safe_edit_message(query, message, reply_markup)
            else:
                message = "❌ הבוט לא חבר באף קבוצה במסד הנתונים.\n\n💡 **טיפ:** הזמן את הבוט לקבוצה ונסה שוב."
                safe_edit_message(query, message)
            return

        elif query.data == 'ecosystem_explanation':
            ecosystem_texts = {
                'he': """
**🌟 סלה ללא גבולות - האקוסיסטם הטכנולוגי השלם**

**🏗️ המבנה הייחודי שלנו:**

**💎 ליבת המערכת - מטבע SLH**
אנחנו יצרנו מטבע קריפטו ייחודי **SLH** עם ערך אמיתי וצמיחה מתוכננת:
• **ערך נוכחי:** 444₪ ל-SLH 1
• **חלוקה למצטרפים:** כל member מקבל SLH 1 (39₪ מידית + השאר בהדרגה)
• **utility אמיתי:** משמש לתשלומים בכל הפלטפורמות שלנו
• **צמיחה אורגנית:** הערך עולה עם גידול הקהילה

**🚀 4 רכיבי הליבה:**

**1. 🤖 Botshop - פלטפורמת הבוטים**
• בוטים אוטומטיים לניהול קהילות
• מערכות תשלום ואימות
• אינטגרציה עם כל המערכות

**2. 💰 SLH Coin - המערכת הפיננסית**
• מטבע utility עם שימושים אמיתיים
• חוזים חכמים אוטומטיים
• מסחר וארנקים דיגיטליים

**3. 🎨 NFT & Digital Assets**
• שוק NFT לנכסים דיגיטליים
• פלטפורמת מסחר מתקדמת
• קהילת יוצרים ומשקיעים

**4. 📈 Network Marketing**
• שיווק רשתי ל-5 דורות
• הכנסות פסיביות אוטומטיות
• מערכת דוחות מתקדמת
                """,
                'en': """
**🌟 Sela Without Borders - The Complete Technological Ecosystem**

**🏗️ Our Unique Structure:**

**💎 System Core - SLH Coin**
We created a unique cryptocurrency **SLH** with real value and planned growth:
• **Current value:** 444₪ per SLH 1
• **Distribution to members:** Every member receives SLH 1 (39₪ immediately + the rest gradually)
• **Real utility:** Used for payments across all our platforms
• **Organic growth:** Value increases with community growth

**🚀 4 Core Components:**

**1. 🤖 Botshop - Bot Platform**
• Automated bots for community management
• Payment and verification systems
• Integration with all systems

**2. 💰 SLH Coin - Financial System**
• Utility coin with real uses
• Automatic smart contracts
• Trading and digital wallets

**3. 🎨 NFT & Digital Assets**
• NFT market for digital assets
• Advanced trading platform
• Community of creators and investors

**4. 📈 Network Marketing**
• 5-generation network marketing
• Automatic passive income
• Advanced reporting system
                """,
                'ru': """
**🌟 Села без границ - Полная технологическая экосистема**

**🏗️ Наша уникальная структура:**

**💎 Ядро системы - Монета SLH**
Мы создали уникальную криптовалюту **SLH** с реальной стоимостью и плановым ростом:
• **Текущая стоимость:** 444₪ за SLH 1
• **Распределение участникам:** Каждый участник получает SLH 1 (39₪ сразу + остальное постепенно)
• **Реальная полезность:** Используется для платежей на всех наших платформах
• **Органический рост:** Стоимость растет с ростом сообщества

**🚀 4 Основных компонента:**

**1. 🤖 Botshop - Платформа ботов**
• Автоматизированные боты для управления сообществами
• Системы платежей и проверки
• Интеграция со всеми системами

**2. 💰 SLH Coin - Финансовая система**
• Утилитарная монета с реальным использованием
• Автоматические смарт-контракты
• Торговля и цифровые кошельки

**3. 🎨 NFT & Digital Assets**
• Рынок NFT для цифровых активов
• Продвинутая торговая платформа
• Сообщество создателей и инвесторов

**4. 📈 Network Marketing**
• Сетевой маркетинг 5 поколений
• Автоматический пассивный доход
• Продвинутая система отчетности
                """,
                'ar': """
**🌟 سيلا بلا حدود - النظام البيئي التكنولوجي الكامل**

**🏗️ هيكلنا الفريد:**

**💎 نواة النظام - عملة SLH**
لقد أنشأنا عملة مشفرة فريدة **SLH** بقيمة حقيقية ونمو مخطط:
• **القيمة الحالية:** 444₪ لكل SLH 1
• **توزيع للأعضاء:** كل عضو يحصل على SLH 1 (39₪ فورًا والباقي تدريجيًا)
• **فائدة حقيقية:** تستخدم للدفع عبر جميع منصاتنا
• **نمو عضوي:** القيمة تزداد مع نمو المجتمع

**🚀 4 مكونات أساسية:**

**1. 🤖 Botshop - منصة البوتات**
• بوتات آلية لإدارة المجتمعات
• أنظمة دفع وتحقق
• تكامل مع جميع الأنظمة

**2. 💰 SLH Coin - النظام المالي**
• عملة utility ذات استخدامات حقيقية
• عقود ذكية آلية
• تداول ومحافظ رقمية

**3. 🎨 NFT & Digital Assets**
• سوق NFT للأصول الرقمية
• منصة تداول متقدمة
• مجتمع المبدعين والمستثمرين

**4. 📈 Network Marketing**
• تسويق شبكي لـ 5 أجيال
• دخل سلبي آلي
• نظام تقارير متقدم
                """
            }
            safe_edit_message(query, ecosystem_texts.get(lang, ecosystem_texts['he']), get_back_keyboard(user_id))

        elif query.data == 'join_community':
            join_texts = {
                'he': """
**💎 הצטרפות לקהילת סלה ללא גבולות**

**🎯 מה באמת קונה ה-39₪ שלך?**

זו לא "עלות" - זו **השקעה בנכס דיגיטלי** שמניב הכנסות!

**💼 חבילת הערך המלאה:**

**1. 💰 נכס דיגיטלי - SLH Coin**
• **SLH 1** בשווי 444₪ - 39₪ מידית, השאר בהדרגה
• מטבע utility עם שימושים אמיתיים
• פוטנציאל צמיחה עם גידול הקהילה

**2. 🎯 לינק שיתוף אישי**
• מניב 10% מכל מצטרף חדש דרך הלינק שלך
• הכנסה פסיבית מ-5 דורות
• מערכת דוחות ואימות אוטומטית

**3. 🌐 גישה לכל המערכות**
• פלטפורמת הבוטים המתקדמת
• קהילת VIP עם אנשי עסקים
• הדרכות והכשרות מקצועיות
• תמיכה טכנית 24/7

**4. 🚀 הזדמנויות עסקיות**
• שירותי פיתוח בוטים (בתשלום נוסף)
• השקעה בפרויקטים נוספים
• שותפויות אסטרטגיות
• נטרוקינג איכותי
                """,
                'en': """
**💎 Joining Sela Without Borders Community**

**🎯 What does your 39₪ actually buy?**

This is not a "cost" - it's an **investment in a digital asset** that generates income!

**💼 Complete Value Package:**

**1. 💰 Digital Asset - SLH Coin**
• **SLH 1** worth 444₪ - 39₪ immediately, the rest gradually
• Utility coin with real uses
• Growth potential with community growth

**2. 🎯 Personal Sharing Link**
• Generates 10% from every new member
• Passive income from 5 generations
• Automated reporting and verification system

**3. 🌐 Access to All Systems**
• Advanced bot platform
• VIP community with business people
• Professional training and guidance
• 24/7 technical support

**4. 🚀 Business Opportunities**
• Bot development services (additional payment)
• Investment in additional projects
• Strategic partnerships
• Quality networking
                """,
                'ru': """
**💎 Вступление в сообщество Села без границ**

**🎯 Что на самом деле покупают ваши 39₪?**

Это не "стоимость" - это **инвестиция в цифровой актив**, который приносит доход!

**💼 Полный пакет ценностей:**

**1. 💰 Цифровой актив - Монета SLH**
• **SLH 1** стоимостью 444₪ - 39₪ сразу, остальное постепенно
• Утилитарная монета с реальным использованием
• Потенциал роста с ростом сообщества

**2. 🎯 Персональная ссылка для приглашений**
• Приносит 10% от каждого нового участника
• Пассивный доход от 5 поколений
• Автоматизированная система отчетности и проверки

**3. 🌐 Доступ ко всем системам**
• Продвинутая платформа ботов
• VIP сообщество с бизнесменами
• Профессиональное обучение и руководство
• Техническая поддержка 24/7

**4. 🚀 Бизнес-возможности**
• Услуги разработки ботов (дополнительная оплата)
• Инвестиции в дополнительные проекты
• Стратегические партнерства
• Качественный нетворкинг
                """,
                'ar': """
**💎 الانضمام إلى مجتمع سيلا بلا حدود**

**🎯 ما الذي تشتريه 39₪ حقًا؟**

هذا ليس "تكلفة" - إنه **استثمار في أصل رقمي** يدر دخلاً!

**💼 باقة القيمة الكاملة:**

**1. 💰 أصل رقمي - عملة SLH**
• **SLH 1** بقيمة 444₪ - 39₪ فورًا، الباقي تدريجيًا
• عملة utility ذات استخدامات حقيقية
• إمكانية النمو مع نمو المجتمع

**2. 🎯 رابط مشاركة شخصي**
• يدر 10% من كل عضو جديد
• دخل سلبي من 5 أجيال
• نظام تقارير وتحقق آلي

**3. 🌐 الوصول لجميع الأنظمة**
• منصة بوتات متقدمة
• مجتمع VIP مع رجال الأعمال
• تدريبات وإرشادات مهنية
• دعم فني 24/7

**4. 🚀 فرص أعمال**
• خدمات تطوير بوتات (دفع إضافي)
• استثمار في مشاريع إضافية
• شراكات استراتيجية
• شبكة علاقات نوعية
                """
            }
            safe_edit_message(query, join_texts.get(lang, join_texts['he']), get_payment_keyboard(user_id))

        elif query.data == 'payment_bank':
            bank_text = get_translation(lang, 'bank_details')
            safe_edit_message(query, bank_text, get_payment_keyboard(user_id))

        elif query.data == 'payment_ton':
            ton_text = get_translation(lang, 'ton_details')
            safe_edit_message(query, ton_text, get_payment_keyboard(user_id))

        elif query.data == 'payment_crypto':
            crypto_text = get_translation(lang, 'crypto_details')
            safe_edit_message(query, crypto_text, get_payment_keyboard(user_id))

        elif query.data == 'payment_sent':
            payment_instructions = {
                'he': """
**✅ שלחתי תשלום - מה עכשיו?**

🚀 **מעולה! עכשיו נשאר רק לשלוח לנו את אישור התשלום:**

1. **אם שילמת בהעברה בנקאית:**
   • שלח צילום מסך של ההעברה
   • או הקלד את פרטי ההעברה

2. **אם שילמת בקריפטו:**
   • שלח צילום מסך של העסקה
   • או הקלד את hash העסקה

📸 **שלח עכשיו את אישור התשלום כאן בצ'אט**
ונחזור אליך עם קישור ההצטרפות תוך 24 שעות!

💎 **בונוס מיוחד:** כל תשלום מזכה אותך ב-**SLH 1** בשווי 444₪!
                """,
                'en': """
**✅ I Sent Payment - What Now?**

🚀 **Great! Now just send us the payment confirmation:**

1. **If you paid by bank transfer:**
   • Send a screenshot of the transfer
   • Or type the transfer details

2. **If you paid with crypto:**
   • Send a screenshot of the transaction
   • Or type the transaction hash

📸 **Send the payment confirmation now in this chat**
We'll get back to you with the joining link within 24 hours!

💎 **Special bonus:** Every payment earns you **SLH 1** worth 444₪!
                """,
                'ru': """
**✅ Я отправил платеж - что теперь?**

🚀 **Отлично! Теперь просто отправьте нам подтверждение платежа:**

1. **Если вы оплатили банковским переводом:**
   • Отправьте скриншот перевода
   • Или введите детали перевода

2. **Если вы оплатили криптовалютой:**
   • Отправьте скриншот транзакции
   • Или введите хэш транзакции

📸 **Отправьте подтверждение платежа сейчас в этом чате**
Мы вернемся к вам со ссылкой для вступления в течение 24 часов!

💎 **Специальный бонус:** Каждый платеж приносит вам **SLH 1** стоимостью 444₪!
                """,
                'ar': """
**✅ قمت بإرسال الدفع - ماذا الآن؟**

🚀 **ممتاز! الآن فقط أرسل لنا تأكيد الدفع:**

1. **إذا دفعت عن طريق التحويل البنكي:**
   • أرسل لقطة شاشة للتحويل
   • أو اكتب تفاصيل التحويل

2. **إذا دفعت بعملة مشفرة:**
   • أرسل لقطة شاشة للمعاملة
   • أو اكتب hash المعاملة

📸 **أرسل تأكيد الدفع الآن في هذه الدردشة**
سنتواصل معك برابط الانضمام خلال 24 ساعة!

💎 **مكافأة خاصة:** كل دفعة تمنحك **SLH 1** بقيمة 444₪!
                """
            }
            safe_edit_message(query, payment_instructions.get(lang, payment_instructions['he']), get_payment_keyboard(user_id))

        elif query.data == 'joining_bonuses':
            bonuses_text = {
                'he': """
**🎁 בונוסי הצטרפות - מה תקבל?**

**💎 תגמולי SLH:**
• **SLH 1** בשווי 444₪ - מיד עם אישור התשלום
• מטבע utility אמיתי עם שימושים במערכת
• פוטנציאל צמיחה עם גידול הקהילה

**🚀 גישה מלאה:**
• קישור להצטרפות לקהילת VIP
• הלינק האישי שלך לשיתוף והכנסות
• הדרכה מלאה לשימוש במערכת

**📊 הכנסות פסיביות:**
• 10% מכל מצטרף חדש דרך הלינק שלך
• הכנסה מ-5 דורות של רפראלים
• דוחות מפורטים בזמן אמת

**👑 הטבות נוספות:**
• שיחת ייעוץ אישית
• גישה לכל החומרים וההדרכות
• תמיכה טכנית 24/7
                """,
                'en': """
**🎁 Joining Bonuses - What You'll Get?**

**💎 SLH Rewards:**
• **SLH 1** worth 444₪ - immediately upon payment confirmation
• Real utility coin with system uses
• Growth potential with community growth

**🚀 Full Access:**
• Link to join VIP community
• Your personal sharing link for earnings
• Complete system usage guidance

**📊 Passive Income:**
• 10% from every new member through your link
• Income from 5 generations of referrals
• Detailed real-time reports

**👑 Additional Benefits:**
• Personal consultation call
• Access to all materials and trainings
• 24/7 technical support
                """
            }
            safe_edit_message(query, bonuses_text.get(lang, bonuses_text['he']), get_payment_keyboard(user_id))

        elif query.data == 'slh_balance':
            slh_balance = get_user_slh_balance(user_id)
            balance_text = {
                'he': f"""
**💎 יתרת SLH שלך**

**🪙 כמות SLH:** {slh_balance}
**💰 שווי נוכחי:** {slh_balance * 444}₪
**🚀 סטטוס:** {'פעיל' if slh_balance > 0 else 'ממתין להצטרפות'}

**📈 מה אפשר לעשות עם SLH?**
• השתתפות בסטייקינג (בקרוב)
• תשלומים בתוך המערכת
• מסחר וניתוח (בפיתוח)
• הצבעות קהילתיות (עתידי)

**💡 טיפ:** כל מצטרף חדש דרך הלינק שלך מזכה אותך בעוד SLH!
                """,
                'en': f"""
**💎 Your SLH Balance**

**🪙 SLH Amount:** {slh_balance}
**💰 Current Value:** {slh_balance * 444}₪
**🚀 Status:** {'Active' if slh_balance > 0 else 'Pending joining'}

**📈 What can you do with SLH?**
• Participate in staking (coming soon)
• Payments within the system
• Trading and analysis (in development)
• Community voting (future)

**💡 Tip:** Every new member through your link earns you more SLH!
                """
            }
            safe_edit_message(query, balance_text.get(lang, balance_text['he']), get_slh_balance_keyboard(user_id))

        elif query.data == 'network_marketing':
            network_texts = {
                'he': """
**📊 שיווק רשתי - 5 דורות**

**💡 איך עובד המודל?**

**🎯 הלינק האישי שלך - מכונת ההכנסות האוטומטית**

לאחר ההצטרפות, תקבל **לינק שיתוף אישי ייחודי** שמזוהה רק איתך. כל פעילות שמתבצעת דרך הלינק הזה - מייצרת לך הכנסה אוטומטית!

**💰 מודל ההכנסות:**

**1. 💰 עמלות ישירות**
• **10%** מכל רכישה של מצטרף חדש דרך הלינק שלך
• תשלום אוטומטי ומיידי ב-SLH
• אין הגבלה על מספר המצטרפים

**2. 📈 עמלות דורות (5 דורות)**
• **דור 1:** 10% מהמצטרפים הישירים שלך
• **דור 2:** 5% מהמצטרפים שלהם
• **דור 3:** 3% מהמצטרפים הבאים
• **דור 4:** 2% מהדור הרביעי
• **דור 5:** 1% מהדור החמישי

**3. 🎯 יעד: 39 רפראלים לגישה חינם**
• לאחר 39 מצטרפים - גישה מלאה בחינם!
• הכנסה פסיבית לכל החיים
• צמיחה אקספוננציאלית
                """,
                'en': """
**📊 Network Marketing - 5 Generations**

**💡 How does the model work?**

**🎯 Your Personal Link - Automatic Income Machine**

After joining, you'll receive a **unique personal sharing link** that's identified only with you. Any activity through this link generates automatic income for you!

**💰 Income Model:**

**1. 💰 Direct Commissions**
• **10%** from every new member purchase through your link
• Automatic and immediate payment in SLH
• No limit on number of members

**2. 📈 Generation Commissions (5 Generations)**
• **Generation 1:** 10% from your direct members
• **Generation 2:** 5% from their members
• **Generation 3:** 3% from next members
• **Generation 4:** 2% from fourth generation
• **Generation 5:** 1% from fifth generation

**3. 🎯 Goal: 39 Referrals for Free Access**
• After 39 members - full access for free!
• Lifetime passive income
• Exponential growth
                """
            }
            safe_edit_message(query, network_texts.get(lang, network_texts['he']), get_network_marketing_keyboard(user_id))

        elif query.data == 'personal_link':
            user_ref_count = get_user_referral_count(user_id)
            personal_link_texts = {
                'he': f"""
**🎯 הלינק האישי שלך**

**📊 הסטטוס שלך:**
• **רפראלים:** {user_ref_count}/39
• **נותרו:** {39 - user_ref_count} להשלמה
• **הכנסות מצטברות:** {user_ref_count * 3.9:.2f}₪
• **SLH שנצבר:** {user_ref_count * 0.1:.1f}

**🔗 הלינק האישי שלך:**
`https://t.me/Buy_My_Shop_bot?start={user_id}`

**💡 טיפים לשיתוף:**
• שתף בפייסבוק, אינסטגרם, טיקטוק
• הסבר על ההזדמנות הכלכלית
• שתף בקבוצות טלגרם ווואטסאפ

**🎁 לאחר 39 רפראלים תקבל:**
• גישה מלאה בחינם!
• מעמד VIP בקהילה
• הטבות נוספות
                """,
                'en': f"""
**🎯 Your Personal Link**

**📊 Your Status:**
• **Referrals:** {user_ref_count}/39
• **Remaining:** {39 - user_ref_count} to complete
• **Cumulative earnings:** {user_ref_count * 3.9:.2f}₪
• **Accumulated SLH:** {user_ref_count * 0.1:.1f}

**🔗 Your Personal Link:**
`https://t.me/Buy_My_Shop_bot?start={user_id}`

**💡 Sharing Tips:**
• Share on Facebook, Instagram, TikTok
• Explain the economic opportunity
• Share in Telegram and WhatsApp groups

**🎁 After 39 referrals you'll get:**
• Full access for free!
• VIP status in community
• Additional benefits
                """
            }
            safe_edit_message(query, personal_link_texts.get(lang, personal_link_texts['he']), get_network_marketing_keyboard(user_id))

        elif query.data == 'back_to_main':
            welcome_back_text = get_translation(lang, 'welcome_back')
            safe_edit_message(query, welcome_back_text, get_main_keyboard(user_id))

        elif query.data in ['investment', 'bot_development', 'our_projects', 'contact', 'help']:
            # הודעות ברירת מחדל לפיצ'רים שעדיין בפיתוח
            default_messages = {
                'he': {
                    'investment': "**🚀 השקעה בפרויקט SLH**\n\nפרטים נוספים על אפשרויות השקעה יישלחו אליך בהמשך.",
                    'bot_development': "**🤖 פיתוח בוטים לעסקים**\n\nשירותי פיתוח בוטים מותאמים אישית. נא צור קשר לפרטים.",
                    'our_projects': "**🌐 הפרויקטים שלנו**\n\nכל הפרויקטים שלנו זמינים באתר הראשי.",
                    'contact': "**📞 צור קשר**\n\nנא שלח לנו הודעה ישירה לפרטים נוספים.",
                    'help': "**🆘 עזרה ראשונה**\n\nכיצד נוכל לעזור? צור איתנו קשר לפתרון מהיר."
                },
                'en': {
                    'investment': "**🚀 Invest in SLH Project**\n\nMore details about investment opportunities will be sent to you later.",
                    'bot_development': "**🤖 Bot Development for Businesses**\n\nCustom bot development services. Please contact us for details.",
                    'our_projects': "**🌐 Our Projects**\n\nAll our projects are available on the main website.",
                    'contact': "**📞 Contact**\n\nPlease send us a direct message for more details.",
                    'help': "**🆘 Quick Help**\n\nHow can we help? Contact us for a quick solution."
                }
            }
            message_dict = default_messages.get(lang, default_messages['he'])
            message = message_dict.get(query.data, "Feature coming soon...")
            safe_edit_message(query, message, get_back_keyboard(user_id))

    except Exception as e:
        logger.error(f"Error in button handler: {e}")
        try:
            lang = get_user_language(query.from_user.id)
            error_messages = {
                'he': "❌ אירעה שגיאה. אנא נסה שוב מהתפריט הראשי.",
                'en': "❌ An error occurred. Please try again from the main menu.",
                'ru': "❌ Произошла ошибка. Пожалуйста, попробуйте снова из главного меню.",
                'ar': "❌ حدث خطأ. يرجى المحاولة مرة أخرى من القائمة الرئيسية."
            }
            query.message.reply_text(
                error_messages.get(lang, "❌ An error occurred."),
                reply_markup=get_main_keyboard(query.from_user.id)
            )
        except:
            pass

def handle_payment_proof(update: Update, context: CallbackContext) -> None:
    """מטפל בשליחת אישור תשלום מהמשתמש"""
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id
        lang = get_user_language(user.id)

        # רישום פעילות מפורט
        log_user_activity(
            user.id, 
            user.username, 
            user.first_name, 
            user.last_name or "",
            "payment_proof_sent", 
            f"שלח אישור תשלום - שפה: {lang}"
        )

        # הודעות אישור רב-לשוניות
        success_messages = {
            'he': """
✅ **תודה רבה! אישור התשלום התקבל ונשלח לאימות.**

🚀 **נחזור אליך עם קישור ההצטרפות תוך 24 שעות!**

💎 **בונוס SLH:** קיבלת **SLH 1** בשווי 444₪!

📧 **מה תקבל:**
• קישור להצטרפות לקהילת VIP
• הלינק האישי שלך לשיתוף והכנסות  
• 39₪ ב-SLH (מתוך ה-444₪)
• שיחת ייעוץ אישית
• כל הבונוסים

💎 **בינתיים, מוזמן לבדוק את שאר האפשרויות!**
            """,
            'en': """
✅ **Thank you! Payment confirmation received and sent for verification.**

🚀 **We'll get back to you with the joining link within 24 hours!**

💎 **SLH Bonus:** You received **SLH 1** worth 444₪!

📧 **What you'll receive:**
• Link to join VIP community
• Your personal sharing link for earnings
• 39₪ in SLH (out of 444₪)
• Personal consultation call
• All bonuses

💎 **Meanwhile, feel free to check out other options!**
            """,
            'ru': """
✅ **Спасибо! Подтверждение платежа получено и отправлено на проверку.**

🚀 **Мы вернемся к вам со ссылкой для вступления в течение 24 часов!**

💎 **Бонус SLH:** Вы получили **SLH 1** стоимостью 444₪!

📧 **Что вы получите:**
• Ссылку для вступления в VIP сообщество
• Вашу персональную ссылку для приглашений и заработка
• 39₪ в SLH (из 444₪)
• Персональную консультацию
• Все бонусы

💎 **Тем временем, ознакомьтесь с другими возможностями!**
            """,
            'ar': """
✅ **شكرًا لك! تم استلام تأكيد الدفع وإرساله للتحقق.**

🚀 **سنتواصل معك برابط الانضمام خلال 24 ساعة!**

💎 **مكافأة SLH:** لقد حصلت على **SLH 1** بقيمة 444₪!

📧 **ما الذي ستحصل عليه:**
• رابط للانضمام لمجتمع VIP
• رابط المشاركة الشخصي للأرباح
• 39₪ في SLH (من أصل 444₪)
• مكالمة استشارية شخصية
• جميع المكافآت

💎 **في هذه الأثناء، لا تتردد في الاطلاع على الخيارات الأخرى!**
            """
        }

        # בדיקה אם המשתמש שלח תמונה (צילום מסך)
        if update.message.photo:
            photo_file = update.message.photo[-1].get_file()
            
            # שליחת אישור תשלום עם תמונה לקבוצת הניהול
            success = send_payment_confirmation(
                user_id=chat_id,
                user_name=f"{user.first_name} {user.last_name or ''}",
                payment_type="העברה בנקאית",
                amount=39,
                proof_text="אישור תמונה",
                image_file_id=photo_file.file_id
            )
            
            update.message.reply_text(
                success_messages.get(lang, success_messages['he']),
                reply_markup=get_main_keyboard(user.id),
                parse_mode='Markdown'
            )

        # בדיקה אם המשתמש שלח טקסט (תמלול ההעברה)
        elif update.message.text and not update.message.text.startswith('/'):
            proof_text = update.message.text
            
            # שליחת אישור תשלום לקבוצת הניהול
            success = send_payment_confirmation(
                user_id=chat_id,
                user_name=f"{user.first_name} {user.last_name or ''}",
                payment_type="העברה בנקאית",
                amount=39,
                proof_text=proof_text
            )
            
            update.message.reply_text(
                success_messages.get(lang, success_messages['he']),
                reply_markup=get_main_keyboard(user.id),
                parse_mode='Markdown'
            )

        else:
            # אם זו פקודה או סוג תוכן אחר
            instruction_messages = {
                'he': "📸 **נא שלח צילום מסך של ההעברה או פרטי התשלום בטקסט.**",
                'en': "📸 **Please send a screenshot of the transfer or payment details in text.**",
                'ru': "📸 **Пожалуйста, отправьте скриншот перевода или детали платежа текстом.**",
                'ar': "📸 **يرجى إرسال لقطة شاشة للتحويل أو تفاصيل الدفع نصًا.**"
            }
            update.message.reply_text(
                instruction_messages.get(lang, instruction_messages['he']),
                reply_markup=get_payment_keyboard(user.id),
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error in handle_payment_proof: {e}")
        lang = get_user_language(update.effective_user.id)
        error_messages = {
            'he': "❌ אירעה שגיאה בעיבוד האישור. אנא נסה שוב או צור קשר.",
            'en': "❌ An error occurred processing the confirmation. Please try again or contact us.",
            'ru': "❌ Произошла ошибка при обработке подтверждения. Пожалуйста, попробуйте снова или свяжитесь с нами.",
            'ar': "❌ حدث خطأ في معالجة التأكيد. يرجى المحاولة مرة أخرى أو الاتصال بنا."
        }
        update.message.reply_text(
            error_messages.get(lang, error_messages['he']),
            reply_markup=get_main_keyboard(update.effective_user.id),
            parse_mode='Markdown'
        )

# --- הגדרת handlers ---
def setup_handlers():
    """מגדיר את ה-handlers עבור הפקודות"""
    # handler לפקודת start - עובד בכל סוגי הצ'אטים
    dispatcher.add_handler(CommandHandler("start", start))
    
    # handlers לפקודות אדמין - עובדים בכל סוגי הצ'אטים
    dispatcher.add_handler(CommandHandler("chatid", chatid))
    dispatcher.add_handler(CommandHandler("admin", admin))
    dispatcher.add_handler(CommandHandler("broadcast", broadcast))
    dispatcher.add_handler(CommandHandler("group_broadcast", group_broadcast))
    
    # handlers לאינטראקציות משתמש - רק בצ'אטים פרטיים
    dispatcher.add_handler(CallbackQueryHandler(button_handler))
    dispatcher.add_handler(MessageHandler(Filters.photo & Filters.chat_type.private, handle_payment_proof))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command & Filters.chat_type.private, handle_payment_proof))
    
    # handler להוספת הבוט לקבוצות
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, handle_group_add))
    
    # handler למעקב אחר כל ההודעות בקבוצות - כדי לרשום אותן
    dispatcher.add_handler(MessageHandler(
        Filters.chat_type.groups & Filters.all, 
        handle_group_activity
    ))
    
    logger.info("Handlers setup completed")

# --- פאנל ניהול מתקדם ---
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'slh2025')

@app.route('/admin')
def admin_panel():
    """פאנל ניהול מתקדם"""
    password = request.args.get('password', '')
    if password != ADMIN_PASSWORD:
        return "❌ גישה נדחתה - סיסמה לא תקינה", 401
    
    stats = get_user_stats()
    recent_activity = get_recent_activity(20)
    pending_payments = get_pending_payments()
    groups = get_all_groups()
    
    admin_html = """
<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SLH - פאנל ניהול מתקדם</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body { 
            font-family: 'Arial', sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container { 
            max-width: 1400px; 
            margin: 0 auto; 
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header { 
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white; 
            padding: 30px; 
            text-align: center;
        }
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 20px; 
            padding: 20px;
        }
        .stat-card { 
            background: white; 
            padding: 25px; 
            border-radius: 12px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.1); 
            text-align: center;
            border-left: 5px solid #3498db;
            transition: transform 0.3s ease;
        }
        .stat-card:hover {
            transform: translateY(-5px);
        }
        .stat-number { 
            font-size: 2.5em; 
            font-weight: bold; 
            color: #2c3e50; 
            margin: 10px 0;
        }
        .stat-label {
            color: #7f8c8d;
            font-size: 1.1em;
        }
        .section {
            padding: 20px;
            margin: 20px;
            background: #f8f9fa;
            border-radius: 12px;
        }
        .section-title {
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        }
        .activity-item, .payment-item, .group-item {
            padding: 15px;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .activity-item:last-child, .payment-item:last-child, .group-item:last-child {
            border-bottom: none;
        }
        .user-info {
            font-weight: bold;
            color: #2c3e50;
        }
        .action-info {
            color: #7f8c8d;
        }
        .time-info {
            color: #95a5a6;
            font-size: 0.9em;
        }
        .payment-actions {
            display: flex;
            gap: 10px;
        }
        .btn {
            padding: 8px 15px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9em;
        }
        .btn-approve {
            background: #27ae60;
            color: white;
        }
        .btn-reject {
            background: #e74c3c;
            color: white;
        }
        .btn-refresh {
            background: #3498db;
            color: white;
        }
        .btn-export {
            background: #9b59b6;
            color: white;
        }
        .controls {
            text-align: center;
            padding: 20px;
        }
        .pending-badge {
            background: #e74c3c;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            margin-left: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 SLH - פאנל ניהול מתקדם</h1>
            <p>ניטור וניהול מלא של פעילות הבוט - נתונים בזמן אמת</p>
        </div>
        
        <div class="controls">
            <button class="btn btn-refresh" onclick="location.reload()">🔄 רענן נתונים</button>
            <button class="btn btn-export" onclick="exportData()">📊 יצא דוח</button>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">משתמשים רשומים</div>
                <div class="stat-number" id="totalUsers">{{ stats.total_users }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">משתמשים פעילים היום</div>
                <div class="stat-number" id="activeToday">{{ stats.active_today }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">תשלומים מאומתים</div>
                <div class="stat-number" id="verifiedPayments">{{ stats.verified_payments }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">תשלומים ממתינים</div>
                <div class="stat-number" id="pendingPayments">{{ stats.pending_payments }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">פעולות היום</div>
                <div class="stat-number" id="actionsToday">{{ stats.actions_today }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">קבוצות רשומות</div>
                <div class="stat-number" id="totalGroups">{{ groups|length }}</div>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">
                💰 תשלומים ממתינים לאישור
                {% if pending_payments %}<span class="pending-badge">{{ pending_payments|length }}</span>{% endif %}
            </h2>
            <div id="paymentList">
                {% if pending_payments %}
                    {% for payment in pending_payments %}
                    <div class="payment-item">
                        <div>
                            <div class="user-info">{{ payment[2] }} (@{{ payment[3] or 'ללא' }})</div>
                            <div class="action-info">סוג: {{ payment[4] }} | סכום: {{ payment[5] }}₪</div>
                            {% if payment[6] %}
                            <div class="action-info">פרטים: {{ payment[6] }}</div>
                            {% endif %}
                        </div>
                        <div>
                            <div class="time-info">{{ payment[7] }}</div>
                            <div class="payment-actions">
                                <button class="btn btn-approve" onclick="approvePayment({{ payment[0] }}, {{ payment[1] }})">✅ אישור</button>
                                <button class="btn btn-reject" onclick="rejectPayment({{ payment[0] }})">❌ דחייה</button>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <p style="text-align: center; color: #7f8c8d; padding: 20px;">אין תשלומים ממתינים לאישור</p>
                {% endif %}
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">
                📁 קבוצות רשומות ({{ groups|length }})
            </h2>
            <div id="groupsList">
                {% if groups %}
                    {% for group in groups %}
                    <div class="group-item">
                        <div>
                            <div class="user-info">{{ group[1] }}</div>
                            <div class="action-info">ID: {{ group[0] }} | Type: {{ group[2] }}</div>
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <p style="text-align: center; color: #7f8c8d; padding: 20px;">אין קבוצות רשומות במערכת</p>
                {% endif %}
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">📈 פעילות אחרונה</h2>
            <div id="activityList">
                {% for activity in recent_activity %}
                <div class="activity-item">
                    <div>
                        <span class="user-info">{{ activity[0] }} ({{ activity[1] or 'ללא' }})</span>
                        <span class="action-info"> - {{ activity[2] }}</span>
                        {% if activity[3] %}
                        <div class="action-info" style="color: #95a5a6; font-size: 0.9em;">{{ activity[3] }}</div>
                        {% endif %}
                    </div>
                    <div class="time-info">{{ activity[4] }}</div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <script>
        function approvePayment(paymentId, userId) {
            if (confirm('האם לאשר תשלום זה?')) {
                fetch('/admin/approve_payment', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        payment_id: paymentId,
                        user_id: userId,
                        password: '{{ request.args.get("password") }}'
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('✅ התשלום אושר! המשתמש קיבל הודעה ו-SLH 1.');
                        location.reload();
                    } else {
                        alert('❌ שגיאה באישור התשלום: ' + data.error);
                    }
                })
                .catch(error => {
                    alert('❌ שגיאה: ' + error);
                });
            }
        }
        
        function rejectPayment(paymentId) {
            if (confirm('האם לדחות תשלום זה?')) {
                // כאן ניתן להוסיף לוגיקת דחייה
                alert('פיצ'ר דחייה בתהליך פיתוח');
            }
        }
        
        function exportData() {
            alert('📊 דוח נתונים יוצא... בפועל כאן תתווסף פונקציית ייצוא');
        }
        
        // עדכון אוטומטי כל 30 שניות
        setInterval(() => {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
    """
    
    return render_template_string(admin_html, stats=stats, recent_activity=recent_activity, pending_payments=pending_payments, groups=groups)

@app.route('/admin/approve_payment', methods=['POST'])
def approve_payment():
    """מאשר תשלום ומשלח הודעה למשתמש"""
    try:
        data = request.get_json()
        password = data.get('password')
        payment_id = data.get('payment_id')
        user_id = data.get('user_id')
        
        if password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'סיסמה לא תקינה'})
        
        # אישור התשלום במסד הנתונים והוספת SLH
        success, slh_reward = approve_user_payment(user_id, 'admin')
        
        if success:
            # שליחת הודעה למשתמש
            try:
                user_info = f"🎉 **מזל טוב! התשלום שלך אושר!**\n\n"
                user_info += f"**💎 בונוס SLH:** קיבלת **{slh_reward} SLH** בשווי {slh_reward * 444}₪!\n\n"
                user_info += f"**🚀 קישור ההצטרפות לקהילה:**\n{MAIN_GROUP_LINK}\n\n"
                user_info += f"**🔗 הלינק האישי שלך לשיתוף:**\n`https://t.me/Buy_My_Shop_bot?start={user_id}`\n\n"
                user_info += f"**📊 מה תקבל:**\n"
                user_info += f"• גישה מלאה לקהילת VIP\n"
                user_info += f"• {slh_reward} SLH בשווי {slh_reward * 444}₪\n"
                user_info += f"• מערכת הכנסות פסיביות\n"
                user_info += f"• תמיכה טכנית 24/7\n\n"
                user_info += f"**💫 ברוך הבא למהפכה!**"
                
                bot.send_message(
                    chat_id=user_id,
                    text=user_info,
                    parse_mode='Markdown'
                )
                
                logger.info(f"Payment approved for user {user_id}, SLH rewarded: {slh_reward}")
                
            except Exception as e:
                logger.error(f"Error sending approval message to user {user_id}: {e}")
            
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'שגיאה באישור התשלום'})
            
    except Exception as e:
        logger.error(f"Error in approve_payment: {e}")
        return jsonify({'success': False, 'error': str(e)})

# --- הגדרת Flask routes ---
@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "service": "SLH Community Gateway Bot - Premium Edition",
        "version": "5.5",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "SLH Coin cryptocurrency ecosystem",
            "Advanced community gateway with smart payments", 
            "Elite bot development services",
            "5-generation network marketing",
            "NFT marketplace integration",
            "Multi-language support (HE/EN/RU/AR)",
            "Real-time analytics dashboard",
            "Advanced admin panel",
            "Payment tracking system",
            "User activity monitoring",
            "Referral tracking system",
            "Free access after 39 referrals",
            "Group management system",
            "Admin chatid command",
            "Payment confirmation to groups",
            "SLH Token rewards system"
        ],
        "monitoring": {
            "admin_panel": "/admin?password=slh2025",
            "real_time_alerts": "Active",
            "payment_tracking": "Active",
            "user_analytics": "Active",
            "referral_tracking": "Active",
            "group_tracking": "Active",
            "slh_rewards": "Active"
        },
        "ecosystem": {
            "slh_coin_value": "444 ILS",
            "membership_cost": "39 ILS", 
            "network_levels": 5,
            "active_users": "500+",
            "monthly_growth": "20%",
            "free_access_after": "39 referrals",
            "slh_reward_per_payment": "1 SLH"
        }
    }), 200

@app.route('/dashboard')
def dashboard():
    """ממשק ניהול בעברית"""
    return """
<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SLH - ממשק ניהול</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #667eea; }
        .projects { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .project-item { padding: 10px; border-bottom: 1px solid #eee; }
        .project-item:last-child { border-bottom: none; }
        .status-active { color: green; font-weight: bold; }
        .status-inactive { color: red; }
        .ecosystem { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-top: 20px; }
        .admin-link { background: #ff6b6b; color: white; padding: 10px 15px; border-radius: 5px; text-decoration: none; display: inline-block; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 SLH - ממשק ניהול מערכת</h1>
            <p>ניהול וניטור כל הפרויקטים במערכת אחת</p>
            <a href="/admin?password=slh2025" class="admin-link">🔐 פאנל ניהול מתקדם</a>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number" id="userCount">0</div>
                <div>משתמשים רשומים</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="projectCount">4</div>
                <div>פרויקטים פעילים</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="slhValue">444₪</div>
                <div>ערך SLH Coin</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="responseTime">2.3s</div>
                <div>זמן תגובה ממוצע</div>
            </div>
        </div>

        <div class="ecosystem">
            <h2>💎 אקוסיסטם סלה ללא גבולות - גרסה 5.5</h2>
            <p><strong>מערכת ניטור מתקדמת:</strong> ✅ פעיל</p>
            <p><strong>התראות בזמן אמת:</strong> ✅ פעיל</p>
            <p><strong>מעקב תשלומים:</strong> ✅ פעיל</p>
            <p><strong>פאנל ניהול:</strong> ✅ פעיל</p>
            <p><strong>טיפול בשגיאות:</strong> ✅ משופר</p>
            <p><strong>מערכת רפראלים:</strong> ✅ פעיל</p>
            <p><strong>גישה חינם אחרי 39:</strong> ✅ פעיל</p>
            <p><strong>תמיכה רב-לשונית:</strong> ✅ פעיל</p>
            <p><strong>מטבע SLH:</strong> 444₪ ליחידה</p>
            <p><strong>עלות הצטרפות:</strong> 39₪</p>
            <p><strong>רמות שיווק:</strong> 5 דורות</p>
            <p><strong>צמיחה חודשית:</strong> 20%</p>
            <p><strong>ניהול קבוצות:</strong> ✅ פעיל</p>
            <p><strong>פקודת /chatid:</strong> ✅ פעיל</p>
            <p><strong>פקודת /admin:</strong> ✅ פעיל</p>
            <p><strong>אישורי תשלום לקבוצה:</strong> ✅ פעיל</p>
            <p><strong>תגמולי SLH:</strong> ✅ פעיל (1 SLH לכל תשלום)</p>
            <p><strong>שידור לקבוצות:</strong> ✅ פעיל</p>
        </div>

        <div class="projects">
            <h2>🌐 הפרויקטים שלנו</h2>
            <div class="project-item">
                <strong>🤖 Bot Development Platform</strong>
                <span class="status-active">פעיל</span>
                <br><small>https://web-production-b425.up.railway.app</small>
            </div>
            <div class="project-item">
                <strong>🎨 SLH NFT Marketplace</strong>
                <span class="status-active">פעיל</span>
                <br><small>https://slh-nft.com/</small>
            </div>
            <div class="project-item">
                <strong>💼 Facebook Business Page</strong>
                <span class="status-active">פעיל</span>
                <br><small>https://www.facebook.com/OMG.adv/</small>
            </div>
            <div class="project-item">
                <strong>📚 Landing Page</strong>
                <span class="status-active">בפיתוח</span>
                <br><small>https://osifeu-prog.github.io/GATE_BOTSHOP/</small>
            </div>
        </div>
    </div>

    <script>
        // הדמיית נתונים דינמיים
        setInterval(() => {
            document.getElementById('userCount').textContent = 
                Math.floor(500 + Math.random() * 100);
            document.getElementById('responseTime').textContent = 
                (1.5 + Math.random() * 1).toFixed(1) + 's';
        }, 3000);
    </script>
</body>
</html>
"""

@app.route('/webhook', methods=['POST'])
def webhook():
    """נקודת הכניסה עבור עדכונים מטלגרם"""
    if request.method == 'POST':
        try:
            update = Update.de_json(request.get_json(force=True), bot)
            dispatcher.process_update(update)
            return 'ok', 200
        except Exception as e:
            logger.error(f"Error processing webhook update: {e}")
            return 'error', 500

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """קובע את ה-Webhook עבור הבוט"""
    try:
        success = bot.set_webhook(WEBHOOK_URL)
        if success:
            logger.info(f"Webhook set successfully to: {WEBHOOK_URL}")
            return jsonify({
                "status": "Webhook set successfully", 
                "url": WEBHOOK_URL,
                "timestamp": datetime.now().isoformat(),
                "bot_info": {
                    "service": "SLH Community & Ecosystem Gateway",
                    "version": "5.5",
                    "ecosystem": {
                        "slh_coin": "444 ILS per coin",
                        "network_marketing": "5 generations", 
                        "membership": "39 ILS",
                        "free_access_after": "39 referrals",
                        "slh_rewards": "1 SLH per payment",
                        "features": ["Bot development", "NFT marketplace", "Crypto ecosystem", "Advanced monitoring", "Referral system", "Multi-language support", "Group management", "Admin commands", "Payment confirmations", "SLH token rewards"]
                    }
                }
            }), 200
        else:
            logger.error("Failed to set webhook")
            return jsonify({"status": "Failed to set webhook"}), 500
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return jsonify({"status": f"Error: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """בדיקת בריאות של האפליקציה"""
    return jsonify({
        "status": "healthy", 
        "service": "SLH Community Gateway & Ecosystem",
        "version": "5.5",
        "timestamp": datetime.now().isoformat(),
        "projects_active": 4,
        "system_uptime": "99.9%",
        "slh_coin_value": "444 ILS",
        "monitoring": {
            "database": "active",
            "alerts": "active",
            "admin_panel": "active",
            "referral_system": "active",
            "multi_language": "active",
            "group_management": "active",
            "payment_confirmation": "active",
            "slh_rewards": "active"
        }
    }), 200

# --- אתחול ---
def initialize_bot():
    """אתחול הבוט והגדרות"""
    try:
        # הגדרת handlers
        setup_handlers()
        
        # קביעת webhook
        webhook_result = bot.set_webhook(WEBHOOK_URL)
        if webhook_result:
            logger.info(f"✅ Webhook set successfully: {WEBHOOK_URL}")
        else:
            logger.error("❌ Failed to set webhook")
            
        # בדיקת פרטי הבוט
        bot_info = bot.get_me()
        logger.info(f"✅ Bot initialized: @{bot_info.username}")
        
        # שליחת הודעת אתחול לקבוצת הניהול (אם היא קיימת)
        try:
            send_admin_alert("🚀 **בוט SLH הותחל בהצלחה!**\n\nגרסה: 5.5 - עם מערכת ניטור מתקדמת\nפאנל ניהול: /admin\nמערכת רפראלים: ✅ פעיל\nתמיכה רב-לשונית: ✅ פעיל\nנתונים בזמן אמת: ✅ פעיל\nניהול קבוצות: ✅ פעיל\nפקודת /chatid: ✅ פעיל\nאישורי תשלום לקבוצה: ✅ פעיל\nתגמולי SLH: ✅ פעיל (1 SLH לכל תשלום)\nשידור לקבוצות: ✅ פעיל")
        except Exception as e:
            logger.warning(f"Could not send startup message to admin group: {e}")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize bot: {e}")

# אתחול הבוט כאשר המודול נטען
initialize_bot()

# הפעלת שרת Flask
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
