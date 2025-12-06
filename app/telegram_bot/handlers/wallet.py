from __future__ import annotations

from decimal import Decimal

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from ...database import async_session_maker
from ...models.user import User
from ...models.wallet import Wallet
from ...services.trade_mode_service import (
    get_or_create_user,
    get_or_create_settings,
    get_trade_mode_label,
)


async def _get_or_create_wallet_for_user(session, user: User) -> Wallet:
    """
    מביא או יוצר רשומת ארנק בסיסית עבור המשתמש.
    השדות כאן מניחים מודל גמיש עם ברירות מחדל,
    ואם נוסיף עמודות בהמשך – נרחיב בהתאם.
    """
    from sqlalchemy import select

    stmt = select(Wallet).where(Wallet.user_id == user.id)
    result = await session.execute(stmt)
    wallet = result.scalar_one_or_none()

    if wallet:
        return wallet

    # יצירת ארנק בסיסי חדש
    wallet = Wallet(
        user_id=user.id,
    )
    session.add(wallet)
    await session.flush()
    return wallet


def _safe_decimal(value, default: str = "0") -> Decimal:
    try:
        if value is None:
            return Decimal(default)
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


async def wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    פקודת /wallet – מציגה סטטוס ארנק פנימי + מצב מסחר.
    בשלב זה זו תצוגה "עדינה" כדי לא לשבור אם חסרות עמודות.
    """
    if update.effective_user is None:
        return

    tg_user = update.effective_user
    chat_id = tg_user.id

    async with async_session_maker() as session:
        # משתמש + הגדרות מסחר
        user = await get_or_create_user(
            session=session,
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
        )
        settings = await get_or_create_settings(session, user)
        wallet = await _get_or_create_wallet_for_user(session, user)

        # ננסה לשלוף שדות סטנדרטיים אם קיימים במודל
        trade_mode = getattr(settings, "trade_mode", "sim")
        trade_mode_label = get_trade_mode_label(trade_mode)

        internal_slh = _safe_decimal(getattr(wallet, "internal_slh_balance", Decimal("0")))
        sim_usd = _safe_decimal(getattr(wallet, "sim_usd_balance", Decimal("0")))
        real_usd = _safe_decimal(getattr(wallet, "real_usd_balance", Decimal("0")))

        ton_addr_testnet = getattr(wallet, "ton_address_testnet", None)
        ton_addr_mainnet = getattr(wallet, "ton_address_mainnet", None)

        # טקסט ידידותי
        lines: list[str] = []

        lines.append("📊 *ארנק GATE BOTSHOP שלך*")
        lines.append("")
        lines.append(f"מצב מסחר נוכחי: {trade_mode_label}")
        lines.append("")

        lines.append("💰 *יתרות פנים־מערכת*")
        lines.append(f"• סימולציה (USD): `{sim_usd}`")
        lines.append(f"• מסחר אמיתי (USD): `{real_usd}`")
        lines.append(f"• SLH פנימי: `{internal_slh}`")
        lines.append("")

        lines.append("🔗 *כתובות TON*")
        if ton_addr_testnet:
            lines.append(f"• Testnet: `{ton_addr_testnet}`")
        else:
            lines.append("• Testnet: _(טרם חובר – יתווסף בשלבי TON)_")

        if ton_addr_mainnet:
            lines.append(f"• Mainnet: `{ton_addr_mainnet}`")
        else:
            lines.append("• Mainnet: _(טרם חובר – יתווסף בשלבי TON)_")

        lines.append("")
        lines.append("בהמשך נוסיף כאן גם:")
        lines.append("• סטייקינג אמיתי על TON/SLH")
        lines.append("• מצב P2P מלא")
        lines.append("• חיבור ישיר לבורסות (DEX/Hybrid)")

        text = "\n".join(lines)

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="Markdown",
    )


def register_wallet_handlers(app: Application) -> None:
    """
    פונקציה שה-bot_app.py מייבא.
    כאן אנחנו רושמים את כל הפקודות הקשורות לארנק.
    """
    app.add_handler(CommandHandler("wallet", wallet_command))
