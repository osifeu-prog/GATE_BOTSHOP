from __future__ import annotations

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
)

from ...database import AsyncSessionLocal
from ...services.wallet_engine import get_or_create_user, get_or_create_wallets
from ...services.staking_engine import create_stake, list_user_stakes
from ..keyboards import staking_menu_kb, main_menu_kb, wallet_mode_kb
from ..utils import get_user_identity


async def generic_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    tid, username, first_name, last_name = get_user_identity(update)

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, tid, username, first_name, last_name)
        demo, real = await get_or_create_wallets(session, user)

        # wallet mode choice
        if data == "wallet_mode_demo":
            user.mode = "demo"
            await session.commit()
            await query.edit_message_text(
                "מצב הארנק הוגדר ל-*דמו*.",
                parse_mode="Markdown",
                reply_markup=main_menu_kb(),
            )
            return
        elif data == "wallet_mode_real":
            user.mode = "real"
            await session.commit()
            await query.edit_message_text(
                "מצב הארנק הוגדר ל-*אמיתי*.",
                parse_mode="Markdown",
                reply_markup=main_menu_kb(),
            )
            return

        if data == "menu_wallet":
            text = (
                "📊 סטטוס ארנק:\n"
                f"מצב נוכחי: *{user.mode.upper()}*\n"
                f"דמו: {demo.balance_slh:.4f} SLH\n"
                f"אמיתי: {real.balance_slh:.4f} SLH"
            )
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=wallet_mode_kb(),
            )
            return

        if data.startswith("stake_"):
            lock_days = int(data.split("_")[1])
            wallet = demo if user.mode == "demo" else real
            try:
                stake = await create_stake(session, wallet, amount_slh=100.0, lock_days=lock_days)
                await session.commit()
                msg = (
                    "🎯 סטייקינג נפתח!\n"
                    f"סכום: *100* SLH\n"
                    f"נעילה: *{lock_days}* ימים\n"
                    f"APY: *{stake.apy:.2f}%*"
                )
            except Exception as e:
                await session.rollback()
                msg = f"שגיאה בפתיחת סטייקינג: {e}"
            await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=staking_menu_kb())
            return

        if data == "stake_list":
            stakes = await list_user_stakes(session, user.id)
            if not stakes:
                msg = "אין לך עדיין סטייקינג פעיל."
            else:
                lines = []
                for s in stakes:
                    mode = "דמו" if s.is_demo else "אמיתי"
                    status = "פעיל" if s.active else "נסגר"
                    lines.append(
                        f"{mode}: {s.amount_slh:.2f} SLH ל-{s.lock_days} ימים ({status})"
                    )
                msg = "📋 הסטייקינג שלך:\n" + "\n".join(lines)
            await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=staking_menu_kb())
            return

        if data == "menu_staking":
            await query.edit_message_text(
                "בחר תקופת סטייקינג:",
                reply_markup=staking_menu_kb(),
            )
            return

        if data == "menu_rewards":
            msg = "מערכת דרגות ו-XP תתווסף בפירוט בשלב הבא (placeholder)."
            await query.edit_message_text(msg, reply_markup=main_menu_kb())
            return

        if data == "menu_referrals":
            msg = "מודול רפרלים (עץ מרקל) – placeholder ראשוני."
            await query.edit_message_text(msg, reply_markup=main_menu_kb())
            return

        if data == "menu_market":
            msg = "ניתוח שוק מהיר יתווסף כאן – placeholder."
            await query.edit_message_text(msg, reply_markup=main_menu_kb())
            return


def register_callback_handlers(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(generic_callback))
