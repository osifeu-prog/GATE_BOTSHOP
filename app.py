import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string

from config import BOT_TOKEN, WEBHOOK_URL, ADMIN_PASSWORD, ADMIN_USER_ID
from database.models import init_db
from database.operations import get_user_stats, get_recent_activity, get_pending_payments, get_all_groups, approve_user_payment
from utils.helpers import bot, send_admin_alert

# הגדרת הלוגים
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# אתחול מסד נתונים
init_db()

# אתחול dispatcher
try:
    from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
    dispatcher = Dispatcher(bot, None, workers=4)
    logger.info("✅ Dispatcher initialized")
except Exception as e:
    logger.error(f"❌ Error initializing dispatcher: {e}")
    dispatcher = None

# יבוא handlers ישירות
try:
    from handlers.user_handlers import start, button_handler, handle_payment_proof
    from handlers.admin_handlers import admin, chatid, groupid, chaid, broadcast, group_broadcast, refresh_all_groups
    from handlers.group_handlers import handle_group_add, handle_group_activity
    
    if dispatcher:
        # handlers בסיסיים
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("admin", admin))
        dispatcher.add_handler(CommandHandler("chatid", chatid))
        dispatcher.add_handler(CommandHandler("groupid", groupid))
        dispatcher.add_handler(CommandHandler("chaid", chaid))
        dispatcher.add_handler(CommandHandler("broadcast", broadcast))
        dispatcher.add_handler(CommandHandler("group_broadcast", group_broadcast))
        dispatcher.add_handler(CommandHandler("refresh_groups", refresh_all_groups))
        
        # handlers לכפתורים
        dispatcher.add_handler(CallbackQueryHandler(button_handler))
        
        # handlers להודעות
        dispatcher.add_handler(MessageHandler(Filters.photo & Filters.chat_type.private, handle_payment_proof))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command & Filters.chat_type.private, handle_payment_proof))
        
        # handlers לקבוצות
        dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, handle_group_add))
        dispatcher.add_handler(MessageHandler(Filters.chat_type.groups & Filters.all, handle_group_activity))
        
        logger.info("✅ All handlers registered successfully")
        
except Exception as e:
    logger.error(f"❌ Error setting up handlers: {e}")

# --- Flask routes ---
@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "service": "SLH Community Gateway Bot", 
        "version": "1.0",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """נקודת הכניסה עבור עדכונים מטלגרם"""
    if request.method == 'POST' and dispatcher:
        try:
            from telegram import Update
            update = Update.de_json(request.get_json(force=True), bot)
            dispatcher.process_update(update)
            return 'ok', 200
        except Exception as e:
            logger.error(f"Error processing webhook update: {e}")
            return 'error', 500
    return 'dispatcher not available', 500

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """קובע את ה-Webhook עבור הבוט"""
    try:
        success = bot.set_webhook(WEBHOOK_URL)
        if success:
            logger.info(f"Webhook set successfully to: {WEBHOOK_URL}")
            return jsonify({"status": "Webhook set successfully", "url": WEBHOOK_URL})
        else:
            return jsonify({"status": "Failed to set webhook"}), 500
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return jsonify({"status": f"Error: {str(e)}"}), 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

# --- פאנל ניהול Flask ---
@app.route('/admin')
def admin_panel():
    """פאנל ניהול מתקדם"""
    password = request.args.get('password', '')
    if password != ADMIN_PASSWORD:
        return "❌ גישה נדחתה - סיסמה לא תקינה", 401
    
    try:
        stats = get_user_stats()
        recent_activity = get_recent_activity(20)
        pending_payments = get_pending_payments()
        groups = get_all_groups()
    except Exception as e:
        logger.error(f"Error getting admin data: {e}")
        stats = {'total_users': 0, 'active_today': 0, 'verified_payments': 0, 'pending_payments': 0, 'actions_today': 0}
        recent_activity = []
        pending_payments = []
        groups = []
    
    admin_html = """
<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
    <meta charset="UTF-8">
    <title>SLH - פאנל ניהול</title>
    <style>
        body { font-family: Arial; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
        .header { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; border-left: 5px solid #3498db; }
        .stat-number { font-size: 2em; font-weight: bold; color: #667eea; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 SLH - פאנל ניהול</h1>
            <p>ניהול הבוט וניטור פעילות</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{{ stats.total_users }}</div>
                <div>משתמשים רשומים</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.active_today }}</div>
                <div>פעילים היום</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.pending_payments }}</div>
                <div>תשלומים ממתינים</div>
            </div>
        </div>

        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3>📊 סטטיסטיקות מערכת</h3>
            <p>✅ הבוט פעיל ומוכן לקבל הודעות</p>
            <p>🌐 Webhook: {{ WEBHOOK_URL }}</p>
        </div>
    </div>
</body>
</html>
    """
    
    return render_template_string(admin_html, stats=stats, recent_activity=recent_activity, 
                               pending_payments=pending_payments, groups=groups, WEBHOOK_URL=WEBHOOK_URL)

def initialize_bot():
    """אתחול הבוט"""
    try:
        # קביעת webhook
        bot.set_webhook(WEBHOOK_URL)
        logger.info(f"✅ Webhook set: {WEBHOOK_URL}")
        
        # הודעת אתחול
        send_admin_alert("🚀 **בוט SLH הותחל בהצלחה!**\nהמערכת פעילה ומוכנה.")
        
    except Exception as e:
        logger.error(f"Bot initialization error: {e}")

# אתחול
initialize_bot()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
