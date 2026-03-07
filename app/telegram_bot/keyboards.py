from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def trade_mode_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("נ¦ A. ׳׳¡׳—׳¨ ׳׳׳™׳×׳™", callback_data="trade_mode:real"),
        ],
        [
            InlineKeyboardButton("נ© B. ׳¡׳™׳׳•׳׳¦׳™׳”", callback_data="trade_mode:sim"),
        ],
        [
            InlineKeyboardButton("נ¨ C. ׳׳¦׳‘ ׳”׳™׳‘׳¨׳™׳“׳™", callback_data="trade_mode:hybrid"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)

