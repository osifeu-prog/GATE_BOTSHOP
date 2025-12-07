import os
from datetime import datetime

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User
from app.models.audit_logs import AuditLog

TERMS_PATH = "docs/custody_terms.pdf"
TERMS_URL = "/static/custody_terms.pdf"  # בעתיד אפשר לשרת דרך FastAPI


def generate_pdf_terms() -> None:
    """
    מייצר מסמך תנאי Custody בסיסי בפורמט PDF (לצורך MVP).
    """
    os.makedirs("docs", exist_ok=True)
    c = canvas.Canvas(TERMS_PATH, pagesize=A4)
    text = c.beginText(40, 800)
    text.setFont("Helvetica", 12)

    content = [
        "GATE BOTSHOP  Custodial Agreement",
        "",
        "1. כספים המופקדים לכתובת ה-TON הראשית מוחזקים במודל Custodial.",
        "2. המפעיל מנהל מאזן פנימי ופעילות בלוקצ'יין בהתאם לתנאים.",
        "3. המשתמש נותר הנהנה הכלכלי בהתאם להסכמות החוזיות.",
        "",
        "מסמך זה הינו בסיס ל-MVP וטעון השלמה/עדכון משפטי חיצוני.",
        "",
        f"Generated at: {datetime.utcnow().isoformat()}",
    ]

    for line in content:
        text.textLine(line)

    c.drawText(text)
    c.showPage()
    c.save()


async def audit_log(
    session: AsyncSession,
    user_id: int | None,
    event: str,
    details: str | None = None,
    amount: float | None = None,
) -> None:
    log = AuditLog(
        user_id=user_id,
        action=event,
        details=details,
        amount=amount,
    )
    session.add(log)
    await session.commit()


async def register_user_agreement(session: AsyncSession, user_id: int) -> None:
    user = await session.get(User, user_id)
    if user:
        user.custody_agreed = True
        await session.commit()
