"""External API clients with timeout and fallback-first behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from modules.config import get_secret

MOCK_COORDINATES = {
    "default_origin": {"lat": 37.615, "lon": 126.715, "label": "김포시 mock 출발지"},
    "default_destination": {"lat": 37.638, "lon": 126.682, "label": "김포반다비체육센터 mock 목적지"},
}


@dataclass(frozen=True)
class ApiResult:
    ok: bool
    data: Any = None
    data_status: str = "missing"
    error: str = ""
    reason: str = ""


def safe_get_json(
    url: str,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    timeout: int = 5,
) -> ApiResult:
    try:
        response = requests.get(url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()
        return ApiResult(ok=True, data=response.json(), data_status="real_api")
    except Exception as exc:
        return ApiResult(ok=False, data=None, data_status="mock_fallback", error=str(exc), reason="request_failed")


def geocode_vworld(address: str) -> tuple[dict[str, Any] | None, dict[str, str]]:
    api_key = get_secret("VWORLD_API_KEY")
    if not api_key:
        return None, {"data_status": "missing", "reason": "VWORLD_API_KEY not configured"}

    if not address or not address.strip():
        return None, {"data_status": "missing", "reason": "address is empty"}

    params = {
        "service": "address",
        "request": "getcoord",
        "format": "json",
        "crs": "epsg:4326",
        "type": "road",
        "address": address,
        "key": api_key,
    }

    result = safe_get_json("https://api.vworld.kr/req/address", params=params, timeout=5)
    if not result.ok:
        return None, {"data_status": result.data_status, "reason": result.error or result.reason}

    try:
        point = result.data["response"]["result"]["point"]
        return (
            {"x": point.get("x"), "y": point.get("y"), "raw": result.data},
            {"data_status": "real_api", "reason": ""},
        )
    except Exception as exc:
        return None, {"data_status": "mock_fallback", "reason": f"unexpected_response: {exc}"}


def mock_coordinate(kind: str = "default_origin") -> dict[str, Any]:
    return dict(MOCK_COORDINATES.get(kind, MOCK_COORDINATES["default_origin"]))


def fetch_weather_stub() -> dict[str, Any]:
    return {
        "data_status": "mock_fallback",
        "source": "weather_stub",
        "message": "날씨 API는 아직 연결하지 않았습니다.",
        "items": [],
    }


def fetch_bus_stub() -> dict[str, Any]:
    return {
        "data_status": "mock_fallback",
        "source": "bus_stub",
        "message": "버스 API는 아직 연결하지 않았습니다.",
        "items": [],
    }


def fetch_public_facility_stub() -> dict[str, Any]:
    return {
        "data_status": "mock_fallback",
        "source": "public_facility_stub",
        "message": "공공시설 API는 아직 연결하지 않았습니다.",
        "items": [],
    }
