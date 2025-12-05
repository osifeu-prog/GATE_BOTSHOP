from __future__ import annotations

from decimal import Decimal
from typing import Literal, Optional

import httpx

from ..config import settings


TonNetwork = Literal["mainnet", "testnet"]


def _get_endpoint_and_key(network: TonNetwork) -> tuple[Optional[str], Optional[str]]:
    if network == "mainnet":
        return settings.TON_MAINNET_ENDPOINT, settings.TON_MAINNET_API_KEY
    return settings.TON_TESTNET_ENDPOINT, settings.TON_TESTNET_API_KEY


async def get_account_balance_ton(address: str, network: TonNetwork) -> Decimal:
    """
    מחזיר Balance ב-TON כ-Decimal.

    אם אין endpoint/KEY מוגדרים, או שיש בעיית רשת – נחזיר 0 ולא נקריס את השרת.
    כאן אפשר לחבר אחר כך TONCENTER / TONAPI / ספק אחר.
    """
    endpoint, api_key = _get_endpoint_and_key(network)
    if not endpoint:
        # אין endpoint מוגדר – placeholder עד שנגדיר
        return Decimal("0")

    try:
        # דוגמה עבור TONCENTER (אפשר להתאים ל-API אחר שתבחר)
        params = {"address": address}
        if api_key:
            params["api_key"] = api_key

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{endpoint.rstrip('/')}/getAddressInformation", params=params)
            resp.raise_for_status()
            data = resp.json()

        # פורמט לדוגמה: {"ok":true,"result":{"balance":"1234567890", ...}}
        result = data.get("result") or {}
        raw_balance = result.get("balance")
        if raw_balance is None:
            return Decimal("0")

        # NANOTON -> TON
        return Decimal(raw_balance) / Decimal(10**9)
    except Exception:
        # לא מפילים כלום – רק מחזירים 0
        return Decimal("0")
