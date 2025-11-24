import logging
from telegram import Update
from telegram.ext import CallbackContext

from database.operations import save_group
from utils.helpers import send_admin_alert

logger = logging.getLogger(__name__)

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
                "👑 **לאדמין:** השתמש ב-`/groupid` או `/chaid` כדי לראות את כל הקבוצות."
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
            # רישום/עדכון הקבוצה במסד הנתונים עם פרטים מעודכנים
            save_group(chat.id, chat.title, chat.type)
            
            # לוג לצורך ניפוי באגים
            logger.info(f"Group activity detected and updated: {chat.title} (ID: {chat.id}, Type: {chat.type})")
            
    except Exception as e:
        logger.error(f"Error in handle_group_activity: {e}")
