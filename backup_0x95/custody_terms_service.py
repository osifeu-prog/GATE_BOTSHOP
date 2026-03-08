import os
from datetime import datetime

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User
from app.models.audit_logs import AuditLog

TERMS_PATH = "docs/custody_terms.pdf"
TERMS_URL = "/static/custody_terms.pdf"  # ×‘×¢×ھ×™×“ ×گ×¤×©×¨ ×œ×©×¨×ھ ×“×¨×ڑ FastAPI


def generate_pdf_terms() -> None:
    """
    ×‍×™×™×¦×¨ ×‍×،×‍×ڑ ×ھ× ×گ×™ Custody ×‘×،×™×،×™ ×‘×¤×•×¨×‍×ک PDF (×œ×¦×•×¨×ڑ MVP).
    """
    os.makedirs("docs", exist_ok=True)
    c = canvas.Canvas(TERMS_PATH, pagesize=A4)
    text = c.beginText(40, 800)
    text.setFont("Helvetica", 12)

    content = [
        "GATE BOTSHOP  Custodial Agreement",
        "",
        "1. ×›×،×¤×™×‌ ×”×‍×•×¤×§×“×™×‌ ×œ×›×ھ×•×‘×ھ ×”-TON ×”×¨×گ×©×™×ھ ×‍×•×—×–×§×™×‌ ×‘×‍×•×“×œ Custodial.",
        "2. ×”×‍×¤×¢×™×œ ×‍× ×”×œ ×‍×گ×–×ں ×¤× ×™×‍×™ ×•×¤×¢×™×œ×•×ھ ×‘×œ×•×§×¦'×™×™×ں ×‘×”×ھ×گ×‌ ×œ×ھ× ×گ×™×‌.",
        "3. ×”×‍×©×ھ×‍×© × ×•×ھ×¨ ×”× ×”× ×” ×”×›×œ×›×œ×™ ×‘×”×ھ×گ×‌ ×œ×”×،×›×‍×•×ھ ×”×—×•×–×™×•×ھ.",
        "",
        "×‍×،×‍×ڑ ×–×” ×”×™× ×• ×‘×،×™×، ×œ-MVP ×•×ک×¢×•×ں ×”×©×œ×‍×”/×¢×“×›×•×ں ×‍×©×¤×ک×™ ×—×™×¦×•× ×™.",
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

