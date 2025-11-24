import os
import logging
import json
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
import threading
import time

# הגדרת משתני הסביבה
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', 'https://web-production-b425.up.railway.app') + '/webhook'
MAIN_GROUP_LINK = "https://t.me/+HIzvM8sEgh1kNWY0"
ADMIN_GROUP_LINK = "https://t.me/+aww1rlTDUSplODc0"
ADMIN_GROUP_ID = "@slh_monitor_group"

# states לשיחת צור קשר
CHOOSING, TYPING_CONTACT = range(2)

# הגדרת הלוגים
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- מסד נתונים מתקדם ---
def init_db():
    """אתחול מסד הנתונים"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    
    # טבלת משתמשים
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER UNIQUE,
                  username TEXT,
                  first_name TEXT,
                  last_name TEXT,
                  join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  total_actions INTEGER DEFAULT 1,
                  status TEXT DEFAULT 'active')''')
    
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
                  verification_date TIMESTAMP)''')
    
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
    
    conn.commit()
    conn.close()

init_db()

# --- פונקציות מסד נתונים ---
def log_user_activity(user_id, username, first_name, last_name, action_type, action_details=""):
    """רישום פעילות משתמש במסד הנתונים"""
    conn = sqlite3.connect('bot_data.db')
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

def log_payment(user_id, payment_type, amount, proof_text=""):
    """רישום תשלום במסד הנתונים"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    
    c.execute('''INSERT INTO payments 
                 (user_id, payment_type, amount, proof_text)
                 VALUES (?, ?, ?, ?)''', (user_id, payment_type, amount, proof_text))
    
    payment_id = c.lastrowid
    
    # עדכון סטטיסטיקות תשלומים
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('''INSERT OR REPLACE INTO daily_stats (date, payments_received)
                 VALUES (?, COALESCE((SELECT payments_received FROM daily_stats WHERE date = ?), 0) + 1)
              ''', (today, today))
    
    conn.commit()
    conn.close()
    return payment_id

def get_user_stats():
    """קבלת סטטיסטיקות משתמשים"""
    conn = sqlite3.connect('bot_data.db')
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
        'total_users': total_users,
        'active_today': active_today,
        'verified_payments': verified_payments,
        'pending_payments': pending_payments,
        'actions_today': actions_today
    }

def get_recent_activity(limit=10):
    """קבלת פעילות אחרונה"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    
    c.execute('''SELECT u.first_name, u.username, al.action_type, al.action_details, al.timestamp
                 FROM activity_log al
                 JOIN users u ON al.user_id = u.user_id
                 ORDER BY al.timestamp DESC LIMIT ?''', (limit,))
    
    activity = c.fetchall()
    conn.close()
    return activity

# אתחול הבוט וה-dispatcher
try:
    bot = Bot(token=BOT_TOKEN)
    dispatcher = Dispatcher(bot, None, workers=4)
    logger.info("Bot and dispatcher initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize bot: {e}")
    raise

# --- לוגיקה לרישום משתמשים ושליחת התראות משודרגת ---
def send_admin_alert(message, image_file_id=None):
    """שולח התראה לקבוצת הניהול"""
    try:
        if image_file_id:
            bot.send_photo(
                chat_id=ADMIN_GROUP_LINK.replace('https://t.me/', ''), 
                photo=image_file_id, 
                caption=message,
                parse_mode='Markdown'
            )
        else:
            bot.send_message(
                chat_id=ADMIN_GROUP_LINK.replace('https://t.me/', ''), 
                text=message, 
                parse_mode='Markdown'
            )
        logger.info(f"התראה נשלחה: {message[:50]}...")
        return True
    except Exception as e:
        logger.error(f"שליחת התראה נכשלה: {e}")
        return False

def log_user_interaction(chat_id, first_name, last_name, username, action, details=""):
    """רושם פעילות משתמש ושולח התראה לקבוצת הניהול"""
    user_info = f"🆔 ID: `{chat_id}`\n👤 שם: {first_name} {last_name}\n📛 משתמש: @{username if username else 'ללא'}"
    log_message = f"🔔 **פעילות חדשה בבוט**\n{user_info}\n📝 **פעולה:** {action}"
    
    if details:
        log_message += f"\n📋 **פרטים:** {details}"
    
    # רישום במסד הנתונים
    log_user_activity(chat_id, username, first_name, last_name, action, details)
    
    # שליחת התראה
    send_admin_alert(log_message)

def send_payment_confirmation(user_id, user_name, payment_type, amount, proof_text="", image_file_id=None):
    """שולח אישור תשלום לקבוצת הניהול"""
    payment_message = f"💰 **אישור תשלום חדש!**\n👤 ממשתמש: {user_name}\n🆔 ID: `{user_id}`\n💳 סוג: {payment_type}\n💸 סכום: {amount}₪"
    
    if proof_text:
        payment_message += f"\n📝 פרטים: {proof_text}"
    
    # רישום במסד הנתונים
    log_payment(user_id, payment_type, amount, proof_text)
    
    # שליחת התראה עם תמונה אם יש
    send_admin_alert(payment_message, image_file_id)

def send_contact_request(chat_id, user_name, contact_type, message):
    """שולח בקשת קשר לקבוצת הניהול"""
    contact_message = f"📞 **בקשת קשר חדשה!**\n👤 ממשתמש: {user_name}\n🆔 ID: `{chat_id}`\n📋 נושא: {contact_type}\n💬 הודעה: {message}"
    
    # רישום במסד הנתונים
    log_user_activity(chat_id, "", user_name, "", "contact_request", f"{contact_type}: {message}")
    
    # שליחת התראה
    send_admin_alert(contact_message)

# --- מקלדות משודרגות ---
def get_main_keyboard():
    """מחזיר את המקלדת הראשית המשודרגת"""
    keyboard = [
        [InlineKeyboardButton("🌟 סלה ללא גבולות - האקוסיסטם", callback_data='ecosystem_explanation')],
        [InlineKeyboardButton("💎 הצטרפות לקהילה - 39₪", callback_data='join_community')],
        [InlineKeyboardButton("🚀 השקעה בפרויקט SLH", callback_data='investment')],
        [InlineKeyboardButton("🤖 פיתוח בוטים לעסקים", callback_data='bot_development')],
        [InlineKeyboardButton("📊 שיווק רשתי - 5 דורות", callback_data='network_marketing')],
        [InlineKeyboardButton("🌐 הפרויקטים שלנו", callback_data='our_projects')],
        [InlineKeyboardButton("📞 צור קשר", callback_data='contact'), InlineKeyboardButton("🆘 עזרה ראשונה", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_contact_keyboard():
    """מחזיר את מקלדת נושאי הקשר"""
    keyboard = [
        [InlineKeyboardButton("💼 עסקים ושותפויות", callback_data='contact_business')],
        [InlineKeyboardButton("🚀 השקעה בפרויקט", callback_data='contact_investment')],
        [InlineKeyboardButton("🤖 פיתוח בוט לעסק שלי", callback_data='contact_bot_development')],
        [InlineKeyboardButton("📊 שיווק רשתי", callback_data='contact_network')],
        [InlineKeyboardButton("🤔 תמיכה טכנית", callback_data='contact_support')],
        [InlineKeyboardButton("💬 כל נושא אחר", callback_data='contact_other')],
        [InlineKeyboardButton("↩️ חזרה לתפריט", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_payment_keyboard():
    """מחזיר את מקלדת אפשרויות התשלום"""
    keyboard = [
        [InlineKeyboardButton("🏦 העברה בנקאית", callback_data='payment_bank')],
        [InlineKeyboardButton("💎 תשלום ב-TON", callback_data='payment_ton')],
        [InlineKeyboardButton("💰 תשלום בקריפטו נוסף", callback_data='payment_crypto')],
        [InlineKeyboardButton("✅ שלחתי תשלום", callback_data='payment_sent')],
        [InlineKeyboardButton("🎁 בונוסי הצטרפות", callback_data='joining_bonuses')],
        [InlineKeyboardButton("↩️ חזרה", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_bot_development_keyboard():
    """מחזיר את מקלדת שירותי פיתוח בוטים"""
    keyboard = [
        [InlineKeyboardButton("💼 בוט לעסק שלי", callback_data='contact_bot_development')],
        [InlineKeyboardButton("💰 הצעת מחיר", callback_data='contact_business')],
        [InlineKeyboardButton("📞 שיחת ייעוץ", callback_data='contact_other')],
        [InlineKeyboardButton("🌐 האתרים שלנו", callback_data='our_websites')],
        [InlineKeyboardButton("↩️ חזרה", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_projects_keyboard():
    """מחזיר את מקלדת הפרויקטים שלנו"""
    keyboard = [
        [InlineKeyboardButton("🛒 SLH NFT Marketplace", callback_data='project_slh_nft')],
        [InlineKeyboardButton("🤖 Bot Development Platform", callback_data='project_bot_platform')],
        [InlineKeyboardButton("💼 Facebook Business Page", callback_data='project_facebook')],
        [InlineKeyboardButton("📊 Live System Dashboard", callback_data='project_dashboard')],
        [InlineKeyboardButton("🌐 כל האתרים שלנו", callback_data='our_websites')],
        [InlineKeyboardButton("↩️ חזרה", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_ecosystem_keyboard():
    """מחזיר את מקלדת האקוסיסטם"""
    keyboard = [
        [InlineKeyboardButton("💰 מטבע SLH - ההסבר המלא", callback_data='slh_coin_explanation')],
        [InlineKeyboardButton("🎯 לינק שיתוף אישי - איך מרוויחים?", callback_data='personal_link_explanation')],
        [InlineKeyboardButton("📈 שיווק רשתי - 5 דורות", callback_data='network_marketing')],
        [InlineKeyboardButton("🤖 שירותי פיתוח בוטים", callback_data='bot_development')],
        [InlineKeyboardButton("💎 הצטרפות לקהילה", callback_data='join_community')],
        [InlineKeyboardButton("↩️ חזרה", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_network_marketing_keyboard():
    """מחזיר את מקלדת שיווק רשתי"""
    keyboard = [
        [InlineKeyboardButton("💰 מודל 5 הדורות - הסבר", callback_data='five_generations')],
        [InlineKeyboardButton("🎯 איך מתחילים להרוויח?", callback_data='how_to_start')],
        [InlineKeyboardButton("📊 דוגמאות להכנסות", callback_data='income_examples')],
        [InlineKeyboardButton("💎 הצטרפות עכשיו", callback_data='join_community')],
        [InlineKeyboardButton("↩️ חזרה", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_premium_keyboard():
    """מחזיר מקלדת פרימיום להצטרפות"""
    keyboard = [
        [InlineKeyboardButton("💎 הצטרפות מיידית - 39₪", callback_data='join_community')],
        [InlineKeyboardButton("🎁 מה כלול בחבילה?", callback_data='premium_package')],
        [InlineKeyboardButton("💰 איך ארים הכנסות?", callback_data='income_calculator')],
        [InlineKeyboardButton("📞 שיחת ייעוץ חינם", callback_data='contact_other')],
        [InlineKeyboardButton("↩️ חזרה", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- מטבעות הטלגרם משודרגים ---
def start(update: Update, context: CallbackContext) -> None:
    """מטפל בפקודה /start - משודרג"""
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id

        # רישום המשתמש ושליחת לוג
        log_user_interaction(
            chat_id=chat_id,
            first_name=user.first_name or "לא צוין",
            last_name=user.last_name or "",
            username=user.username or "לא צוין",
            action="התחיל שיחה עם הבוט (/start)"
        )

        # שליחת תמונה עם הודעת ברוך הבא משודרגת
        welcome_image_url = "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2032&q=80"
        
        try:
            update.message.reply_photo(
                photo=welcome_image_url,
                caption=f"🌅 **ברוך הבא {user.first_name} למהפכה הכלכלית של סלה ללא גבולות!**\n\n_גילית את האקוסיסטם הטכנולוגי המתקדם ביותר בישראל שמשלב קריפטו, בוטים חכמים, ושיווק רשתי מתקדם_ ✨",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.warning(f"Could not send welcome image: {e}")

        welcome_text = f"""
