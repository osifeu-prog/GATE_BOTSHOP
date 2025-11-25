import logging
import os
from telegram import Bot
from telegram.error import NetworkError

from config import ADMIN_GROUP_ID, ADMIN_USER_ID, BOT_TOKEN

logger = logging.getLogger(__name__)

# אתחול הבוט עם טיפול בשגיאות
try:
    bot = Bot(token=BOT_TOKEN)
    logger.info("✅ Bot initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize bot: {e}")
    # יצירת bot דמה כדי שהאפליקציה תרוץ
    class DummyBot:
        def __init__(self):
            self.id = 0
        def set_webhook(self, *args, **kwargs):
            return True
        def send_message(self, *args, **kwargs):
            return None
        def send_photo(self, *args, **kwargs):
            return None
    bot = DummyBot()

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

# שאר הפונקציות נשארות כמו שהיו...
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
        if "Message is not modified" in str(e):
            logger.debug("Message not modified - same content")
            return True
        else:
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
        return True
    except Exception as e:
        logger.error(f"Failed to send admin alert: {e}")
        return False

def send_payment_confirmation(user_id, user_name, payment_type, amount, proof_text="", image_file_id=None):
    """שולח אישור תשלום וקובע במסד נתונים"""
    try:
        payment_message = f"💰 **אישור תשלום חדש!**\n👤 ממשתמש: {user_name}\n🆔 ID: `{user_id}`\n💳 סוג: {payment_type}\n💸 סכום: {amount}₪"
        
        if proof_text:
            payment_message += f"\n📝 פרטים: {proof_text}"
        
        # שליחת התראה לאדמין
        if image_file_id:
            bot.send_photo(
                chat_id=ADMIN_USER_ID,
                photo=image_file_id,
                caption=payment_message,
                parse_mode='Markdown'
            )
        else:
            safe_send_message(ADMIN_USER_ID, payment_message)
        
        logger.info(f"Payment confirmation sent for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error in send_payment_confirmation: {e}")
        return False
