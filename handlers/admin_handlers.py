import logging
import time
import sqlite3
from telegram import Update
from telegram.ext import CallbackContext

from config import ADMIN_USER_ID
from database.operations import get_user_stats, get_all_groups, get_pending_payments, save_group
from keyboards.menus import get_admin_groups_keyboard
from utils.helpers import safe_send_message, send_admin_alert

logger = logging.getLogger(__name__)

def admin(update: Update, context: CallbackContext) -> None:
    """פקודת אדמין - מציגה סטטיסטיקות וניהול"""
    try:
        user = update.effective_user
        
        # בדיקה אם המשתמש הוא אדמין
        if str(user.id) != ADMIN_USER_ID:
            update.message.reply_text("❌ אתה לא מורשה להשתמש בפקודה זו.")
            return

        stats = get_user_stats()
        groups = get_all_groups()
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
        message += "• `/groupid` או `/chaid` - הצג ID קבוצה/רשימת קבוצות\n"
        message += "• `/admin` - פאנל ניהול זה\n"
        message += "• `/broadcast` - שליחת הודעה לכל המשתמשים\n"
        message += "• `/group_broadcast` - שליחת הודעה לכל הקבוצות\n"
        message += "• `/refresh_groups` - רענון רשימת הקבוצות\n"
        message += "• 🌐 https://web-production-b425.up.railway.app/admin?password=slh2025 - פאנל ניהול מתקדם\n\n"
        
        message += "🚀 **לאסוף צ'אטים נוספים:**\n"
        message += "1. הזמן את הבוט לקבוצה\n"
        message += "2. שלח `/start` או `/groupid` בקבוצה\n"
        message += "3. הקבוצה תירשם אוטומטית\n"
        
        update.message.reply_text(message, parse_mode='Markdown', reply_markup=get_admin_groups_keyboard())
            
    except Exception as e:
        logger.error(f"Error in admin command: {e}")
        update.message.reply_text("❌ אירעה שגיאה בפקודת האדמין.")

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
            
            # שמירת/עדכון הקבוצה במסד הנתונים
            save_group(chat_id, chat_title, update.message.chat.type)
            message += f"\n\n✅ **הקבוצה נשמרה/עודכנה במסד הנתונים!**"
            
            # הוספת כפתורים לפעולות נוספות
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = [
                [InlineKeyboardButton("📊 הצג כל הקבוצות", callback_data='show_all_groups')],
                [InlineKeyboardButton("🔄 רענן קבוצות", callback_data='refresh_groups')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            # אם נשלחה בצ'אט פרטי, שלח את רשימת כל הקבוצות
            show_all_groups_command(update, context)
            
    except Exception as e:
        logger.error(f"Error in chatid command: {e}")
        update.message.reply_text("❌ אירעה שגיאה בקבלת ID הקבוצה.")

def groupid(update: Update, context: CallbackContext) -> None:
    """פקודת groupid - alias ל-chatid"""
    chatid(update, context)

def chaid(update: Update, context: CallbackContext) -> None:
    """פקודת chaid - alias ל-chatid"""
    chatid(update, context)

def show_all_groups_command(update: Update, context: CallbackContext):
    """מציג את כל הקבוצות"""
    try:
        user = update.effective_user
        
        if str(user.id) != ADMIN_USER_ID:
            if update.message:
                update.message.reply_text("❌ אתה לא מורשה להשתמש בפקודה זו.")
            return

        # קבלת כל הקבוצות האמיתיות
        all_chats = get_all_groups()
        
        if all_chats:
            message = f"📊 **כל הצ'אטים שהבוט חבר בהם ({len(all_chats)}):**\n\n"
            
            for i, chat in enumerate(all_chats, 1):
                chat_id = chat[0]
                chat_title = chat[1] 
                chat_type = chat[2] if len(chat) > 2 else "unknown"
                message += f"{i}. **{chat_title}**\n   ID: `{chat_id}` | Type: {chat_type}\n\n"
            
            message += "💡 **הערה:** הקבוצות נשמרות אוטומטית כאשר הבוט פעיל בהן."
            
        else:
            message = "❌ הבוט לא חבר באף צ'אט שנרשם במערכת.\n\n"
            message += "💡 **טיפים:**\n"
            message += "• הזמן את הבוט לקבוצה ונסה שוב\n"
            message += "• שלח /start בקבוצה כדי לרשום אותה\n"
            message += "• השתמש ב-/chatid בתוך קבוצה כדי לרשום אותה"
        
        # שליחת ההודעה
        if update.message:
            update.message.reply_text(message, parse_mode='Markdown', reply_markup=get_admin_groups_keyboard())
        elif update.callback_query:
            from utils.helpers import safe_edit_message
            safe_edit_message(update.callback_query, message, get_admin_groups_keyboard())
            
    except Exception as e:
        logger.error(f"Error in show_all_groups_command: {e}")
        error_msg = "❌ אירעה שגיאה בטעינת רשימת הקבוצות"
        if update.message:
            update.message.reply_text(error_msg)
        elif update.callback_query:
            from utils.helpers import safe_edit_message
            safe_edit_message(update.callback_query, error_msg)

def refresh_all_groups(update: Update, context: CallbackContext):
    """פונקציה לרענון כל הקבוצות מהטלגרם"""
    try:
        user = update.effective_user
        
        # בדיקה אם המשתמש הוא אדמין
        if str(user.id) != ADMIN_USER_ID:
            if update.message:
                update.message.reply_text("❌ אתה לא מורשה להשתמש בפקודה זו.")
            return

        # קבלת כל הקבוצות מהמסד נתונים
        current_groups = get_all_groups()
        
        message = f"🔄 **רענון קבוצות בוצע!**\n\n"
        message += f"📊 **קבוצות במסד הנתונים:** {len(current_groups)}\n\n"
        
        for i, group in enumerate(current_groups, 1):
            group_id = group[0]
            group_title = group[1]
            group_type = group[2] if len(group) > 2 else "unknown"
            message += f"{i}. **{group_title}**\n   ID: `{group_id}` | Type: {group_type}\n\n"
        
        if update.message:
            update.message.reply_text(message, parse_mode='Markdown', reply_markup=get_admin_groups_keyboard())
        elif update.callback_query:
            from utils.helpers import safe_edit_message
            safe_edit_message(update.callback_query, message, get_admin_groups_keyboard())
            
    except Exception as e:
        logger.error(f"Error in refresh_all_groups: {e}")
        error_msg = "❌ אירעה שגיאה ברענון הקבוצות"
        if update.message:
            update.message.reply_text(error_msg)
        elif update.callback_query:
            from utils.helpers import safe_edit_message
            safe_edit_message(update.callback_query, error_msg)

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
        
        from utils.helpers import bot
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
        
        from utils.helpers import bot
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
