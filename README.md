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