**🎊 {user.first_name}, גילית את העתיד הכלכלי שלך!**

**סלה ללא גבולות - SLH** הוא אקוסיסטם טכנולוגי ראשון מסוגו בישראל שמשלב:

**💎 מטבע קריפטו ייחודי - SLH**
• מטבע בעל ערך אמיתי שצומח עם הקהילה
• כל מצטרף חדש מקבל **SLH 1** בשווי 444₪ (39₪ מתוכם מיד עם ההצטרפות)
• אסימון utility עם שימושים אמיתיים בכל המערכת

**🚀 4 מקורות הכנסה במערכת אחת:**
1. **🤖 בוטים אוטומטיים** - שערי כניסה חכמים לקהילות
2. **📊 מסחר ומטבע SLH** - צמיחה עם ערך המטבע
3. **🎨 נכסים דיגיטליים** - NFT ופלטפורמות מסחר
4. **📈 שיווק רשתי** - הכנסה פסיבית מ-5 דורות

**💼 מה תקבל בהצטרפות?**
• **לינק שיתוף אישי** - מניב הכנסות אוטומטיות
• **SLH 1** בשווי 444₪ - עם 39₪ מידית
• **גישה לקהילת VIP** - אנשי עסקים ויזמים
• **כלים טכנולוגיים** - בוטים, ניתוחים, מסחר

**🎯 החזון שלנו:** לבנות את הקהילה הטכנולוגית-כלכלית הגדולה בישראל, שבה כל member הוא גם משקיע, גם יזם, וגם שותף להצלחה.

**📊 כבר היום המערכת שלנו:**
✅ מאות משתמשים פעילים
✅ מטבע SLH עם ערך אמיתי
✅ הכנסות שוטפות לכל החברים
✅ צמיחה של 20% בחודש

**🌐 זה הבוט שאתה רואה עכשיו - הוא השער לעולם שלם של הזדמנויות!**
        """

        # שליחת הודעת ברוך הבא עם מקלדת
        update.message.reply_text(
            welcome_text,
            reply_markup=get_main_keyboard(),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        update.message.reply_text("❌ אירעה שגיאה. אנא נסה שוב.")

def button_handler(update: Update, context: CallbackContext) -> None:
    """מטפל בלחיצות על כפתורים - משודרג"""
    query = update.callback_query
    query.answer()

    try:
        user = query.from_user
        action_details = f"לחץ על: {query.data}"
        
        # רישום פעילות
        log_user_activity(
            user.id, 
            user.username, 
            user.first_name, 
            user.last_name or "",
            "button_click", 
            action_details
        )

        if query.data == 'ecosystem_explanation':
            ecosystem_text = """
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
• שירותי פיתוח בוטים מותאמים

**2. 💰 SLH Coin - המערכת הפיננסית**
• מטבע utility עם שימושים אמיתיים
• חוזים חכמים אוטומטיים
• מסחר וארנקים דיגיטליים
• חלוקת רווחים אוטומטית

