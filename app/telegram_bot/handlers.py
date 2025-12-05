from __future__ import annotations

from typing import List
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from app.config import settings
from app.services.signal_engine import generate_signal
from app.services.ai_explainer import explain_signal
from app.services.exchange_routing import compare_exchanges


SUPPORTED = [s.upper() for s in settings.SUPPORTED_SYMBOLS]


def get_handlers() -> List[CommandHandler]:
    return [
        CommandHandler("start", start),
        CommandHandler("help", help_command),
        CommandHandler("signal", signal_command),
        CommandHandler("compare", compare_command),
    ]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "ברוך הבא לשער המסחר החכם של GATE BOTSHOP.\n\n"
        "כאן תקבל:\n"
        "• התראות מסחר למטבעות: BTC, ETH, BNB, SOL, XRP, TON.\n"
        "• ניתוח טכני מהיר לעסקאות דקות/שעות.\n"
        "• הסבר ידידותי על סיבת הכניסה, סטופ לוס וצפי זמן.\n"
        "• השוואת מחירי פיוצ'רז בין בורסות מובילות.\n\n"
        "פקודות חשובות:\n"
        "/signal <symbol> <timeframe> – ניתוח עסקה (לדוגמה: /signal BTCUSDT 15m)\n"
        "/compare <symbol> – השוואת מחירים בין בורסות (לדוגמה: /compare ETHUSDT)\n"
        "/help – עזרה מלאה."
    )
    if update.message:
        await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "עזרה – GATE BOTSHOP AI TRADER\n\n"
        "/signal <symbol> <timeframe>\n"
        "  מקבל ניתוח לעסקת פיוצ'רז לטווח קצר.\n"
        "  סמלים נתמכים: " + ", ".join(SUPPORTED) + "\n"
        "  טיימפריימים נפוצים: 5m, 15m, 1h, 4h\n\n"
        "/compare <symbol>\n"
        "  השוואת מחירי פיוצ'רז בין Binance / Bybit / OKX (אם זמין).\n\n"
        "שים לב: זהו כלי לימודי ואינפורמטיבי בלבד – אין לראות בו ייעוץ השקעות."
    )
    if update.message:
        await update.message.reply_text(text)


async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    if not context.args:
        await update.message.reply_text(
            "שימוש: /signal <symbol> <timeframe>\nלדוגמה: /signal BTCUSDT 15m"
        )
        return

    symbol = context.args[0].upper()
    timeframe = context.args[1] if len(context.args) > 1 else settings.DEFAULT_TIMEFRAME

    if symbol not in SUPPORTED:
        await update.message.reply_text(
            "הסמל שביקשת אינו מורשה כרגע. סמלים נתמכים: " + ", ".join(SUPPORTED)
        )
        return

    try:
        trade_signal = await generate_signal(symbol, timeframe)
    except Exception as e:
        await update.message.reply_text(f"לא הצלחתי לייצר כרגע ניתוח: {e}")
        return

    try:
        quotes = await compare_exchanges(symbol)
        best = min(quotes, key=lambda q: q.price)
        trade_signal.exchange_hint = best.exchange
    except Exception:
        quotes = []
        best = None

    explanation = await explain_signal(trade_signal, exchange_hint=getattr(trade_signal, "exchange_hint", None))

    lines = [
        f"🔥 הצעת עסקה עבור {trade_signal.symbol} ({trade_signal.timeframe})",
        "",
        f"כיוון: {trade_signal.direction}",
        f"כניסה משוערת: {trade_signal.entry:.4f}",
        f"סטופ לוס: {trade_signal.stop_loss:.4f}",
        f"טייק פרופיט: {trade_signal.take_profit:.4f}",
        f"יחס סיכוי/סיכון: {trade_signal.risk_reward:.2f}",
        f"צפי זמן עסקה: ~{trade_signal.estimated_duration_minutes} דקות",
        f"רמת ביטחון: {trade_signal.confidence * 100:.1f}%",
    ]

    if best and quotes:
        lines.append("")
        lines.append("📊 השוואת מחירים (עתידי / פיוצ'רז):")
        for q in quotes:
            mark = "✅" if q.exchange == best.exchange else "•"
            lines.append(f"{mark} {q.exchange}: {q.price:.4f} ({q.symbol})")

    lines.append("")
    lines.append("🧠 הסבר לוגי:")
    lines.append(explanation)
    lines.append("")
    lines.append("⚠ אין לראות במידע זה ייעוץ השקעות. מסחר בפיוצ'רז מסוכן ועלול לגרום להפסד מלא של ההשקעה.")

    await update.message.reply_text("\n".join(lines))


async def compare_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    if not context.args:
        await update.message.reply_text("שימוש: /compare <symbol> (לדוגמה: /compare BTCUSDT)")
        return

    symbol = context.args[0].upper()
    if symbol not in SUPPORTED:
        await update.message.reply_text(
            "הסמל שביקשת אינו מורשה כרגע. סמלים נתמכים: " + ", ".join(SUPPORTED)
        )
        return

    try:
        quotes = await compare_exchanges(symbol)
    except Exception as e:
        await update.message.reply_text(f"לא הצלחתי להשיג כרגע נתונים: {e}")
        return

    if not quotes:
        await update.message.reply_text("לא הצלחתי לקבל מחירים לבורסות הנתמכות.")
        return

    best = min(quotes, key=lambda q: q.price)

    lines = [f"📊 השוואת מחירי פיוצ'רז עבור {symbol}:", ""]
    for q in quotes:
        mark = "✅" if q.exchange == best.exchange else "•"
        lines.append(f"{mark} {q.exchange}: {q.price:.4f} ({q.symbol})")

    lines.append("")
    lines.append("⚠ הנתונים בזמן אמת אך עלולים להיות שונים מעט מהמחיר בפועל ברגע הביצוע.")

    await update.message.reply_text("\n".join(lines))
