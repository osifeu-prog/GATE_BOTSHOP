# GATE BOTSHOP – AI Trading Gateway (V2, עם OpenAI/HuggingFace)

פרויקט משודרג ל-GATE_BOTSHOP שמוסיף:

- שרת FastAPI מודרני
- בוט טלגרם עם python-telegram-bot v21 (Webhook)
- התראות מסחר למטבעות BTC / ETH / BNB / SOL / XRP / TON
- ניתוח טכני בסיסי (MA קצר/ארוך, תנודתיות)
- הסברים מבוססי AI (OpenAI או HuggingFace) על כל איתות
- השוואת מחירי פיוצ'רז בין Binance / Bybit / OKX (אם זמינים)

> ⚠ חשוב: המערכת היא כלי לימודי בלבד. אין לראות באיתותים ובהסברים ייעוץ השקעות.

## מבנה תיקיות

```text
.
├─ app/
│  ├─ __init__.py
│  ├─ main.py              # נקודת הכניסה של FastAPI + Webhook לטלגרם
│  ├─ config.py            # קונפיג והגדרות מה-ENV (כולל מפתחות AI)
│  ├─ schemas.py           # מודלים לוגיים (TradeSignal, ExchangeQuote)
│  ├─ services/
│  │  ├─ market_data.py        # משיכת נתוני שוק (Binance)
│  │  ├─ signal_engine.py      # יצירת אותות מסחר
│  │  ├─ ai_explainer.py       # הסבר טקסטואלי (OpenAI/HF או fallback)
│  │  └─ exchange_routing.py   # השוואת מחירים בין בורסות
│  └─ telegram_bot/
│     ├─ __init__.py
│     └─ handlers.py           # פקודות /start /help /signal /compare
├─ Procfile
├─ runtime.txt
├─ requirements.txt
└─ README.md
```

## הגדרת קובץ .env (חשוב מאוד)

צור קובץ `.env` בשורש הפרויקט (ליד `requirements.txt`) עם לפחות:

```env
# חובה
BOT_TOKEN=הטוקן_מהBotFather
WEBHOOK_URL=https://your-railway-app.up.railway.app
LOG_LEVEL=INFO

# בחירת ספק AI: openai / huggingface / none
AI_PROVIDER=openai

# === OpenAI (אם משתמשים ב-openai) ===
# קח מפה: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-...

# דגם, ניתן להשאיר ברירת מחדל:
OPENAI_MODEL=gpt-4o-mini

# === Hugging Face (אם משתמשים ב-huggingface) ===
# קח מפה: https://huggingface.co/settings/tokens/new?tokenType=fineGrained
HF_TOKEN=hf_...
# מודל ברירת מחדל (אפשר לשנות למודל אחר שתגדיר לעצמך):
HF_MODEL=mistralai/Mixtral-8x7B-Instruct-v0.1
# אופציונלי: אם יש לך Endpoint מנוהל משלך:
# HF_API_URL=https://api-inference.huggingface.co/models/your/model
```

### מאיפה משיגים את המפתחות?

#### 1. מפתח OpenAI (OPENAI_API_KEY)

1. היכנס: https://platform.openai.com/api-keys
2. לחץ על **Create new secret key**.
3. בחר שם מפתח (למשל: `gate-botshop-trading`).
4. העתק את ה-Key המלא (מתחיל ב-`sk-...`).
5. הדבק אותו בקובץ `.env` כערך של `OPENAI_API_KEY`.

> לעולם אל תכניס את המפתח לתוך הקוד עצמו או לגיטהאב – רק כ-ENV משתנה.

#### 2. טוקן HuggingFace (HF_TOKEN)

1. היכנס: https://huggingface.co/settings/tokens/new?tokenType=fineGrained
2. בחר Token מסוג **Fine-grained** עם הרשאת `Read` ל-Inference.
3. תן שם (למשל: `gate-botshop-ai`).
4. צור והעתק את הטוקן (מתחיל ב-`hf_...`).
5. הדבק בקובץ `.env` כערך של `HF_TOKEN` (אם תשתמש ב-HF).

> גם כאן – הטוקן נשאר רק ב-ENV או ב-Secret של השרת, ולא נכנס לקוד או לגיט.

## הרצה מקומית

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

וודא שקובץ `.env` מוגדר נכון.


## פריסה ל-Railway (או פלטפורמה דומה)

1. דחוף את הפרויקט לגיטהאב (לדוגמה לריפו `GATE_BOTSHOP_AI`).
2. חבר את הריפו ל-Railway.
3. ב-Railway, תחת Settings → Variables, הגדר את אותם משתנים כמו ב-`.env`:
   - BOT_TOKEN
   - WEBHOOK_URL
   - LOG_LEVEL
   - AI_PROVIDER
   - OPENAI_API_KEY / HF_TOKEN (לפי מה שאתה משתמש)
   - OPENAI_MODEL / HF_MODEL (אם תרצה להחליף)

4. ודא שה-Command הוא (משתמש ב-Procfile):
   - `uvicorn app.main:app --host 0.0.0.0 --port 8080`

5. לאחר דיפלוי מוצלח, בדוק:
   - `/health` – אמור להחזיר JSON עם `status: "ok"`.
   - לשלוח `/start` לבוט בטלגרם.
   - לנסות `/signal BTCUSDT 15m` ולראות הסבר מה-AI.

## שימוש בבוט

- `/start` – הסבר כללי על הבוט.
- `/help` – הצגת אפשרויות ופקודות.
- `/signal <symbol> <timeframe>` – ניתוח עסקה (למשל: `/signal BTCUSDT 15m`).
- `/compare <symbol>` – השוואת מחירי פיוצ'רז בין בורסות.

## הערות בטיחות

- מסחר בפיוצ'רז קריפטו הוא בעל סיכון גבוה מאוד, כולל אפשרות להפסד מלא של ההשקעה.
- המערכת הזו היא כלי למידה בלבד. אתה אחראי בלעדית לכל החלטת מסחר.
- מומלץ תמיד להתחיל בסכומים קטנים, בלי מינוף קיצוני, ורק אחרי הבנה מלאה של הסיכון.