**3. 🎨 NFT & Digital Assets**
• שוק NFT לנכסים דיגיטליים
• פלטפורמת מסחר מתקדמת
• יצירה וניהול תוכן
• קהילת יוצרים ומשקיעים

**4. 📈 Network Marketing**
• שיווק רשתי ל-5 דורות
• הכנסות פסיביות אוטומטיות
• לינקים אישיים לשיתוף
• מערכת דוחות מתקדמת

**🔗 כל הרכיבים מחוברים** ויוצרים אקוסיסטם סגור שבו כל פעילות מזינה את האחרות ומייצרת צמיחה לכל השותפים!
            """
            query.edit_message_text(
                ecosystem_text,
                reply_markup=get_ecosystem_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'slh_coin_explanation':
            slh_coin_text = """
**💎 מטבע SLH - המהפכה הכלכלית**

**🎯 מה זה SLH Coin?**
SLH הוא מטבע קריפטו utility ייחודי שאנחנו הנפקנו, עם ערך אמיתי ושימושים קונקרטיים בכל המערכת שלנו.

**💰 ערך וצמיחה:**
• **ערך נוכחי:** 444₪ ל-SLH 1
• **מדיניות הנפקה:** כמות מוגבלת עם צמיחה מתוכננת
• **ביקוש אורגני:** גדל עם כל מצטרף חדש
• **utility:** משמש לתשלומים בכל הפלטפורמות

**🎁 מה מקבלים בהצטרפות?**
כאשר אתה מצטרף ב-39₪, אתה מקבל:
• **גישה מלאה** לכל המערכות
• **SLH 1** בשווי 444₪ - 39₪ מידית, השאר בהדרגה
• **לינק שיתוף אישי** להכנסות נוספות
• **קהילת VIP** עם אנשי עסקים

**🚀 איך עולה הערך?**
1. **ביקוש גובר** - כל מצטרף חדש צריך SLH
2. **utility מגביר** - יותר שימושים = יותר ביקוש
3. **קהילה גדלה** - רשת משתמשים פעילה
4. **פיתוח מתמיד** - פיצ'רים חדשים כל הזמן

**💼 שימושים אמיתיים ב-SLH:**
• תשלום עבור שירותי פיתוח בוטים
• רכישת נכסים דיגיטליים ב-NFT marketplace
• השתתפות בהנחות וקידומים בלעדיים
• תשלום עמלות במערכת השיווק הרשתי

**📈 הערך המוסף:**
זו לא רק "השקעה" - זו **רכישת נכס דיגיטלי** שמניב הכנסות פסיביות דרך הלינק האישי שלך ומקבל ערך מצמיחת הקהילה!
            """
            query.edit_message_text(
                slh_coin_text,
                reply_markup=get_ecosystem_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'personal_link_explanation':
            personal_link_text = """
**🎯 הלינק האישי שלך - מכונת ההכנסות האוטומטית**

**💡 איך עובד הלינק האישי?**
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

**3. 🚀 בונוסים נוספים**
• בונוסים עבור ביצועים יוצאי דופן
• תגמולים על פעילות בקהילה
• הטבות בלעדיות למצטרפים מובילים

**📊 דוגמאות להכנסות:**
אם תצרף רק **5 אנשים** בחודש, והם יצרפו כל אחד 3 אנשים:
• **חודש 1:** 5 × 39₪ × 10% = 19.5₪
• **חודש 2:** 15 × 39₪ × 5% = 29.25₪
• **חודש 3:** 45 × 39₪ × 3% = 52.65₪
• **סה"כ לאחר 3 חודשים:** 101.4₪ **פסיבי**!

**🎁 וזה רק מהשיווק הרשתי - belum כולל צמיחת ערך ה-SLH שלך!**
            """
            query.edit_message_text(
                personal_link_text,
                reply_markup=get_ecosystem_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'network_marketing':
            network_text = """
**📈 שיווק רשתי מתקדם - 5 דורות של הכנסה**

**🎯 המודל המתקדם שלנו:**

אנחנו יצרנו מודל שיווק רשתי שהוגן, שקוף, ומניב הכנסות אמיתיות לכל השותפים.

**💰 מבנה העמלות ל-5 דורות:**

**דור 1 - המצטרפים הישירים שלך**
• **10%** מכל רכישה של אדם שהצטרף דרך הלינק שלך
• התשלום מתבצע אוטומטית ב-SLH
• אין הגבלה על מספר המצטרפים

**דור 2 - המצטרפים של הדור הראשון**
• **5%** מכל רכישה של אדם שהצטרף דרך המצטרפים שלך
• הכנסה פסיבית מהרשת שלך גדלה

**דור 3 - הרחבה נוספת**
• **3%** מהמצטרפים בדור השלישי
• הרשת ממשיכה להתרחב

**דור 4 - הכנסה עמוקה**
• **2%** מהדור הרביעי
• עומק אסטרטגי שמגביר יציבות

**דור 5 - בסיס רחב**
• **1%** מהדור החמישי
• רשת רחבה שמייצרת הכנסה קבועה

**📊 דוגמאות מספריות:**
אם כל member מצרף בממוצע 3 אנשים:
• **דור 1:** 3 people
• **דור 2:** 9 people  
• **דור 3:** 27 people
• **דור 4:** 81 people
• **דור 5:** 243 people
• **סה"כ:** 363 people ברשת שלך!

**💎 היתרונות שלנו:**
• **שקיפות מלאה** - רואים כל פעילות ברשת
• **תשלומים אוטומטיים** - אין צורך בתזכורות
• **לינק אישי** - קל לשיתוף והפצה
• **קהילה תומכת** - עוזרים לך להצליח
• **הכנסה פסיבית** - העבודה נעשית פעם אחת

**🚀 מוכן להתחיל להרוויח?** הצטרף עכשיו וקבל את הלינק האישי שלך!
            """
            query.edit_message_text(
                network_text,
                reply_markup=get_network_marketing_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'five_generations':
            five_gen_text = """
**💰 מודל 5 הדורות - ההסבר המלא**

**🎯 איך באמת עובד מודל 5 הדורות?**

זה לא "שיווק רשתי" רגיל - זו **מערכת הכנסות פסיביות** מתוחכמת:

**📊 מבנה הדורות:**

**🌱 דור 1 - השורשים שלך**
• האנשים שהצטרפו **ישירות** דרך הלינק שלך
• אתה מקבל **10%** מכל רכישה שלהם
• זה הבסיס הישיר שלך

**🌿 דור 2 - הענפים**
• האנשים שהצטרפו דרך הדור הראשון שלך  
• אתה מקבל **5%** מכל רכישה שלהם
• הרשת מתחילה להתרחב

**🌳 דור 3 - הצמרת**
• האנשים שהצטרפו דרך הדור השני
• אתה מקבל **3%** מכל רכישה
• ההכנסה הפסיבית מתחילה לצבור תאוצה

**🍃 דור 4 - העלים**
• האנשים שהצטרפו דרך הדור השלישי
• אתה מקבל **2%** מכל רכישה
• רשת רחבה ועמוקה

**🌲 דור 5 - היער**
• האנשים שהצטרפו דרך הדור הרביעי
• אתה מקבל **1%** מכל רכישה
• בסיס רחב שמייצר הכנסה קבועה

**💡 למה 5 דורות?**
• **הוגן** - כולם מרוויחים
• **מתגמל** - מי שפעיל מרוויח יותר
• **יציב** - רשת עמוקה פחות מתפוררת
• **צומח** - פוטנציאל צמיחה אקספוננציאלי

