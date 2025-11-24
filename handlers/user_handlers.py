import logging
from telegram import Update
from telegram.ext import CallbackContext
from database.operations import log_user_activity, get_user_language
from keyboards.menus import get_main_keyboard, get_language_keyboard
from translations.texts import get_translation
from utils.helpers import safe_edit_message

logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    """מטפל בפקודה /start - רב-לשוני"""
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id

        # רישום מפורט של המשתמש ושליחת לוג
        log_user_activity(
            chat_id=chat_id,
            first_name=user.first_name or "לא צוין",
            last_name=user.last_name or "",
            username=user.username or "לא צוין",
            action="התחיל שיחה עם הבוט (/start)",
            details=f"User ID: {user.id}, Language: {user.language_code}, Chat Type: {update.message.chat.type if update.message else 'callback'}"
        )

        # שליחת תמונה עם הודעת ברוך הבא
        welcome_image_url = "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2032&q=80"
        
        try:
            if update.message:
                update.message.reply_photo(
                    photo=welcome_image_url,
                    caption=get_translation(get_user_language(user.id), 'welcome', name=user.first_name),
                    parse_mode='Markdown',
                    reply_markup=get_main_keyboard(user.id)
                )
            else:
                update.callback_query.message.reply_photo(
                    photo=welcome_image_url,
                    caption=get_translation(get_user_language(user.id), 'welcome', name=user.first_name),
                    parse_mode='Markdown',
                    reply_markup=get_main_keyboard(user.id)
                )
            return
        except Exception as e:
            logger.warning(f"Could not send welcome image: {e}")

        # אם לא הצליחה התמונה, שולח טקסט בלבד
        if update.message:
            update.message.reply_text(
                get_translation(get_user_language(user.id), 'welcome', name=user.first_name),
                reply_markup=get_main_keyboard(user.id),
                parse_mode='Markdown'
            )
        else:
            update.callback_query.message.reply_text(
                get_translation(get_user_language(user.id), 'welcome', name=user.first_name),
                reply_markup=get_main_keyboard(user.id),
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        if update.message:
            update.message.reply_text("❌ אירעה שגיאה. אנא נסה שוב.")

def language_handler(update: Update, context: CallbackContext) -> None:
    """מטפל בבחירת שפה"""
    query = update.callback_query
    query.answer()
    
    user_id = query.from_user.id
    lang_code = query.data.replace('lang_', '')
    
    # שמירת השפה במסד נתונים
    from database.operations import set_user_language
    set_user_language(user_id, lang_code)
    
    # הודעת אישור לפי שפה
    confirmation_messages = {
        'he': "✅ שפת הממשק שונתה לעברית",
        'en': "✅ Interface language changed to English", 
        'ru': "✅ Язык интерфейса изменен на русский",
        'ar': "✅ تم تغيير لغة الواجهة إلى العربية"
    }
    
    query.edit_message_text(
        text=confirmation_messages.get(lang_code, "Language changed"),
        reply_markup=get_main_keyboard(user_id)
    )

# handlers נוספים למשתמשים...
