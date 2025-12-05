from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_kb() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("📊 סטטוס ארנק", callback_data="menu_wallet"),
            InlineKeyboardButton("🎯 סטייקינג", callback_data="menu_staking"),
        ],
        [
            InlineKeyboardButton("🏆 משימות ודרגות", callback_data="menu_rewards"),
            InlineKeyboardButton("👥 הפניות", callback_data="menu_referrals"),
        ],
        [
            InlineKeyboardButton("📈 ניתוח שוק", callback_data="menu_market"),
        ],
    ]
    return InlineKeyboardMarkup(rows)


def wallet_mode_kb() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("🧪 דמו", callback_data="wallet_mode_demo"),
            InlineKeyboardButton("💰 אמיתי", callback_data="wallet_mode_real"),
        ]
    ]
    return InlineKeyboardMarkup(rows)


def staking_menu_kb() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("7 ימים", callback_data="stake_7"),
            InlineKeyboardButton("30 ימים", callback_data="stake_30"),
            InlineKeyboardButton("90 ימים", callback_data="stake_90"),
        ],
        [
            InlineKeyboardButton("📋 הסטייקינג שלי", callback_data="stake_list"),
        ],
    ]
    return InlineKeyboardMarkup(rows)


def admin_menu_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("👤 משתמשים", callback_data="admin_users")],
        [InlineKeyboardButton("💼 סטייקינג", callback_data="admin_stakes")],
        [InlineKeyboardButton("👥 רפרלים", callback_data="admin_referrals")],
    ]
    return InlineKeyboardMarkup(rows)