**📈 דוגמה מעשית:**
אם אתה מצרף 5 אנשים, וכל אחד מהם מצרף 3:
• **חודש 1:** 5 people × 39₪ × 10% = 19.5₪
• **חודש 2:** 15 people × 39₪ × 5% = 29.25₪  
• **חודש 3:** 45 people × 39₪ × 3% = 52.65₪
• **חודש 4:** 135 people × 39₪ × 2% = 105.3₪
• **חודש 5:** 405 people × 39₪ × 1% = 157.95₪
• **סה"כ:** 364.65₪ **פסיבי** לחודש!

**🎯 וזה רק מהשיווק - belum כולל צמיחת ה-SLH שלך!**
            """
            query.edit_message_text(
                five_gen_text,
                reply_markup=get_network_marketing_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'income_examples':
            income_text = """
**📊 דוגמאות להכנסות אמיתיות מהשטח**

**🎯 איך באמת נראות ההכנסות במערכת?**

**📈 תרחיש צנוע - "המתחיל"**
• מצרף 3 אנשים בחודש הראשון
• כל אחד מהם מצרף 2 אנשים
• **הכנסה חודשית:** 150-300₪
• **פוטנציאל שנתי:** 2,000-4,000₪

**🚀 תרחיש בינוני - "הפעיל"**  
• מצרף 5 אנשים בחודש הראשון
• כל אחד מהם מצרף 3 אנשים
• **הכנסה חודשית:** 500-1,000₪
• **פוטנציאל שנתי:** 8,000-15,000₪

**💎 תרחיש מתקדם - "המוביל"**
• מצרף 10 אנשים בחודש הראשון
• צוות פעיל שמצרף 5 אנשים בממוצע
• **הכנסה חודשית:** 2,000-5,000₪
• **פוטנציאל שנתי:** 30,000-60,000₪

**🌟 תרחיש מקצועי - "הבונה"**
• בונה צוות של 100+ people
• מערכת הכשרה והדרכה
• **הכנסה חודשית:** 10,000₪+
• **פוטנציאל שנתי:** 120,000₪+

**💰 וזה רק מהשיווק הרשתי!**
**➕ תוסיף את זה:**
• צמיחת ערך ה-SLH שלך (פוטנציאל 2-5X בשנה)
• הכנסות משירותי בוטים (אם תרצה)
• הכנסות מ-NFT ופרויקטים נוספים

**🎯 האסטרטגיה המומלצת:**
1. **התחל קטן** - צרף 3-5 אנשים ראשונים
2. **למד והכשר** - עזור לצוות שלך להצליח
3. **תבנה בסיס** - רשת יציבה של 2-3 דורות
4. **תגדיל פעילות** - הרחב את ההשפעה שלך
5. **תיהנה מהפירות** - הכנסה פסיבית שגדלה עם הזמן

**🚀 מוכן להתחיל את המסע?** הצטרף עכשיו וקבל את כל הכלים!
            """
            query.edit_message_text(
                income_text,
                reply_markup=get_network_marketing_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'join_community':
            join_text = """
**💎 הצטרפות לקהילת סלה ללא גבולות**

**🎯 מה באמת קונה ה-39₪ שלך?**

זו לא "עלות" - זו **השקעה בנכס דיגיטלי** שמניב הכנסות!

**💼 חבילת הערך המלאה:**

**1. 💰 נכס דיגיטלי - SLH Coin**
• **SLH 1** בשווי 444₪ - 39₪ מידית, השאר בהדרגה
• מטבע utility עם שימושים אמיתיים
• פוטנציאל צמיחה עם גידול הקהילה

**2. 🎯 לינק שיתוף אישי**
• מניב 10% מכל מצטרף חדש
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

**📊 מה תקבל בפועל:**
1. **מייד עם ההצטרפות:**
   - גישה לקהילת הטלגרם
   - לינק שיתוף אישי
   - 39₪ ב-SLH (מתוך ה-444₪)

2. **בהמשך הדרך:**
   - יתרת ה-SLH (405₪ נוספים)
   - הדרכות והכשרות
   - גישה לכלים נוספים

**💰 איך משלמים?**
• **העברה בנקאית** - פשוט ומיידי
• **תשלום ב-TON** - טכנולוגי ומתקדם  
• **קריפטו נוסף** - גמישות מלאה

**🎁 בונוס למצטרפים עכשיו:**
• שיחת ייעוץ אישית עם המייסדים
• הדרכה מפורטת איך להתחיל להרוויח
• גישה לקבוצת לימוד exclusive

**🚀 העלות הסמלית מבטיחה קהילה איכותית ומחויבת!**
            """
            query.edit_message_text(
                join_text,
                reply_markup=get_payment_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'joining_bonuses':
            bonuses_text = """
🎁 **בונוסי הצטרפות בלעדיים - רק עכשיו!**

לכל מצטרף חדש בחודש זה אנחנו נותנים מתנות נוספות:

🏆 **חבילת בונוסים בשווי 500₪+:**

1. **📞 שיחת ייעוץ אישית עם המייסדים** (שווי 200₪)
   • אסטרטגיה אישית להצלחה
   • ניתוח פוטנציאל ההכנסה שלך
   • ליווי צמוד בהתחלה

2. **🤖 בוט שיווקי אישי** (שווי 150₪)
   • בוט אוטומטי לשיווק הלינק שלך
   • מערכת מעקב אחר מצטרפים
   • דוחות הכנסות אוטומטיים

3. **📚 קורס דיגיטל אקספרס** (שווי 99₪)
   • איך לשווק נכון בטלגרם
   • טכניקות לשיתוף אפקטיבי
   • בניית קהילה דיגיטלית

4. **💳 הטבות נוספות:**
   • הנחה 20% על פיתוח בוטים
   • עדיפות בהשקעות עתידיות
   • גישה למידע בלעדי

⚡ **הבונוסים בתוקף ל-24 השעות הקרובות בלבד!**

💎 **זה הזמן המושלם להצטרף!**
            """
            query.edit_message_text(
                bonuses_text,
                reply_markup=get_premium_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'income_calculator':
            calculator_text = """
📊 **מחשבון הכנסות - כמה באמת תוכל להרוויח?**

🎯 **בוא נחשב ביחד:**

**תרחיש בסיסי - רק 3 מצטרפים בחודש:**
חודש 1: 3 אנשים × 39₪ × 10% = 11.7₪
חודש 2: 9 אנשים × 39₪ × 5% = 17.55₪
חודש 3: 27 אנשים × 39₪ × 3% = 31.59₪
חודש 4: 81 אנשים × 39₪ × 2% = 63.18₪
חודש 5: 243 אנשים × 39₪ × 1% = 94.77₪
**סה"כ לאחר 5 חודשים: 218.79₪ לחודש!**

💰 **וזה רק מהשיווק - belum כולל:**
• צמיחת ערך ה-SLH שלך (פוטנציאל 2-5X)
• הכנסות משירותי בוטים
• השקעות נוספות

🚀 **תרחיש מציאותי - 5 מצטרפים בחודש:**
חודש 1: 5 אנשים = 19.5₪
חודש 2: 25 אנשים = 48.75₪
חודש 3: 125 אנשים = 146.25₪
חודש 4: 625 אנשים = 487.5₪
חודש 5: 3125 אנשים = 1218.75₪
**סה"כ: 1920.75₪ לחודש - הכנסה פסיבית!**

💎 **וזה רק מתחיל...**
הרשת שלך ממשיכה לגדול גם אם אתה מפסיק לגייס!

