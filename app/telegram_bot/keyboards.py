from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def trade_mode_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("أ—آ ط¢ع؛ط¢ع؛ط¢آ¦ A. أ—آ³ط¢â€چأ—آ³ط¢طŒأ—آ³أ¢â‚¬â€‌أ—آ³ط¢آ¨ أ—آ³ط¢ع¯أ—آ³ط¢â€چأ—آ³أ¢â€‍آ¢أ—آ³ط£â€”أ—آ³أ¢â€‍آ¢", callback_data="trade_mode:real"),
        ],
        [
            InlineKeyboardButton("أ—آ ط¢ع؛ط¢ع؛ط¢آ© B. أ—آ³ط¢طŒأ—آ³أ¢â€‍آ¢أ—آ³ط¢â€چأ—آ³أ¢â‚¬آ¢أ—آ³ط¢إ“أ—آ³ط¢آ¦أ—آ³أ¢â€‍آ¢أ—آ³أ¢â‚¬â€Œ", callback_data="trade_mode:sim"),
        ],
        [
            InlineKeyboardButton("أ—آ ط¢ع؛ط¢ع؛ط¢آ¨ C. أ—آ³ط¢â€چأ—آ³ط¢آ¦أ—آ³أ¢â‚¬ع© أ—آ³أ¢â‚¬â€Œأ—آ³أ¢â€‍آ¢أ—آ³أ¢â‚¬ع©أ—آ³ط¢آ¨أ—آ³أ¢â€‍آ¢أ—آ³أ¢â‚¬إ“أ—آ³أ¢â€‍آ¢", callback_data="trade_mode:hybrid"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)




