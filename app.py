import os
import logging
from flask import Flask, request, jsonify
from telegram.ext import Dispatcher

from config import BOT_TOKEN, WEBHOOK_URL
from database.models import init_db
from handlers import setup_handlers
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

# הגדרת handlers
setup_handlers(dispatcher)

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
