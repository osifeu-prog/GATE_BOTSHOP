import logging
import time
from telegram import Update
from telegram.ext import CallbackContext
from config import ADMIN_USER_ID
from database.operations import get_user_stats, get_all_groups, get_pending_payments, get_recent_activity
from keyboards.menus import get_admin_groups_keyboard
from utils.helpers import safe_edit_message, send_admin_alert

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
                context.bot.send_message(
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

# פונקציות אדמין נוספות...
