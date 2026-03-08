from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def trade_mode_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("ًںں¦ A. ×‍×،×—×¨ ×گ×‍×™×ھ×™", callback_data="trade_mode:real"),
        ],
        [
            InlineKeyboardButton("ًںں© B. ×،×™×‍×•×œ×¦×™×”", callback_data="trade_mode:sim"),
        ],
        [
            InlineKeyboardButton("ًںں¨ C. ×‍×¦×‘ ×”×™×‘×¨×™×“×™", callback_data="trade_mode:hybrid"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)