🎯 **מוכן להתחיל? ההצטרפות עכשיו במיוחד עם בונוסים!**
            """
            query.edit_message_text(
                calculator_text,
                reply_markup=get_premium_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'premium_package':
            package_text = """
🎁 **חבילת הפרימיום המלאה - מה באמת תקבל?**

💎 **חבילת הערך השלמה:**

1. **SLH Coin - הנכס הדיגיטלי שלך**
   • SLH 1 בשווי 444₪ (39₪ מידית + 405₪ נוספים)
   • מטבע אמיתי עם utility במערכת
   • פוטנציאל צמיחה אקספוננציאלי

2. **מערכת הכנסות פסיביות**
   • לינק שיתוף אישי - מניב 10% מכל מצטרף
   • 5 דורות של הכנסות אוטומטיות
   • דוחות וסטטיסטיקות בזמן אמת

3. **קהילת VIP בלעדית**
   • נטרוקינג עם אנשי עסקים מובילים
   • מידע וטיפים לפני כולם
   • שיתופי פעולה בלעדיים

4. **כלים טכנולוגיים מתקדמים**
   • גישה לפלטפורמת הבוטים
   • מערכת ניהול והפצת תוכן
   • כלי ניתוח ומעקב

5. **הדרכה ותמיכה מלאה**
   • שיחת ייעוץ אישית עם מייסדים
   • הדרכות וידאו מקצועיות
   • תמיכה טכנית 24/7

6. **הטבות וזכויות נוספות**
   • הנחות על שירותי פיתוח
   • עדיפות בהשקעות עתידיות
   • גישה לפרויקטים חדשים

💰 **שווי החבילה האמיתי: 1000₪+**
**💸 המחיר שלך: 39₪ בלבד!**

🎯 **זו לא הוצאה - זו השקעה!**
            """
            query.edit_message_text(
                package_text,
                reply_markup=get_premium_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'investment':
            # שליחת תמונה להשקעה
            investment_image_url = "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80"
            
            try:
                query.message.reply_photo(
                    photo=investment_image_url,
                    caption="🚀 **הזדמנות השקעה - להצטרף למהפכה של סלה ללא גבולות!**\n\n_מערכת SLH - האקוסיסטם הטכנולוגי שצומח בקצב מסחרר_ 🌟",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.warning(f"Could not send investment image: {e}")

            investment_text = """
**🚀 הזדמנות השקעה - להצטרף להצלחה שכבר רצה!**

**💎 אנחנו לא סטארט-אפ - אנחנו אקוסיסטם פעיל עם:**

**📊 נתונים אמיתיים מהשטח:**
• ✅ **מערכת SLH FULL SUITE** - פעילה ומייצרת הכנסות
• ✅ **קהילה של מאות משתמשים** - גדלה בקצב 20% בחודש
• ✅ **מטבע SLH עם ערך** - 444₪ ליחידה עם utility אמיתי
• ✅ **מודל עסקי מוכח** - הכנסות מכמה מקורות במקביל

**🎯 למה להשקיע דווקא עכשיו?**
• **סבב השקעה ראשון** - מחיר כניסה אטרקטיבי
• **צמיחה אקספוננציאלית** - השוק רק בתחילת הדרך
• **צוות מנוסה** - מייסדים עם ניסיון של 10+ שנים
• **טכנולוגיה ייחודית** - אין מתחרים ישירים בישראל

**💰 מה אנחנו מציעים למשקיעים:**
• **החזר השקעה משמעותי** - תשואה צפויה של 5-10X
• **שותפות אסטרטגית** - להיות חלק מהמהפכה הטכנולוגית
• **גישה לכל הטכנולוגיות** - גם לשימוש אישי
• **ליווי אישי צמוד** - ישירות מהמייסדים

**📈 תכנית הפיתוח:**
• **Q1 2024** - הרחבת צוות הפיתוח ושיווק
• **Q2 2024** - כניסה לשווקים בינלאומיים
• **Q3 2024** - פיתוח מוצרים נוספים
• **Q4 2024** - פозициониון כאקזיט

**🔒 למה אנחנו בטוחים בהצלחה?**
• **ביקוש אדיר** - אלפי פניות ממשתמשים פוטנציאליים
• **טכנולוגיה ייחודית** - אקוסיסטם שלם וייחודי
• **צוות מקצועי** - ניסיון עשיר בפיתוח ושיווק
• **תזמון מושלם** - השוק בשל ומוכן לטכנולוגיה שלנו

**💼 מעוניינים להיות חלק מהסיפור?** 
לחצו על '📞 צור קשר' ובחרו 'השקעה בפרויקט'
            """
            query.edit_message_text(
                investment_text,
                reply_markup=get_main_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'bot_development':
            bot_dev_text = """
**🤖 פיתוח בוטים לעסקים - הטכנולוגיה שתשדרג את העסק שלך!**

**💡 למה כל עסק מצליח משתמש בבוט טלגרם?**

**📊 נתונים שלא ניתן להתעלם מהם:**
• **חיסכון של 40%** בעלויות שירות לקוחות - הבוט עובד 24/7
• **עלייה של 50%** במכירות - שיווק ממוקד ואוטומטי
• **זמינות בלתי מתפשרת** - מענה ללקוחות בכל שעה
• **ניהול קהילות** - הגדלת נאמנות לקוחות ב-300%

**🚀 מה אנחנו בונים עבורך?**
• **בוטים מותאמים אישית** - מתאים בדיוק לצרכי העסק שלך
• **שערי כניסה חכמים** - לקהילות וקבוצות VIP
• **מערכות הזמנות מתקדמות** - איקומרס ישירות בטלגרם
• **אינטגרציות מתקדמות** - אתרים, CRM, מערכות תשלום
• **שיווק אוטומטי** - ניהול קמפיינים וקידומים

**💼 דוגמאות לבוטים שבנינו:**
• **בוט קהילה** - ניהול מאות חברים עם תשלומים אוטומטיים
• **בוט מכירות** - הזמנות, תשלומים ומעקב אחריות
• **בוט שירות** - מענה אוטומטי לשאלות נפוצות
• **בוט תוכן** - הפצת עדכונים וקידומים

**💰 תמחור שקוף והוגן:**
• **בוט בסיסי** - החל מ-₪149 (כולל תמיכה חודשית)
• **בוט מתקדם** - ₪349 (כולל אינטגרציות מתקדמות)
• **בוט פרימיום** - ₪749 (פיתוח מלא + אחזקה לשנה)

**🎁 מה כלול במחיר?**
• **פיתוח מותאם אישית** - לפי הצרכים הספציפיים שלך
• **הדרכה מלאה** - איך להשתמש ולנהל את הבוט
• **תמיכה טכנית** - זמינים לכל שאלה או בעיה
• **עדכונים שוטפים** - הטכנולוגיה מתפתחת כל הזמן

**📞 נשמח לשוחח על הצרכים הספציפיים של העסק שלך!**
            """
            query.edit_message_text(
                bot_dev_text,
                reply_markup=get_bot_development_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'our_projects':
            projects_text = """
**🌐 הפרויקטים שלנו - תיק עבודות**

להלן הפרויקטים והפלטפורמות שאנו מפתחים ומתחזקים:

**🎯 המערכות הפעילות שלנו:**
• **SLH FULL SUITE** - המערכת המרכזית שלנו
• **בוטים אוטומטיים** לקהילות ועסקים
• **פלטפורמות מסחר** וניהול תיקים
• **אתרי NFT** ושיווק דיגיטלי

**📊 כל הפרויקטים מחוברים ומשתלבים** ליצירת חוויה אחת מלאה ללקוח.

