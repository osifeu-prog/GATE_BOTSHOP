from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional

import httpx

from ..config import settings

logger = logging.getLogger("gate_botshop_ai.ton_client")

TONNetwork = Literal["mainnet", "testnet"]


def _get_base_url(network: TONNetwork) -> str:
    if network == "testnet":
        return settings.TON_TESTNET_API_ENDPOINT or "https://testnet.toncenter.com/api/v2"
    return settings.TON_MAINNET_API_ENDPOINT or "https://toncenter.com/api/v2"


def _get_api_key(network: TONNetwork) -> Optional[str]:
    if network == "testnet":
        return settings.TON_TESTNET_API_KEY
    return settings.TON_MAINNET_API_KEY


async def _request(
    network: TONNetwork,
    method: str,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    base_url = _get_base_url(network)
    api_key = _get_api_key(network)

    query = dict(params)
    if api_key:
        query["api_key"] = api_key

    url = f"{base_url}/{method}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=query)

    resp.raise_for_status()
    data = resp.json()

    if not data.get("ok", False):
        raise RuntimeError(f"TON API error: {data.get('error')}")

    return data["result"]


async def get_address_balance(network: TONNetwork, address: str) -> Decimal:
    result = await _request(
        network,
        "getAddressBalance",
        {"address": address},
    )
    nano = Decimal(result)
    return nano / Decimal("1_000_000_000")


async def get_recent_transactions(
    network: TONNetwork,
    address: str,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    result = await _request(
        network,
        "getTransactions",
        {"address": address, "limit": limit},
    )
    if isinstance(result, list):
        return result
    return []


async def get_treasury_balances() -> Dict[str, Optional[Decimal]]:
    if not settings.TON_TREASURY_ADDRESS:
        return {"testnet": None, "mainnet": None}

    address = settings.TON_TREASURY_ADDRESS
    balances: Dict[str, Optional[Decimal]] = {"testnet": None, "mainnet": None}

    try:
        balances["testnet"] = await get_address_balance("testnet", address)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to fetch testnet TON balance: %s", exc)

    try:
        balances["mainnet"] = await get_address_balance("mainnet", address)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to fetch mainnet TON balance: %s", exc)

    return balances


async def get_ton_price_usd() -> Decimal:
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "the-open-network", "vs_currencies": "usd"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        price = data.get("the-open-network", {}).get("usd")
        if price is None:
            raise RuntimeError("Missing TON price")
        return Decimal(str(price))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to fetch TON price from CoinGecko: %s", exc)
        return Decimal("2")
