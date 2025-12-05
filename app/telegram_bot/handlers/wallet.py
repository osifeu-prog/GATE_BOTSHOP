from __future__ import annotations

from decimal import Decimal

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, Application

from ...database import AsyncSessionLocal
from ...services.trade_mode_service import (
    get_or_create_user,
    get_or_create_settings,
)
from ...services.wallet_service import (
    get_or_create_default_wallets,
)
from ...services.ton_client import get_account_balance_ton


async def wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or update.effective_message is None:
        return

    try:
        async with AsyncSessionLocal() as session:
            user = await get_or_create_user(
                session,
                telegram_id=update.effective_user.id,
                username=update.effective_user.username,
                first_name=update.effective_user.first_name,
            )
            settings_row = await get_or_create_settings(session, user)
            wallets = await get_or_create_default_wallets(session, user.id)
            await session.commit()
    except Exception:
        # כאן אפשר בעתיד להוסיף לוג מפורט, כרגע נשלח הודעה גנרית
        await update.effective_message.reply_text("❗ אירעה שגיאה בטעינת הארנק. נסה שוב עוד רגע.")
        return

    user_net = settings_row.network

    relevant = [w for w in wallets if w.network == user_net]
    if not relevant:
        await update.effective_message.reply_text("אין לך עדיין ארנקים פעילים במערכת.")
        return

    # ננסה לקרוא balance אמיתי אם יש כתובת ארנק Real
    real_wallets = [w for w in relevant if w.kind == "real"]
    onchain_text = "לא הוגדרה עדיין כתובת TON אישית.\n"
    onchain_balance = Decimal("0")

    if real_wallets and real_wallets[0].address:
        address = real_wallets[0].address
        onchain_balance = await get_account_balance_ton(
            address=address,
            network=user_net,  # "testnet" / "mainnet"
        )
        onchain_text = (
            f"כתובת TON ({user_net}):\n"
            f"`{address}`\n\n"
            f"יתרה על השרשרת (משוערת): {onchain_balance:.4f} TON\n"
        )

    lines: list[str] = []
    lines.append("💼 מצב הארנק שלך")
    lines.append("")
    lines.append(f"מצב מסחר נוכחי: {settings_row.trade_mode}")
    lines.append(f"רשת: {user_net}")
    lines.append("")
    lines.append("📊 יתרות פנימיות (Ledger):")

    for w in relevant:
        kind_label = "Real" if w.kind == "real" else "Demo"
        # שים לב: השדות האלה עכשיו קיימים במודל wallet
        lines.append(
            f"• {kind_label} – TON={w.balance_ton}  USDT={w.balance_usdt}  SLH={w.balance_slh}"
        )

    lines.append("")
    lines.append("⛓ מצב On-Chain:")
    lines.append(onchain_text)

    text = "\n".join(lines)
    await update.effective_message.reply_text(text, parse_mode="Markdown")


def register_wallet_handlers(app: Application) -> None:
    app.add_handler(CommandHandler("wallet", wallet_command))
