import os
import logging
import json
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import threading
import time

# הגדרת משתני הסביבה
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', 'https://web-production-b425.up.railway.app') + '/webhook'
MAIN_GROUP_LINK = os.environ.get('MAIN_GROUP_LINK') 
ADMIN_GROUP_ID = os.environ.get('ADMIN_GROUP_ID', '-1002147033592')
ADMIN_USER_ID = os.environ.get('ADMIN_USER_ID', '6996423991')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'slh2025')

# הגדרת הלוגים
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- פונקציות מסד נתונים בסיסיות ---
def init_db():
    """אתחול מסד הנתונים"""
    try:
        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (user_id INTEGER PRIMARY KEY,
                      username TEXT,
                      first_name TEXT,
                      last_name TEXT,
                      language TEXT DEFAULT 'he',
                      join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS groups
                     (group_id INTEGER PRIMARY KEY,
                      title TEXT,
                      type TEXT,
                      added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

def log_user_activity(user_id, username, first_name, last_name, action_type):
    """רישום פעילות משתמש"""
    try:
        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO users 
                     (user_id, username, first_name, last_name, last_activity) 
                     VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)''', 
                     (user_id, username, first_name, last_name))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error logging user activity: {e}")

def save_group(group_id, title, group_type):
    """שמירת קבוצה במסד נתונים"""
    try:
        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO groups 
                     (group_id, title, type, last_activity) 
                     VALUES (?, ?, ?, CURRENT_TIMESTAMP)''', 
                     (group_id, title, group_type))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error saving group: {e}")
        return False

def get_all_groups():
    """קבלת כל הקבוצות"""
    try:
        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT group_id, title, type FROM groups ORDER BY last_activity DESC")
        groups = c.fetchall()
        conn.close()
        return groups
    except Exception as e:
        logger.error(f"Error getting groups: {e}")
        return []

# --- אתחול הבוט ---
try:
    bot = Bot(token=BOT_TOKEN)
    dispatcher = Dispatcher(bot, None, workers=4)
    logger.info("Bot and dispatcher initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize bot: {e}")
    raise

# --- פונקציות עזר ---
def safe_send_message(chat_id, text, reply_markup=None, parse_mode='Markdown'):
    """שליחת הודעה בטוחה עם טיפול בשגיאות"""
    try:
        return bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except Exception as e:
        logger.error(f"Error sending message to {chat_id}: {e}")
        return None

def safe_edit_message(query, text, reply_markup=None, parse_mode='Markdown'):
    """עריכת הודעה בטוחה"""
    try:
        query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        return True
    except Exception as e:
        logger.warning(f"Error editing message: {e}")
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

def send_admin_alert(message):
    """שליחת התראה לאדמין"""
    try:
        safe_send_message(ADMIN_USER_ID, message)
        logger.info(f"Admin alert sent: {message[:100]}...")
    except Exception as e:
        logger.error(f"Failed to send admin alert: {e}")

