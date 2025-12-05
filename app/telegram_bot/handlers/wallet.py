from __future__ import annotations

from decimal import Decimal
import logging

from telegram import Update
from telegram.ext import ContextTypes

from ...database import AsyncSessionLocal
from ...services.trade_mode_service import (
    get_or_create_user,
    get_or_create_settings,
)
from ...services.wallet_service import get_or_create_default_wallets
from ...services.ton_client import get_account_balance_ton

logger = logging.getLogger("gate_botshop_ai")


async def wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    if tg_user is None:
        return

    try:
        async with AsyncSessionLocal() as session:
            user = await get_or_create_user(
                session=session,
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
            )
            settings_row = await get_or_create_settings(session, user)
            wallets = await get_or_create_default_wallets(session, user, settings_row)
            await session.commit()
    except Exception as e:
        # לוג מלא כדי שנוכל לראות מה נשבר ב־Railway
        logger.exception("Error while loading wallet for user %s", tg_user.id)
        await update.effective_message.reply_text(
            "❗ אירעה שגיאה בטעינת הארנק. נסה שוב עוד רגע."
        )
        return

    # --- עיבוד ארנקים ---
    user_net = settings_row.network or "ton_testnet"

    relevant = [w for w in wallets if w.network in ("testnet", "ton_testnet", "ton_mainnet")]
    if not relevant:
        await update.effective_message.reply_text("לא נמצאו ארנקים פעילים עבור המשתמש.")
        return

    demo_wallets = [w for w in relevant if w.kind == "demo"]
    real_wallets = [w for w in relevant if w.kind == "real"]

    # חישוב יתרות דמו
    demo_text = "— ארנק סימולציה —\n"
    if demo_wallets:
        d = demo_wallets[0]
        demo_text += (
            f"TON (SIM): {d.balance_ton:.4f}\n"
            f"USDT (SIM): {d.balance_usdt:.2f}\n"
            f"SLH (SIM): {d.balance_slh:.4f}\n"
        )
    else:
        demo_text += "לא קיים עדיין ארנק סימולציה.\n"

    # חישוב יתרות ריאליות (על TON)
    onchain_text = "— ארנק TON אמיתי —\n"
    if real_wallets and real_wallets[0].address:
        address = real_wallets[0].address
        try:
            onchain_balance = await get_account_balance_ton(address=address, network=user_net)
        except Exception:
            logger.exception("Error while fetching TON balance for %s", address)
            onchain_balance = Decimal("0")
        w = real_wallets[0]
        onchain_text += (
            f"כתובת: `{address}`\n"
            f"TON (on-chain): {onchain_balance:.4f}\n"
            f"USDT (ledger): {w.balance_usdt:.2f}\n"
            f"SLH (ledger): {w.balance_slh:.4f}\n"
        )
    else:
        onchain_text += "לא הוגדרה עדיין כתובת TON אישית.\n"

    text = (
        "💼 *מצב הארנק שלך*\n\n"
        f"{demo_text}\n"
        f"{onchain_text}\n"
        "_בהמשך נוסיף הפקדות/משיכות אמיתיות על TON + סטייקינג._"
    )

    await update.effective_message.reply_markdown(text)
