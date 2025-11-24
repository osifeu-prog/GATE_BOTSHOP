import logging
from config import ADMIN_GROUP_ID, ADMIN_USER_ID
from telegram import Bot
import os

logger = logging.getLogger(__name__)

# אתחול הבוט
try:
    bot = Bot(token=os.environ.get('BOT_TOKEN'))
    logger.info("Bot initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize bot: {e}")
    raise

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