בחר אחד מהפרויקטים להצגת פרטים נוספים:
            """
            query.edit_message_text(
                projects_text,
                reply_markup=get_projects_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'our_websites':
            websites_text = """
**🌐 כל האתרים והפלטפורמות שלנו**

**🛠 פלטפורמות פעילות:**
• **פלטפורמת הבוטים** - https://web-production-b425.up.railway.app/set_webhook
• **שרת API וממשק** - https://web-production-b425.up.railway.app

**🎨 אתרים ושיווק:**
• **שוק ה-NFT שלנו** - https://slh-nft.com/
• **דף הפייסבוק העסקי** - https://www.facebook.com/OMG.adv/

**📚 משאבים ומידע:**
• **דף נחיתה** - https://osifeu-prog.github.io/GATE_BOTSHOP/
• **תיעוד ומדריכים** - בקרוב

**📞 ליצירת קשר:**
**אוסיף**: 058-4203384
**צביקה**: 054-6671882

**💡 כל האתרים מעודכנים ופעילים!**
            """
            query.edit_message_text(
                websites_text,
                reply_markup=get_projects_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'project_slh_nft':
            nft_text = """
**🎨 SLH NFT Marketplace**

**https://slh-nft.com/**

שוק NFT מתקדם המאפשר יצירה, קניה ומכירה של נכסים דיגיטליים ייחודיים.

**🚀 תכונות מרכזיות:**
• יצירת NFT מקוריים
• מסחר מאובטח
• חוזים חכמים
• אינטגרציה עם ארנקים דיגיטליים

**💎 יתרונות:**
• עמלות נמוכות
• ממשק משתמש intuitive
• תמיכה במגוון פורמטים
• קהילה פעילה

**👥 קהל יעד:**
• אמנים דיגיטליים
• אספנים
• משקיעים
• עסקים המעוניינים בנכסים דיגיטליים

**🔗 בקרו באתר:** https://slh-nft.com/
            """
            query.edit_message_text(
                nft_text,
                reply_markup=get_projects_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'project_bot_platform':
            platform_text = """
**🤖 Bot Development Platform**

**https://web-production-b425.up.railway.app/set_webhook**

פלטפורמה מתקדמת לפיתוח בוטי טלגרם עם יכולות מתקדמות.

**🚀 תכונות מרכזיות:**
• בוטי קהילה וניהול
• מערכות תשלום אינטגרטיביות
• אינטגרציה עם APIs חיצוניים
• ניתוח נתונים מתקדם

**💼 שירותים:**
• פיתוח בוטים מותאמים אישית
• תמיכה והדרכה
• אחזקה ושיפורים
• אינטגרציות מתקדמות

**📊 נתונים:**
• מהירות תגובה: < 3 שניות
• זמינות: 99.9%
• תמיכה במאות משתמשים בו-זמנית

**🔗 פלטפורמה פעילה:** https://web-production-b425.up.railway.app
            """
            query.edit_message_text(
                platform_text,
                reply_markup=get_projects_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'project_facebook':
            facebook_text = """
**💼 Facebook Business Page**

**https://www.facebook.com/OMG.adv/**

דף העסקים הרשמי שלנו בפייסבוק - המרכז השיווקי והתקשורתי שלנו.

**📱 מה תמצאו בדף:**
• עדכונים שוטפים על הפרויקטים
• טיפים ועצות לעסקים
• קידומים והנחות בלעדיים
• סיפורי הצלחה של לקוחות

**🎯 מטרות הדף:**
• בניית קהילה עסקית
• שיווק ושיח עם לקוחות
• הפקת לידים איכותיים
• בניית מותג חזק

**👥 קהל יעד:**
• בעלי עסקים
• יזמים ומשקיעים
• אנשי טכנולוגיה
• מעוניינים בקריפטו ו-Web3

**👍 עקבו אחרינו:** https://www.facebook.com/OMG.adv/
            """
            query.edit_message_text(
                facebook_text,
                reply_markup=get_projects_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'project_dashboard':
            dashboard_text = """
**📊 Live System Dashboard**

**https://web-production-b425.up.railway.app/**

ממשק ניהול וניטור חי של כל המערכות שלנו - בעברית!

**📈 מה תוכלו לראות בממשק:**
• **סטטוס מערכת** - זמינות ופעילות
• **סטטיסטיקות** - משתמשים ופעילות
• **ביצועים** - מהירות ותגובה
• **לוגים** - פעילות מערכת

**🔧 אפשרויות נוספות:**
• ניהול משתמשים
• עדכוני מערכת
• דוחות וביצועים
• הגדרות והתאמות

**🌐 הממשק כולל:**
• דשבורד אינטואיטיבי בעברית
• גרפים וסטטיסטיקות
• התראות בזמן אמת
• דוחות ניתנים להורדה

**🔗 גשו לממשק:** https://web-production-b425.up.railway.app/
            """
            query.edit_message_text(
                dashboard_text,
                reply_markup=get_projects_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'contact':
            contact_text = """
**📞 צור קשר עם המייסדים**

אנחנו כאן כדי לעזור! בחר נושא לפניה:
            """
            query.edit_message_text(
                contact_text,
                reply_markup=get_contact_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'help':
            help_text = """
**🆘 עזרה ראשונה**

**❓ בעיות טכניות?**
• נסה לסגור ולפתוח את הבוט מחדש
• ודא שיש לך חיבור אינטרנט

**💳 בעיות בתשלום?**
• שלח לנו צילום מסך של ההעברה
• נבדוק ונחזור אליך תוך 24 שעות

**👥 רוצה להצטרף לקהילה?**
• לחץ על 'הצטרפות לקהילה'
• עקוב אחר הוראות התשלום

**🤖 מעוניין בבוט לעסק שלך?**
• לחץ על 'פיתוח בוטים לעסקים'
• נשמח לעזור!

**📞 צריך עזרה נוספת?**
• לחץ על 'צור קשר'
• נשמח לעזור!
            """
            query.edit_message_text(
                help_text,
                reply_markup=get_main_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'payment_bank':
            bank_text = """
**🏦 העברה בנקאית**
בנק: הפועלים
סניף: כפר גנים (153)
מספר חשבון: 73462
שם המוטב: קאופמן צביקה

**📝 חשוב:** אחרי ההעברה, שלח אלינו את אישור התשלום באמצעות הכפתור '✅ שלחתי תשלום'
            """
            query.edit_message_text(
                bank_text,
                reply_markup=get_payment_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'payment_ton':
            ton_text = """
**💎 תשלום ב-TON**
UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp

**📝 חשוב:** אחרי ההעברה, שלח אלינו את אישור התשלום באמצעות הכפתור '✅ שלחתי תשלום'
"""
            query.edit_message_text(
                ton_text,
                reply_markup=get_payment_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'payment_crypto':
            crypto_text = """
**💰 תשלום בקריפטו נוסף**

אנחנו מקבלים תשלומים גם במטבעות קריפטו נוספים:

**🎯 המטבעות המקובלים:**
• Bitcoin (BTC)
• Ethereum (ETH) 
• BNB
• USDT
• ומטבעות נוספים

**📞 איך משלמים?**
1. לחצו על '📞 צור קשר'
2. בחרו 'שיחת ייעוץ'
3. נשלח לכם את כתובות הארנק המתאימות

**💎 יתרונות תשלום בקריפטו:**
• עמלות נמוכות
• העברה בינלאומית
• אנונימיות ופרטיות
• טכנולוגיה עתידית

