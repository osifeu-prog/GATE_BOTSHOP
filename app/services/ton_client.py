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
    """Return TON balance from TON API. If misconfigured, fall back to 0."""
    endpoint, api_key = _get_endpoint_and_key(network)
    if not endpoint:
        return Decimal("0")

    try:
        params: dict[str, str] = {"address": address}
        if api_key:
            params["api_key"] = api_key

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{endpoint.rstrip('/')}/getAddressInformation", params=params)
            resp.raise_for_status()
            data = resp.json()

        result = data.get("result") or {}
        raw_balance = result.get("balance")
        if raw_balance is None:
            return Decimal("0")
        return Decimal(raw_balance) / Decimal(10**9)
    except Exception:
        return Decimal("0")
