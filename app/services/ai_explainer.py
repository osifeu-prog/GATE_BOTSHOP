from __future__ import annotations

from typing import Optional
import httpx

from app.schemas import TradeSignal
from app.config import settings


def _basic_explanation(signal: TradeSignal, exchange_hint: Optional[str] = None) -> str:
    """Deterministic fallback explanation (ללא AI חיצוני)."""
    direction_he = {
        "LONG": "לונג (קנייה)",
        "SHORT": "שורט (מכירה)",
        "NEUTRAL": "ללא כיוון חד משמעי",
    }

    d = signal.direction
    risk_text = (
        f"יחס סיכוי/סיכון ~ {signal.risk_reward:.2f} עם סטופ לוס ב-{signal.stop_loss:.4f} "
        f"ויעד ראשוני ב-{signal.take_profit:.4f}."
    )

    base = (
        f"ניתוח למטבע {signal.symbol} בטיימפריים {signal.timeframe}.\n"
        f"המערכת מזהה כרגע כיוון: {direction_he.get(d, d)} ברמת ביטחון של כ-{signal.confidence * 100:.1f}%.\n"
        f"מחיר כניסה משוער: {signal.entry:.4f}.\n"
        f"צפי משך עסקה: כ-{signal.estimated_duration_minutes} דקות.\n"
        f"{risk_text}\n"
    )

    trend_part = (
        f"ממוצע נע קצר ({signal.extra.get('short_ma')}) יחסית לממוצע נע ארוך ({signal.extra.get('long_ma')}) "
        f"והסטייה ביניהם מצביעה על עוצמת מגמה בסיסית. "
    )

    if d == "LONG":
        dir_part = (
            "המגמה הנוכחית מצביעה על נטייה לעלייה, כאשר המערכת מציעה לונג בזהירות, "
            "עם סטופ מתחת לאזור התמיכה הקרוב."
        )
    elif d == "SHORT":
        dir_part = (
            "המגמה הנוכחית מצביעה על חולשה במחיר, כאשר המערכת מציעה שורט מבוקר, "
            "עם סטופ מעל רמת ההתנגדות האחרונה."
        )
    else:
        dir_part = (
            "כרגע אין עדיפות ברורה ללונג או לשורט – ייתכן שהשוק במצב דשדוש, "
            "ולכן ההמלצה היא להמתין או לעבוד עם היקף סיכון קטן במיוחד."
        )

    ex_part = ""
    if exchange_hint:
        ex_part = f"\nלמסחר בפיוצ'רז, בדוק את העמלות והמינוף הזמין בבורסה {exchange_hint}."

    return base + trend_part + dir_part + ex_part


async def _explain_with_openai(signal: TradeSignal, exchange_hint: Optional[str]) -> str:
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not configured")

    system_prompt = (
        "You are an expert crypto futures trading educator. "
        "Explain trade ideas in clear, simple Hebrew, for short-term trades (minutes to hours). "
        "Always remind that this is not financial advice."
    )

    user_prompt = f"""תן הסבר מקצועי אבל פשוט לאיתות מסחר הבא (בעברית):

מטבע: {signal.symbol}
טיימפריים: {signal.timeframe}
כיוון: {signal.direction}
מחיר כניסה: {signal.entry}
סטופ לוס: {signal.stop_loss}
טייק פרופיט: {signal.take_profit}
יחס סיכוי/סיכון: {signal.risk_reward}
משך עסקה משוער (בדקות): {signal.estimated_duration_minutes}
ממוצע נע קצר: {signal.extra.get('short_ma')}
ממוצע נע ארוך: {signal.extra.get('long_ma')}
תנודתיות אחרונה: {signal.extra.get('volatility')}

הסבר:
- למה דווקא הכיוון הזה (לונג/שורט/נייטרלי)
- איך בחרנו סטופ לוס ויעד
- למה מדובר בעסקה לטווח של דקות/שעות
- איך כדאי לחשוב על גודל פוזיציה וסיכון אחוזי (בלי מספרים אישיים)
- להזכיר שזה כלי לימודי בלבד, לא ייעוץ ולא הבטחת רווח

{f"אם רלוונטי, אפשר לציין שבורסה מומלצת למסחר היא {exchange_hint}." if exchange_hint else ""}
"""

    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": settings.OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.4,
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body)
        r.raise_for_status()
        data = r.json()

    try:
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return _basic_explanation(signal, exchange_hint=exchange_hint)


async def _explain_with_hf(signal: TradeSignal, exchange_hint: Optional[str]) -> str:
    if not settings.HF_TOKEN:
        raise RuntimeError("HF_TOKEN not configured")

    prompt = (
        "אתה מורה למסחר בקריפטו. הסבר בעברית, בפשטות וללא הבטחות לרווח, "
        "את ההיגיון בעסקת הפיוצ'רז הבאה, כולל סיכון, סטופ ויעד:\n\n"
    ) + _basic_explanation(signal, exchange_hint=exchange_hint)

    api_url = settings.HF_API_URL or f"https://api-inference.huggingface.co/models/{settings.HF_MODEL}"
    headers = {"Authorization": f"Bearer {settings.HF_TOKEN}"}
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 400, "temperature": 0.4}}

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(api_url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()

    if isinstance(data, list) and data and "generated_text" in data[0]:
        return str(data[0]["generated_text"]).strip()

    return _basic_explanation(signal, exchange_hint=exchange_hint)


async def explain_signal(signal: TradeSignal, exchange_hint: Optional[str] = None) -> str:
    """Public entry point: tries AI provider, falls back to deterministic text."""
    try:
        if settings.AI_PROVIDER == "openai" and settings.OPENAI_API_KEY:
            return await _explain_with_openai(signal, exchange_hint)
        if settings.AI_PROVIDER == "huggingface" and settings.HF_TOKEN:
            return await _explain_with_hf(signal, exchange_hint)
    except Exception:
        # On any AI error, fall back to basic explanation
        pass

    return _basic_explanation(signal, exchange_hint=exchange_hint)