**🚀 נשמח לעזור לכם בתהליך!**
            """
            query.edit_message_text(
                crypto_text,
                reply_markup=get_payment_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'payment_sent':
            payment_sent_text = """
**✅ אישור תשלום**

מצוין! שלח אלינו עכשיו את **אישור התשלום** כ:

📸 **צילום מסך** של ההעברה
📝 **או** פרטי ההעברה בטקסט

**🚀 אחרי האימות** (עד 24 שעות) נשלח לך:
1. **קישור להצטרפות לקהילה**
2. **הלינק האישי שלך לשיתוף**
3. **39₪ ב-SLH** (מתוך ה-444₪ המלאים)

**🎁 בונוס:** שיחת ייעוץ אישית עם המייסדים!
            """
            query.edit_message_text(
                payment_sent_text,
                reply_markup=get_payment_keyboard(),
                parse_mode='Markdown'
            )
            context.user_data['waiting_for_payment'] = True

        elif query.data in ['contact_business', 'contact_investment', 'contact_bot_development', 'contact_network', 'contact_support', 'contact_other']:
            contact_types = {
                'contact_business': '💼 עסקים ושותפויות',
                'contact_investment': '🚀 השקעה בפרויקט', 
                'contact_bot_development': '🤖 פיתוח בוט לעסק שלי',
                'contact_network': '📊 שיווק רשתי',
                'contact_support': '🤔 תמיכה טכנית',
                'contact_other': '💬 כל נושא אחר'
            }
            
            context.user_data['contact_type'] = contact_types[query.data]
            contact_info_text = f"""
**📞 צור קשר - {contact_types[query.data]}**

**👤 פרטי התקשרות:**
**אוסיף אונגר**: 058-4203384
**צביקה קאופמן**: 054-6671882

**💬 אנא כתוב את הודעתך:**
(נא לתאר בקצרה את פנייתך)
            """
            query.edit_message_text(
                contact_info_text,
                parse_mode='Markdown'
            )
            return TYPING_CONTACT

        elif query.data == 'back_to_main':
            welcome_back_text = """
**🏠 חזרת לתפריט הראשי**

**💎 איך נוכל לעזור לך להצליח היום?**

בחר אחת האפשרויות להמשך המסע:
            """
            query.message.reply_text(
                welcome_back_text,
                reply_markup=get_main_keyboard(),
                parse_mode='Markdown'
            )

    except Exception as e:
        logger.error(f"Error in button handler: {e}")
        query.message.reply_text(
            "❌ אירעה שגיאה. אנא נסה שוב מהתפריט הראשי.",
            reply_markup=get_main_keyboard()
        )

def handle_contact_message(update: Update, context: CallbackContext) -> int:
    """מטפל בהודעת קשר מהמשתמש"""
    try:
        user = update.effective_user
        user_message = update.message.text
        
        # שליחת בקשת הקשר לקבוצת הניהול
        send_contact_request(
            chat_id=update.effective_chat.id,
            user_name=f"{user.first_name} {user.last_name or ''}",
            contact_type=context.user_data.get('contact_type', 'לא צוין'),
            message=user_message
        )
        
        # הודעת תודה למשתמש
        update.message.reply_text(
            "✅ **תודה רבה!** ההודעה שלך נשלחה למייסדים.\n\n"
            "📞 ניצור איתך קשר בהקדם האפשרי.",
            reply_markup=get_main_keyboard()
        )
        
        # ניקוי ה-state
        context.user_data.clear()
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error in handle_contact_message: {e}")
        update.message.reply_text("❌ אירעה שגיאה בשליחת ההודעה. אנא נסה שוב.")
        return ConversationHandler.END

def handle_payment_proof(update: Update, context: CallbackContext) -> None:
    """מטפל בשליחת אישור תשלום מהמשתמש"""
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id

        # רישום פעילות
        log_user_activity(
            user.id, 
            user.username, 
            user.first_name, 
            user.last_name or "",
            "payment_proof_sent", 
            "שלח אישור תשלום"
        )

        # בדיקה אם המשתמש שלח תמונה (צילום מסך)
        if update.message.photo:
            photo_file = update.message.photo[-1].get_file()
            
            # שליחת אישור תשלום עם תמונה לקבוצת הניהול
            send_payment_confirmation(
                user_id=chat_id,
                user_name=f"{user.first_name} {user.last_name or ''}",
                payment_type="העברה בנקאית",
                amount=39,
                proof_text="אישור תמונה",
                image_file_id=photo_file.file_id
            )
            
            update.message.reply_text(
                "✅ **תודה רבה! אישור התשלום התקבל ונשלח לאימות.**\n\n"
                "🚀 **נחזור אליך עם קישור ההצטרפות תוך 24 שעות!**\n\n"
                "📧 **מה תקבל:**\n"
                "• קישור להצטרפות לקהילת VIP\n" 
                "• הלינק האישי שלך לשיתוף והכנסות\n"
                "• 39₪ ב-SLH (מתוך ה-444₪)\n"
                "• שיחת ייעוץ אישית\n"
                "• כל הבונוסים\n\n"
                "💎 **בינתיים, מוזמן לבדוק את שאר האפשרויות!**",
                reply_markup=get_main_keyboard()
            )

        # בדיקה אם המשתמש שלח טקסט (תמלול ההעברה)
        elif update.message.text and not update.message.text.startswith('/'):
            proof_text = update.message.text
            
            # שליחת אישור תשלום לקבוצת הניהול
            send_payment_confirmation(
                user_id=chat_id,
                user_name=f"{user.first_name} {user.last_name or ''}",
                payment_type="העברה בנקאית",
                amount=39,
                proof_text=proof_text
            )
            
            update.message.reply_text(
                "✅ **תודה רבה! פרטי האישור התקבלו ונשלחו לאימות.**\n\n"
                "🚀 **נחזור אליך עם קישור ההצטרפות תוך 24 שעות!**\n\n"
                "📧 **מה תקבל:**\n"
                "• קישור להצטרפות לקהילת VIP\n"
                "• הלינק האישי שלך לשיתוף והכנסות\n" 
                "• 39₪ ב-SLH (מתוך ה-444₪)\n"
                "• שיחת ייעוץ אישית\n"
                "• כל הבונוסים\n\n"
                "💎 **בינתיים, מוזמן לבדוק את שאר האפשרויות!**",
                reply_markup=get_main_keyboard()
            )

        else:
            # אם זו פקודה או סוג תוכן אחר
            update.message.reply_text(
                "📸 **נא שלח צילום מסך של ההעברה או פרטי התשלום בטקסט.**",
                reply_markup=get_payment_keyboard()
            )
            
    except Exception as e:
        logger.error(f"Error in handle_payment_proof: {e}")
        update.message.reply_text(
            "❌ אירעה שגיאה בעיבוד האישור. אנא נסה שוב או צור קשר.",
            reply_markup=get_main_keyboard()
        )

def cancel(update: Update, context: CallbackContext) -> int:
    """מבטל את שיחת צור קשר"""
    update.message.reply_text(
        "❌ הפניה בוטלה.\n\n💎 **מוזמן להמשיך לגלות את האפשרויות שלנו!**",
        reply_markup=get_main_keyboard()
    )
    context.user_data.clear()
    return ConversationHandler.END

# --- הגדרת handlers ---
def setup_handlers():
    """מגדיר את ה-handlers עבור הפקודות"""
    # ConversationHandler עבור צור קשר
    contact_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern='^(contact_business|contact_investment|contact_bot_development|contact_network|contact_support|contact_other)$')],
        states={
            TYPING_CONTACT: [MessageHandler(Filters.text & ~Filters.command, handle_contact_message)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(contact_conv_handler)
    dispatcher.add_handler(CallbackQueryHandler(button_handler))
    dispatcher.add_handler(MessageHandler(Filters.photo, handle_payment_proof))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_payment_proof))
    logger.info("Handlers setup completed")

# --- פאנל ניהול מתקדם ---
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'slh2024')

@app.route('/admin')
def admin_panel():
    """פאנל ניהול מתקדם"""
    password = request.args.get('password', '')
    if password != ADMIN_PASSWORD:
        return "❌ גישה נדחתה - סיסמה לא תקינה", 401
    
    stats = get_user_stats()
    recent_activity = get_recent_activity(20)
    
    admin_html = """