# --- מקלדות ---
def get_main_keyboard():
    """מקלדת ראשית"""
    keyboard = [
        [InlineKeyboardButton("🌟 האקוסיסטם", callback_data='ecosystem')],
        [InlineKeyboardButton("💎 הצטרפות לקהילה - 39₪", callback_data='join')],
        [InlineKeyboardButton("🚀 השקעה בפרויקט", callback_data='investment')],
        [InlineKeyboardButton("🤖 פיתוח בוטים", callback_data='bots')],
        [InlineKeyboardButton("📊 שיווק רשתי", callback_data='marketing')],
        [InlineKeyboardButton("🌐 הפרויקטים שלנו", callback_data='projects')],
        [InlineKeyboardButton("📞 צור קשר", callback_data='contact')],
        [InlineKeyboardButton("🆘 עזרה", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard():
    """מקלדת אדמין"""
    keyboard = [
        [InlineKeyboardButton("📊 סטטיסטיקות", callback_data='admin_stats')],
        [InlineKeyboardButton("📦 ניהול קבוצות", callback_data='admin_groups')],
        [InlineKeyboardButton("💰 תשלומים ממתינים", callback_data='admin_payments')],
        [InlineKeyboardButton("🔄 רענן נתונים", callback_data='admin_refresh')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_groups_keyboard():
    """מקלדת ניהול קבוצות"""
    keyboard = [
        [InlineKeyboardButton("📋 הצג כל הקבוצות", callback_data='groups_list')],
        [InlineKeyboardButton("🔄 רענן קבוצות", callback_data='groups_refresh')],
        [InlineKeyboardButton("📤 שידור לקבוצות", callback_data='groups_broadcast')],
        [InlineKeyboardButton("↩️ חזרה לפאנל", callback_data='admin_back')]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- handlers למשתמשים ---
def start(update: Update, context: CallbackContext) -> None:
    """פקודת /start"""
    try:
        user = update.effective_user
        chat = update.effective_chat
        
        # רישום פעילות
        log_user_activity(
            user.id, 
            user.username, 
            user.first_name, 
            user.last_name or "",
            'start'
        )
        
        # אם זו קבוצה
        if chat.type in ['group', 'supergroup']:
            save_group(chat.id, chat.title, chat.type)
            safe_send_message(
                chat.id,
                f"🤖 הבוט פעיל! ID הקבוצה: `{chat.id}`\n\nלאדמין: השתמש ב-`/admin` לניהול.",
                parse_mode='Markdown'
            )
            return
        
        # אם זה משתמש פרטי
        welcome_text = f"🌅 **ברוך הבא {user.first_name}!**\n\nאני הבוט של סלה ללא גבולות - האקוסיסטם הטכנולוגי המתקדם ביותר!"
        
        safe_send_message(
            chat.id,
            welcome_text,
            reply_markup=get_main_keyboard(),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in start: {e}")

def handle_callback(update: Update, context: CallbackContext) -> None:
    """טיפול בלחיצות על כפתורים"""
    query = update.callback_query
    
    try:
        # מענה לבקשה - עם טיפול בשגיאות
        try:
            query.answer()
        except Exception as e:
            logger.warning(f"Could not answer callback: {e}")
        
        user = query.from_user
        data = query.data
        
        # רישום פעילות
        log_user_activity(user.id, user.username, user.first_name, user.last_name or "", f"button_{data}")
        
        if data == 'ecosystem':
            text = "🌟 **סלה ללא גבולות - האקוסיסטם**\n\nהמערכת הטכנולוגית המתקדמת שלנו כוללת..."
            safe_edit_message(query, text, get_main_keyboard())
            
        elif data == 'join':
            text = "💎 **הצטרפות לקהילה - 39₪**\n\nפרטי תשלום והצטרפות..."
            safe_edit_message(query, text, get_main_keyboard())
            
        elif data == 'admin_stats':
            if str(user.id) != ADMIN_USER_ID:
                safe_edit_message(query, "❌ אין הרשאות אדמין", get_main_keyboard())
                return
                
            groups = get_all_groups()
            text = f"📊 **סטטיסטיקות אדמין**\n\n📦 קבוצות: {len(groups)}\n👤 ID אדמין: {ADMIN_USER_ID}"
            safe_edit_message(query, text, get_admin_keyboard())
            
        elif data == 'admin_groups':
            if str(user.id) != ADMIN_USER_ID:
                safe_edit_message(query, "❌ אין הרשאות אדמין", get_main_keyboard())
                return
                
            show_groups_command(update, context)
            
        elif data == 'groups_list':
            if str(user.id) != ADMIN_USER_ID:
                safe_edit_message(query, "❌ אין הרשאות אדמין", get_main_keyboard())
                return
                
            groups = get_all_groups()
            if groups:
                text = f"📋 **כל הקבוצות ({len(groups)}):**\n\n"
                for i, group in enumerate(groups, 1):
                    text += f"{i}. {group[1]}\n   ID: `{group[0]}`\n\n"
            else:
                text = "❌ אין קבוצות רשומות במערכת"
                
            safe_edit_message(query, text, get_groups_keyboard())
            
        elif data == 'groups_refresh':
            if str(user.id) != ADMIN_USER_ID:
                safe_edit_message(query, "❌ אין הרשאות אדמין", get_main_keyboard())
                return
                
            # רענון קבוצות - במקרה הזה רק מעדכן מהמסד נתונים
            groups = get_all_groups()
            text = f"🔄 **רענון קבוצות בוצע!**\n\n📦 קבוצות: {len(groups)}"
            safe_edit_message(query, text, get_groups_keyboard())
            
        elif data in ['admin_back', 'back']:
            if str(user.id) == ADMIN_USER_ID:
                text = "👑 **פאנל ניהול**\n\nבחר פעולה:"
                safe_edit_message(query, text, get_admin_keyboard())
            else:
                text = "🌅 **תפריט ראשי**\n\nבחר אפשרות:"
                safe_edit_message(query, text, get_main_keyboard())
                
        else:
            # ברירת מחדל
            text = "🔄 **תפריט ראשי**\n\nבחר אפשרות:"
            safe_edit_message(query, text, get_main_keyboard())
            
    except Exception as e:
        logger.error(f"Error in callback handler: {e}")
        try:
            safe_send_message(user.id, "❌ אירעה שגיאה. נסה שוב.", get_main_keyboard())
        except:
            pass

# --- handlers לאדמין ---
def admin_command(update: Update, context: CallbackContext) -> None:
    """פקודת /admin"""
    try:
        user = update.effective_user
        
        if str(user.id) != ADMIN_USER_ID:
            safe_send_message(user.id, "❌ אין הרשאות אדמין")
            return
            
        text = "👑 **פאנל ניהול - SLH Bot**\n\nבחר פעולה:"
        
        safe_send_message(
            user.id,
            text,
            reply_markup=get_admin_keyboard(),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in admin command: {e}")

def groupid_command(update: Update, context: CallbackContext) -> None:
    """פקודת /groupid או /chatid"""
    try:
        user = update.effective_user
        chat = update.effective_chat
        
        if str(user.id) != ADMIN_USER_ID:
            safe_send_message(user.id, "❌ אין הרשאות אדמין")
            return
            
        if chat.type in ['group', 'supergroup']:
            # שמירת הקבוצה
            save_group(chat.id, chat.title, chat.type)
            
            text = f"📦 **קבוצה:** {chat.title}\n🆔 **ID:** `{chat.id}`\n✅ **נשמרה במערכת!**"
            safe_send_message(chat.id, text, parse_mode='Markdown')
        else:
            # אם נשלח בפרטי, הצג את כל הקבוצות
            show_groups_command(update, context)
            
    except Exception as e:
        logger.error(f"Error in groupid command: {e}")

def show_groups_command(update: Update, context: CallbackContext) -> None:
    """הצגת כל הקבוצות"""
    try:
        user = update.effective_user
        
        if str(user.id) != ADMIN_USER_ID:
            safe_send_message(user.id, "❌ אין הרשאות אדמין")
            return
            
        groups = get_all_groups()
        
        if groups:
            text = f"📋 **כל הקבוצות ({len(groups)}):**\n\n"
            for i, group in enumerate(groups, 1):
                text += f"{i}. **{group[1]}**\n   🆔 `{group[0]}` | 📝 {group[2]}\n\n"
        else:
            text = "❌ אין קבוצות רשומות במערכת\n\n💡 **טיפ:** הזמן את הבוט לקבוצה ושים `/groupid`"
        
        # שליחה עם מקלדת ניהול
        safe_send_message(
            user.id,
            text,
            reply_markup=get_groups_keyboard(),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in show_groups_command: {e}")

def handle_group_events(update: Update, context: CallbackContext) -> None:
    """טיפול באירועים בקבוצות"""
    try:
        if update.message and update.message.chat.type in ['group', 'supergroup']:
            chat = update.message.chat
            # רישום/עדכון הקבוצה
            save_group(chat.id, chat.title, chat.type)
            
    except Exception as e:
        logger.error(f"Error in handle_group_events: {e}")

# --- הגדרת handlers ---
def setup_handlers():
    """הגדרת כל ה-handlers"""
    # handlers בסיסיים
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("admin", admin_command))
    dispatcher.add_handler(CommandHandler("groupid", groupid_command))
    dispatcher.add_handler(CommandHandler("chatid", groupid_command))
    
    # handlers לכפתורים
    dispatcher.add_handler(CallbackQueryHandler(handle_callback))
    
    # handlers לקבוצות
    dispatcher.add_handler(MessageHandler(
        Filters.chat_type.groups & Filters.all, 
        handle_group_events
    ))
    
    logger.info("All handlers setup completed")

# --- Flask routes ---
@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "service": "SLH Community Bot",
        "version": "2.0",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """נקודת הכניסה לעדכונים מטלגרם"""
    if request.method == 'POST':
        try:
            update = Update.de_json(request.get_json(force=True), bot)
            dispatcher.process_update(update)
            return 'ok', 200
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return 'error', 500

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """קביעת webhook"""
    try:
        success = bot.set_webhook(WEBHOOK_URL)
        if success:
            logger.info(f"Webhook set: {WEBHOOK_URL}")
            return jsonify({"status": "success", "url": WEBHOOK_URL})
        else:
            return jsonify({"status": "failed"}), 500
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

# --- פאנל ניהול Flask ---
@app.route('/admin')
def admin_panel():
    """פאנל ניהול בדפדפן"""
    password = request.args.get('password', '')
    if password != ADMIN_PASSWORD:
        return "❌ גישה נדחתה", 401
    
    groups = get_all_groups()
    
    html = f"""
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>SLH Admin</title>
        <style>
            body {{ font-family: Arial; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }}
            .header {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; border-radius: 10px; }}
            .groups {{ margin: 20px 0; }}
            .group-item {{ padding: 10px; border-bottom: 1px solid #eee; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>👑 SLH - פאנל ניהול</h1>
                <p>קבוצות פעילות: {len(groups)}</p>
            </div>
            
            <div class="groups">
                <h3>📦 קבוצות רשומות:</h3>
                {"".join(f'<div class="group-item"><strong>{g[1]}</strong><br>ID: <code>{g[0]}</code> | Type: {g[2]}</div>' for g in groups) if groups else "<p>אין קבוצות</p>"}
            </div>
            
            <div>
                <h3>🔧 פעולות:</h3>
                <button onclick="location.reload()">🔄 רענן</button>
                <button onclick="window.open('https://t.me/Buy_My_Shop_bot?start=admin', '_blank')">👑 פתח בוט</button>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

# --- אתחול ---
def initialize():
    """אתחול המערכת"""
    try:
        # אתחול DB
        init_db()
        
        # הגדרת handlers
        setup_handlers()
        
        # קביעת webhook
        bot.set_webhook(WEBHOOK_URL)
        
        # הודעת אתחול
        send_admin_alert("🚀 **בוט SLH הותחל!**\nגרסה: 2.0 - עם ניהול קבוצות\nפקודות: /admin, /groupid")
        
        logger.info("System initialized successfully")
    except Exception as e:
        logger.error(f"Initialization failed: {e}")

# אתחול
initialize()

# הרצת שרת
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
