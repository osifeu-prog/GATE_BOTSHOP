# GATE BOTSHOP AI

FastAPI + Telegram bot gateway for trading simulation and future on-chain trading (TON / DEX).

Generated at 2025-12-05T20:14:22.350682 UTC.

## Running locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt

export BOT_TOKEN="..."
export WEBHOOK_URL="https://your-ngrok-or-railway-url"
export DATABASE_URL="postgresql+asyncpg://user:pass@host:port/dbname"

uvicorn app.main:app --reload
```

Health check:
- `GET /health`

Telegram webhook (Railway):
- `WEBHOOK_URL` must be your public base URL, e.g. `https://gatebotshop-production.up.railway.app`
- The app config will set the webhook to `/webhook/telegram` automatically.


📌 "אני ממשיך מ-GATE BOTSHOP. הדאטאבייס כבר סונכרן (human_score תוקן). אני רוצה שנמשיך לפתח את המערכת: סטייקינג אמיתי, מסכי Wallet, AI Trade Assistant, חיבור BSC/TON און-צ'יין, ודשבורד אדמין מלא. תדריך אותי מה השלב הבא."

או אם תרצה פשוט:

📌 "המשך מפה: GATE BOTSHOP רץ, ה-DB תוקן. בוא נמשיך לבנות את הפיצ’רים המלאים."
🎁 מה אתה יכול לעשות בשיחה הבאה

בדיוק מפה אפשר:

✔ לבנות staking מלא עם APR משתנה
✔ לחבר NFT / TON / BSC wallets
✔ להוסיף AI במסכי הסבר עסקה
✔ לבנות /portfolio שמחזיר גרף תשואות
✔ לייצר Admin Dashboard עם PDF / CSV
✔ לייצר מערכת earnings מלאה
✔ לעשות Real-Time on-chain deposits
✔ לבנות מערכת referral חדשה עם QR

כל זה על בסיס המנוע שכבר בנינו.

אם תרצה – אפשר גם להתחיל ליצור ALEMBIC Migrations כדי שכל שינוי DB יקרה אוטומטית בלי SQL ידני.
