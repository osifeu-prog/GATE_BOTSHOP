from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database.operations import get_user_language, get_user_slh_balance
from translations.texts import get_translation

def get_main_keyboard(user_id):
    """מחזיר את המקלדת הראשית לפי שפת המשתמש"""
    lang = get_user_language(user_id)
    keyboard = [
        [InlineKeyboardButton(get_translation(lang, 'ecosystem'), callback_data='ecosystem_explanation')],
        [InlineKeyboardButton(get_translation(lang, 'join_community'), callback_data='join_community')],
        [InlineKeyboardButton(get_translation(lang, 'investment'), callback_data='investment')],
        [InlineKeyboardButton(get_translation(lang, 'bot_development'), callback_data='bot_development')],
        [InlineKeyboardButton(get_translation(lang, 'network_marketing'), callback_data='network_marketing')],
        [InlineKeyboardButton(get_translation(lang, 'our_projects'), callback_data='our_projects')],
        [InlineKeyboardButton(get_translation(lang, 'contact'), callback_data='contact'), 
         InlineKeyboardButton(get_translation(lang, 'help'), callback_data='help')],
        [InlineKeyboardButton(get_translation(lang, 'website'), url='https://slh-nft.com/')],
        [InlineKeyboardButton("🌐 שפה / Language", callback_data='change_language')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_language_keyboard():
    """מקלדת בחירת שפה"""
    keyboard = [
        [InlineKeyboardButton("🇮🇱 עברית", callback_data='lang_he')],
        [InlineKeyboardButton("🇺🇸 English", callback_data='lang_en')],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data='lang_ru')],
        [InlineKeyboardButton("🇸🇦 العربية", callback_data='lang_ar')],
        [InlineKeyboardButton("↩️ חזרה", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_payment_keyboard(user_id):
    """מחזיר את מקלדת אפשרויות התשלום לפי שפה"""
    lang = get_user_language(user_id)
    keyboard = [
        [InlineKeyboardButton(get_translation(lang, 'bank_transfer'), callback_data='payment_bank')],
        [InlineKeyboardButton(get_translation(lang, 'ton_payment'), callback_data='payment_ton')],
        [InlineKeyboardButton(get_translation(lang, 'crypto_payment'), callback_data='payment_crypto')],
        [InlineKeyboardButton(get_translation(lang, 'payment_sent'), callback_data='payment_sent')],
        [InlineKeyboardButton(get_translation(lang, 'joining_bonuses'), callback_data='joining_bonuses')],
        [InlineKeyboardButton("↩️ " + ("חזרה" if lang == 'he' else "Back" if lang == 'en' else "Назад" if lang == 'ru' else "رجوع"), callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_groups_keyboard():
    """מקלדת ניהול קבוצות לאדמין"""
    keyboard = [
        [InlineKeyboardButton("📊 הצג כל הקבוצות", callback_data='show_all_groups')],
        [InlineKeyboardButton("🔄 רענן קבוצות", callback_data='refresh_groups')],
        [InlineKeyboardButton("📤 שידור לקבוצות", callback_data='broadcast_groups')],
        [InlineKeyboardButton("💎 חזרה לפאנל", callback_data='back_to_admin')]
    ]
    return InlineKeyboardMarkup(keyboard)

# מקלדות נוספות יועברו כאן...
