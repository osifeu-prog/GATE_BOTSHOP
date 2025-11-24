import os
import logging
from flask import Flask, request, jsonify
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

from config import BOT_TOKEN, WEBHOOK_URL
from database.models import init_db
from handlers.admin_handlers import admin, broadcast
from handlers.user_handlers import start, language_handler
from handlers.group_handlers import chatid, groupid, chaid, handle_group_add, handle_group_activity
from utils.helpers import bot

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
dispatcher = Dispatcher(bot, None, workers=4)

def setup_handlers():
    """מגדיר את כל ה-handlers"""
    # handler לפקודת start
    dispatcher.add_handler(CommandHandler("start", start))
    
    # handlers לפקודות אדמין
    dispatcher.add_handler(CommandHandler("chatid", chatid))
    dispatcher.add_handler(CommandHandler("groupid", groupid))
    dispatcher.add_handler(CommandHandler("chaid", chaid))
    dispatcher.add_handler(CommandHandler("admin", admin))
    dispatcher.add_handler(CommandHandler("broadcast", broadcast))
    
    # handlers נוספים...
    dispatcher.add_handler(CallbackQueryHandler(language_handler, pattern='^lang_'))
    
    # handler להוספת הבוט לקבוצות
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, handle_group_add))
    
    # handler למעקב אחר כל ההודעות בקבוצות
    dispatcher.add_handler(MessageHandler(
        Filters.chat_type.groups & Filters.all, 
        handle_group_activity
    ))
    
    logger.info("All handlers setup completed")

# הגדרת Flask routes
@app.route('/')
def home():
    return jsonify({"status": "SLH Bot is running!"})

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
            return jsonify({"status": "Webhook set successfully"}), 200
        else:
            logger.error("Failed to set webhook")
            return jsonify({"status": "Failed to set webhook"}), 500
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return jsonify({"status": f"Error: {str(e)}"}), 500

if __name__ == '__main__':
    # הגדרת handlers
    setup_handlers()
    
    # קביעת webhook
    bot.set_webhook(WEBHOOK_URL)
    
    # הפעלת שרת Flask
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
