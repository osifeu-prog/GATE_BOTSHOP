from __future__ import annotations

from typing import Dict, Any

import httpx

from ..config import settings


async def explain_signal(symbol: str, analysis: Dict[str, Any]) -> str:
    """Small helper that can either call OpenAI/HF or do local template."""
    trend = analysis.get("trend")
    vol = analysis.get("volatility")
    last = analysis.get("last")
    ma20 = analysis.get("ma20")
    ma50 = analysis.get("ma50")

    base_text = (
        f"סיכום מהיר ל-{symbol}:\n"
        f"- מגמה כללית: {trend}\n"
        f"- מחיר אחרון: {last:.2f}\n"
        f"- ממוצע נע 20: {ma20:.2f}\n"
        f"- ממוצע נע 50: {ma50:.2f}\n"
        f"- תנודתיות אחרונה (סטיית תקן): {vol:.4f}\n\n"
        f"הסבר: כאשר המחיר מעל MA20 ו-MA50, זה בדרך כלל מרמז על מומנטום חיובי. "
        f"כאשר MA20 חוצה כלפי מעלה את MA50 זה מחזק את התרחיש השורי לטווח הקצר."
    )

    # אם אין מפתח, נחזיר טקסט סטטי (ללא AI חיצוני)
    if settings.AI_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        try:
            payload = {
                "model": "gpt-4.1-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": "אתה עוזר מסחר שמסביר ניתוח טכני בעברית קצרה וברורה.",
                    },
                    {
                        "role": "user",
                        "content": base_text + "\n\nסכם את המצב ב-3 Bullet points קצרים.",
                    },
                ],
                "max_tokens": 200,
            }
            headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
                r.raise_for_status()
                data = r.json()
                return data["choices"][0]["message"]["content"]
        except Exception:
            return base_text

    return base_text
