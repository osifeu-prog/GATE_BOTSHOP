from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def trade_mode_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("🟦 A. מסחר אמיתי", callback_data="trade_mode:real"),
        ],
        [
            InlineKeyboardButton("🟩 B. סימולציה", callback_data="trade_mode:sim"),
        ],
        [
            InlineKeyboardButton("🟨 C. מצב היברידי", callback_data="trade_mode:hybrid"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)
