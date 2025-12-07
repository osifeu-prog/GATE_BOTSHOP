from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger("gate_botshop_ai.dex")

STONFI_API_URL = "https://api.ston.fi"
DEDUST_API_URL = "https://api.dedust.io"


async def get_stonfi_quote(
    from_symbol: str,
    to_symbol: str,
    amount: Decimal,
) -> Optional[Decimal]:
    try:
        params = {
            "from": from_symbol,
            "to": to_symbol,
            "amount": str(amount),
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{STONFI_API_URL}/v1/swap/simulate", params=params)
        resp.raise_for_status()
        data: Dict[str, Any] = resp.json()
        out_amount = data.get("to_amount") or data.get("out_amount")
        if out_amount is None:
            return None
        return Decimal(str(out_amount))
    except Exception as exc:
        logger.warning("STON.fi quote failed: %s", exc)
        return None
