from telegram import InlineKeyboardMarkup, InlineKeyboardButton


def trade_mode_keyboard(current: str | None = None) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("🟦 מסחר אמיתי (DEX)", callback_data="mode_real")],
        [InlineKeyboardButton("🟩 סימולציה (Futures SIM)", callback_data="mode_sim")],
        [InlineKeyboardButton("🟨 היברידי (Hybrid)", callback_data="mode_hybrid")],
    ]
    return InlineKeyboardMarkup(buttons)
