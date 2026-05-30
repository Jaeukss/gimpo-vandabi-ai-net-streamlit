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


def _classify_request_error(exc: Exception) -> str:
    name = exc.__class__.__name__.lower()
    if isinstance(exc, requests.Timeout):
        return "timeout"
    if isinstance(exc, requests.ConnectionError):
        return "network_error"
    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)
    if status_code in (401, 403):
        return "unauthorized"
    if status_code == 429:
        return "rate_limit"
    if status_code:
        return f"http_{status_code}"
    if "json" in name:
        return "invalid_json"
    return "request_error"


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
        return ApiResult(ok=False, data=None, data_status="mock_fallback", error="", reason=_classify_request_error(exc))


def vworld_status() -> dict[str, str | bool]:
    configured = get_secret("VWORLD_API_KEY") not in (None, "")
    return {
        "configured": configured,
        "data_status": "configured" if configured else "missing",
        "message": "VWorld API Key 설정 상태만 확인합니다.",
    }


def data_go_kr_status() -> dict[str, str | bool]:
    configured = get_secret("DATA_GO_KR_SERVICE_KEY") not in (None, "")
    return {
        "configured": configured,
        "data_status": "configured" if configured else "missing",
        "message": "DATA_GO_KR_SERVICE_KEY는 8단계에서 설정 상태만 확인하며 실제 endpoint 호출은 9단계 대상입니다.",
    }


def geocode_vworld(address: str) -> tuple[dict[str, Any] | None, dict[str, str]]:
    if not address or not address.strip():
        return None, {"data_status": "missing_input", "reason": "missing_input"}

    api_key = get_secret("VWORLD_API_KEY")
    if not api_key:
        return None, {"data_status": "mock_fallback", "reason": "missing_key"}

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
        return None, {"data_status": result.data_status, "reason": result.reason or "request_failed"}

    try:
        response = result.data.get("response", {})
        status = response.get("status", "")
        if str(status).upper() not in {"OK", "SUCCESS"}:
            return None, {"data_status": "mock_fallback", "reason": "not_found_or_invalid_response"}
        point = response["result"]["point"]
        return (
            {"x": point.get("x"), "y": point.get("y"), "raw": result.data},
            {"data_status": "real_api", "reason": ""},
        )
    except Exception:
        return None, {"data_status": "mock_fallback", "reason": "invalid_response"}


def test_vworld_geocode_connection(address: str = "김포반다비체육센터") -> dict[str, Any]:
    """User-triggered smoke test. It never returns the API key."""
    geocode, meta = geocode_vworld(address)
    return {
        "ok": geocode is not None,
        "status": meta.get("data_status", "mock_fallback"),
        "reason": meta.get("reason", ""),
        "has_coordinate": geocode is not None,
    }


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