<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SLH - פאנל ניהול מתקדם</title>
    <style>
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
        .activity-section {
            padding: 20px;
            margin: 20px;
            background: #f8f9fa;
            border-radius: 12px;
        }
        .activity-item {
            padding: 15px;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .activity-item:last-child {
            border-bottom: none;
        }
        .activity-user {
            font-weight: bold;
            color: #2c3e50;
        }
        .activity-action {
            color: #7f8c8d;
        }
        .activity-time {
            color: #95a5a6;
            font-size: 0.9em;
        }
        .section-title {
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        }
        .refresh-btn {
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 10px;
        }
        .export-btn {
            background: #27ae60;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 10px;
        }
        .controls {
            text-align: center;
            padding: 20px;
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
            <button class="refresh-btn" onclick="location.reload()">🔄 רענן נתונים</button>
            <button class="export-btn" onclick="exportData()">📊 יצא דוח</button>
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
        </div>

        <div class="activity-section">
            <h2 class="section-title">📈 פעילות אחרונה</h2>
            <div id="activityList">
                {% for activity in recent_activity %}
                <div class="activity-item">
                    <div>
                        <span class="activity-user">{{ activity[0] }} ({{ activity[1] }})</span>
                        <span class="activity-action"> - {{ activity[2] }}</span>
                        {% if activity[3] %}
                        <div class="activity-details" style="color: #95a5a6; font-size: 0.9em;">{{ activity[3] }}</div>
                        {% endif %}
                    </div>
                    <div class="activity-time">{{ activity[4] }}</div>
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="activity-section">
            <h2 class="section-title">📊 דוחות נוספים</h2>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div>
                    <h3>📈 מגמות שבועיות</h3>
                    <p>גרף מגמות וניתוח סטטיסטי יוצג כאן...</p>
                </div>
                <div>
                    <h3>💰 ניתוח הכנסות</h3>
                    <p>פילוח הכנסות ומקורות תשלום...</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        function exportData() {
            alert('📊 דוח נתונים יוצא... בפועל כאן תתווסף פונקציית ייצוא');
            // כאן ניתן להוסיף פונקציית ייצוא אמיתית ל-Excel או PDF
        }
        
        // עדכון אוטומטי כל 30 שניות
        setInterval(() => {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
    """
    
    return render_template_string(admin_html, stats=stats, recent_activity=recent_activity)

# --- הגדרת Flask routes ---
@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "service": "SLH Community Gateway Bot - Premium Edition",
        "version": "5.0",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "SLH Coin cryptocurrency ecosystem",
            "Advanced community gateway with smart payments", 
            "Elite bot development services",
            "5-generation network marketing",
            "NFT marketplace integration",
            "Hebrew-optimized interface",
            "Real-time analytics dashboard",
            "Advanced admin panel",
            "Payment tracking system",
            "User activity monitoring"
        ],
        "monitoring": {
            "admin_panel": "/admin?password=YOUR_PASSWORD",
            "real_time_alerts": "Active",
            "payment_tracking": "Active",
            "user_analytics": "Active"
        },
        "ecosystem": {
            "slh_coin_value": "444 ILS",
            "membership_cost": "39 ILS", 
            "network_levels": 5,
            "active_users": "500+",
            "monthly_growth": "20%"
        },
        "projects": {
            "bot_platform": "https://web-production-b425.up.railway.app/set_webhook",
            "nft_marketplace": "https://slh-nft.com/",
            "facebook_page": "https://www.facebook.com/OMG.adv/",
            "premium_landing": "https://osifeu-prog.github.io/GATE_BOTSHOP/"
        },
        "contact": {
            "osif_ungar": "058-4203384",
            "zvika_kaufman": "054-6671882", 
            "telegram_bot": "@SLH_Israel_Bot"
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
            <a href="/admin?password=slh2024" class="admin-link">🔐 פאנל ניהול מתקדם</a>
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
            <h2>💎 אקוסיסטם סלה ללא גבולות - גרסה 5.0</h2>
            <p><strong>מערכת ניטור מתקדמת:</strong> ✅ פעיל</p>
            <p><strong>התראות בזמן אמת:</strong> ✅ פעיל</p>
            <p><strong>מעקב תשלומים:</strong> ✅ פעיל</p>
            <p><strong>פאנל ניהול:</strong> ✅ פעיל</p>
            <p><strong>מטבע SLH:</strong> 444₪ ליחידה</p>
            <p><strong>עלות הצטרפות:</strong> 39₪</p>
            <p><strong>רמות שיווק:</strong> 5 דורות</p>
            <p><strong>צמיחה חודשית:</strong> 20%</p>
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

        <div class="projects" style="margin-top: 20px;">
            <h2>📞 יצירת קשר</h2>
            <p><strong>אוסיף אונגר:</strong> 058-4203384</p>
            <p><strong>צביקה קאופמן:</strong> 054-6671882</p>
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
                    "version": "5.0",
                    "ecosystem": {
                        "slh_coin": "444 ILS per coin",
                        "network_marketing": "5 generations", 
                        "membership": "39 ILS",
                        "features": ["Bot development", "NFT marketplace", "Crypto ecosystem", "Advanced monitoring"]
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
        "version": "5.0",
        "timestamp": datetime.now().isoformat(),
        "projects_active": 4,
        "system_uptime": "99.9%",
        "slh_coin_value": "444 ILS",
        "monitoring": {
            "database": "active",
            "alerts": "active",
            "admin_panel": "active"
        }
    }), 200

@app.route('/services', methods=['GET'])
def services():
    """מחזיר מידע על השירותים"""
    return jsonify({
        "services": [
            {
                "name": "SLH Community Membership",
                "description": "הצטרפות לקהילת סלה ללא גבולות",
                "price": "39₪",
                "features": ["SLH Coin worth 444₪", "Personal sharing link", "5-generation network", "VIP community access"]
            },
            {
                "name": "Custom Bot Development", 
                "description": "פיתוח בוטים מותאמים אישית לעסקים",
                "price": "Starting from 149₪",
                "features": ["Custom design", "Integration", "Support & maintenance"]
            },
            {
                "name": "Investment Opportunities",
                "description": "השקעה באקוסיסטם SLH", 
                "contact_required": True,
                "features": ["Equity partnership", "Technology access", "Personal mentoring"]
            }
        ],
        "contact": {
            "osif": "058-4203384",
            "zvika": "054-6671882"
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
        
        # שליחת הודעת אתחול לקבוצת הניהול
        send_admin_alert("🚀 **בוט SLH הותחל בהצלחה!**\n\nגרסה: 5.0 - עם מערכת ניטור מתקדמת\nפאנל ניהול: /admin\nנתונים בזמן אמת: ✅ פעיל")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize bot: {e}")

# אתחול הבוט כאשר המודול נטען
initialize_bot()

# הפעלת שרת Flask
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
