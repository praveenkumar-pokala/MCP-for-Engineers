"""Currency conversion client using a real, free API (exchangerate.host).

This module again reflects the *API world*:
- You must know the endpoint and query parameters.
- You must interpret the JSON payloads on your own.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import requests


BASE_URL = "https://api.exchangerate.host/convert"


class CurrencyAPIError(RuntimeError):
    """Raised when the FX API call fails."""


@dataclass
class CurrencyConversionResult:
    from_currency: str
    to_currency: str
    amount: float
    converted_amount: float
    rate: float


def convert_currency(amount: float, from_currency: str, to_currency: str) -> CurrencyConversionResult:
    """Convert an amount from one currency to another using exchangerate.host.

    API docs: https://exchangerate.host/#/#docs
    """
    params = {
        "from": from_currency.upper(),
        "to": to_currency.upper(),
        "amount": amount,
    }

    try:
        resp = requests.get(BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        raise CurrencyAPIError(f"Currency API request failed: {exc}") from exc

    data = resp.json()
    if not data.get("success", True):
        raise CurrencyAPIError(f"Currency API reported failure: {data!r}")

    result = float(data.get("result", 0.0))
    rate = float(data.get("info", {}).get("rate", 0.0))

    return CurrencyConversionResult(
        from_currency=from_currency.upper(),
        to_currency=to_currency.upper(),
        amount=amount,
        converted_amount=result,
        rate=rate,
    )
