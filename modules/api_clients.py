"""External API clients with timeout and fallback-first behavior."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from xml.etree import ElementTree as ET

import requests

from modules.config import get_secret
from modules.safety import sanitize_public_claims

SPORTS_FACILITY_URL = "https://apis.data.go.kr/B551014/SRVC_API_SFMS_FACI"
SPORTS_FACILITY_DETAIL_URL = "https://apis.data.go.kr/B551014/SRVC_SFMS_FACIL_INFO"
DISABLED_CONVENIENCE_URL = "https://apis.data.go.kr/B554287/DisabledPersonConvenientFacility"
MOBILITY_SUPPORT_URL = "https://apis.data.go.kr/B551982/tsdo_v2"
WEATHER_URL = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0"
BUS_ARRIVAL_URL = "https://apis.data.go.kr/1613000/ArvlInfoInqireService"
BUS_ROUTE_URL = "https://apis.data.go.kr/1613000/BusRouteInfoInqireService"

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
        return "parse_error"
    return "api_error"


def _status_message(status: str) -> str:
    messages = {
        "real_api": "공공데이터 API 응답을 사용했습니다.",
        "missing_key": "DATA_GO_KR_SERVICE_KEY가 없어 fallback 데이터를 사용합니다.",
        "missing_params": "필수 파라미터가 부족해 fallback 데이터를 사용합니다.",
        "api_error": "API 응답 상태가 정상으로 확인되지 않아 fallback 데이터를 사용합니다.",
        "timeout": "API timeout으로 fallback 데이터를 사용합니다.",
        "network_error": "네트워크 오류로 fallback 데이터를 사용합니다.",
        "parse_error": "응답 파싱 실패로 fallback 데이터를 사용합니다.",
        "fallback": "fallback 데이터를 사용합니다.",
    }
    return messages.get(status, "fallback 데이터를 사용합니다.")


def _clean_item(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _clean_item(v) for k, v in value.items() if str(k).lower() not in {"servicekey", "apikey", "key"}}
    if isinstance(value, list):
        return [_clean_item(item) for item in value]
    return sanitize_public_claims(str(value)) if isinstance(value, str) else value


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
    configured = get_data_go_kr_key() not in (None, "")
    return {
        "configured": configured,
        "data_status": "configured" if configured else "missing",
        "message": "DATA_GO_KR_SERVICE_KEY 설정 상태만 확인합니다.",
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


def get_data_go_kr_key() -> str | None:
    key = get_secret("DATA_GO_KR_SERVICE_KEY")
    return str(key) if key not in (None, "") else None


def build_public_data_params(params: dict[str, Any] | None = None, json: bool = True) -> dict[str, Any]:
    built: dict[str, Any] = {}
    if params:
        built.update({key: value for key, value in params.items() if value not in (None, "")})
    built.setdefault("pageNo", 1)
    built.setdefault("numOfRows", 10)
    if json:
        built.setdefault("_type", "json")
        built.setdefault("type", "json")
    service_key = get_data_go_kr_key()
    if service_key:
        built["serviceKey"] = service_key
    return built


def classify_public_data_error(error_or_response: Any) -> str:
    if isinstance(error_or_response, Exception):
        return _classify_request_error(error_or_response)
    if isinstance(error_or_response, requests.Response):
        status_code = error_or_response.status_code
        if status_code in (401, 403):
            return "unauthorized"
        if status_code == 429:
            return "rate_limit"
        if status_code >= 500:
            return "api_error"
        if status_code >= 400:
            return f"http_{status_code}"
    return "api_error"


def _find_first_key(data: Any, keys: set[str]) -> Any:
    if isinstance(data, dict):
        for key, value in data.items():
            if str(key).lower() in keys:
                return value
        for value in data.values():
            found = _find_first_key(value, keys)
            if found is not None:
                return found
    elif isinstance(data, list):
        for item in data:
            found = _find_first_key(item, keys)
            if found is not None:
                return found
    return None


def _collect_items(data: Any) -> list[Any]:
    if isinstance(data, dict):
        for key, value in data.items():
            if str(key).lower() == "item":
                if isinstance(value, list):
                    return value
                return [value]
        for key, value in data.items():
            if str(key).lower() in {"items", "body", "response", "data"}:
                collected = _collect_items(value)
                if collected:
                    return collected
        return []
    if isinstance(data, list):
        return data
    return []


def _xml_element_to_obj(element: ET.Element) -> Any:
    children = list(element)
    if not children:
        return element.text.strip() if element.text else ""

    result: dict[str, Any] = {}
    for child in children:
        child_obj = _xml_element_to_obj(child)
        key = child.tag.split("}")[-1]
        if key in result:
            if not isinstance(result[key], list):
                result[key] = [result[key]]
            result[key].append(child_obj)
        else:
            result[key] = child_obj
    return result


def normalize_public_data_response(raw: Any, service_name: str = "") -> dict[str, Any]:
    try:
        parsed = _xml_element_to_obj(raw) if isinstance(raw, ET.Element) else raw
        result_code = _find_first_key(parsed, {"resultcode", "code", "returncode"})
        result_msg = _find_first_key(parsed, {"resultmsg", "message", "returnmsg", "errmsg"})
        total_count = _find_first_key(parsed, {"totalcount", "total_count", "count"})
        items = [_clean_item(item) for item in _collect_items(parsed)]
        code_text = str(result_code).upper() if result_code is not None else ""
        ok_codes = {"", "0", "00", "OK", "SUCCESS", "NORMAL_SERVICE", "INFO-000"}
        ok = code_text in ok_codes or bool(items)
        return {
            "ok": ok,
            "service_name": service_name,
            "result_code": code_text,
            "message": sanitize_public_claims(str(result_msg or "")),
            "items": items,
            "total_count": total_count,
        }
    except Exception:
        return {"ok": False, "service_name": service_name, "result_code": "parse_error", "message": "parse_error", "items": [], "total_count": 0}


def extract_public_data_items(normalized: dict[str, Any]) -> list[Any]:
    items = normalized.get("items", [])
    return items if isinstance(items, list) else []


def make_api_result(
    service_name: str,
    status: str,
    data: Any = None,
    message: str = "",
    source: str = "public_data",
    endpoint_name: str = "",
) -> dict[str, Any]:
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        items = data["items"]
    elif isinstance(data, list):
        items = data
    elif data is None:
        items = []
    else:
        items = [data]

    cleaned_items = [_clean_item(item) for item in items]
    return {
        "service_name": sanitize_public_claims(service_name),
        "status": status,
        "data_status": status,
        "data": _clean_item(data) if data is not None else None,
        "items": cleaned_items,
        "message": sanitize_public_claims(message or _status_message(status)),
        "source": source,
        "endpoint_name": endpoint_name,
        "count": len(cleaned_items),
    }


def call_data_go_kr_api(
    endpoint: str,
    params: dict[str, Any] | None = None,
    service_name: str = "",
    timeout: int = 8,
    prefer_json: bool = True,
) -> dict[str, Any]:
    if not get_data_go_kr_key():
        return make_api_result(service_name, "missing_key", source="fallback", endpoint_name=service_name)

    request_params = build_public_data_params(params, json=prefer_json)
    try:
        response = requests.get(endpoint, params=request_params, timeout=timeout)
        if response.status_code >= 400:
            return make_api_result(service_name, classify_public_data_error(response), source="fallback", endpoint_name=service_name)

        raw: Any
        try:
            raw = response.json()
        except Exception:
            try:
                raw = ET.fromstring(response.content)
            except Exception:
                return make_api_result(service_name, "parse_error", source="fallback", endpoint_name=service_name)

        normalized = normalize_public_data_response(raw, service_name)
        items = extract_public_data_items(normalized)
        if not normalized.get("ok"):
            return make_api_result(
                service_name,
                "api_error",
                data={"items": []},
                message=str(normalized.get("message") or "api_error"),
                source="fallback",
                endpoint_name=service_name,
            )
        return make_api_result(
            service_name,
            "real_api",
            data={"items": items, "total_count": normalized.get("total_count")},
            message=str(normalized.get("message") or "real_api"),
            source="public_data",
            endpoint_name=service_name,
        )
    except Exception as exc:
        return make_api_result(service_name, classify_public_data_error(exc), source="fallback", endpoint_name=service_name)


def _keyword_filter(items: list[Any], keywords: tuple[str, ...]) -> list[Any]:
    if not keywords:
        return items
    filtered: list[Any] = []
    for item in items:
        text = str(item)
        if any(keyword and keyword in text for keyword in keywords):
            filtered.append(item)
    return filtered


def _with_fallback(result: dict[str, Any], fallback_items: list[dict[str, Any]], fallback_message: str) -> dict[str, Any]:
    if result["status"] == "real_api":
        return result
    return make_api_result(
        result["service_name"],
        result["status"],
        data=fallback_items,
        message=f"{result['message']} {fallback_message}",
        source="fallback",
        endpoint_name=result["endpoint_name"],
    )


def _sports_facility_fallback() -> list[dict[str, Any]]:
    return [
        {
            "facility_name": "김포반다비체육센터",
            "area": "김포",
            "data_type": "prototype_dummy",
            "note": "실제 API 실패 시 표시되는 생활체육 시설 참고 샘플",
        }
    ]


def _disabled_convenience_fallback() -> list[dict[str, Any]]:
    return [
        {
            "facility_name": "김포 접근성 편의시설 참고 샘플",
            "area": "김포",
            "data_type": "prototype_dummy",
            "note": "장애인 편의시설 현황 API 실패 시 표시되는 샘플",
        }
    ]


def _mobility_support_fallback() -> list[dict[str, Any]]:
    return [
        {
            "area": "김포",
            "candidate": "이동지원 후보 추천",
            "review": "운영기관 검토 필요",
            "availability": "이용 가능 여부 확인 필요",
            "data_type": "prototype_dummy",
        }
    ]


def _weather_fallback() -> list[dict[str, Any]]:
    return [
        {
            "category": "weather_summary",
            "summary": "기상 API fallback: 현장 상태와 최신 예보 확인 필요",
            "route_impact": "주의",
            "data_type": "prototype_dummy",
        }
    ]


def _bus_arrival_fallback() -> list[dict[str, Any]]:
    return [{"service": "TAGO 버스도착정보", "status": "missing_params_or_fallback", "data_type": "prototype_dummy"}]


def _bus_route_fallback() -> list[dict[str, Any]]:
    return [{"service": "TAGO 버스노선정보", "status": "missing_params_or_fallback", "data_type": "prototype_dummy"}]


def fetch_sports_facilities(keyword: str = "김포", page_no: int = 1, num_of_rows: int = 10) -> dict[str, Any]:
    service_name = "전국체육시설 정보"
    params = {"pageNo": page_no, "numOfRows": num_of_rows, "keyword": keyword, "faciNm": keyword, "fcltyNm": keyword}
    result = call_data_go_kr_api(SPORTS_FACILITY_URL, params=params, service_name=service_name, timeout=8)
    if result["status"] == "real_api" and keyword:
        filtered = _keyword_filter(result["items"], (keyword, "김포", "반다비"))
        if filtered:
            result = make_api_result(service_name, "real_api", data=filtered, message=result["message"], source="public_data", endpoint_name=service_name)
    return _with_fallback(result, _sports_facility_fallback(), "전국체육시설 정보 fallback을 표시합니다.")


def fetch_sports_facility_detail(facility_id: str | None = None, facility_name: str = "김포반다비체육센터") -> dict[str, Any]:
    service_name = "공공체육시설 상세 정보"
    params = {"pageNo": 1, "numOfRows": 10}
    if facility_id:
        params.update({"facilityId": facility_id, "faciId": facility_id, "fcltyId": facility_id})
    elif facility_name:
        params.update({"facilityName": facility_name, "faciNm": facility_name, "fcltyNm": facility_name, "keyword": facility_name})
    else:
        return make_api_result(service_name, "missing_params", data=_sports_facility_fallback(), source="fallback", endpoint_name=service_name)
    result = call_data_go_kr_api(SPORTS_FACILITY_DETAIL_URL, params=params, service_name=service_name, timeout=8)
    return _with_fallback(result, _sports_facility_fallback(), "공공체육시설 상세 정보 fallback을 표시합니다.")


def fetch_disabled_convenience_facilities(keyword: str = "김포", page_no: int = 1, num_of_rows: int = 10) -> dict[str, Any]:
    service_name = "장애인편의시설 현황"
    params = {"pageNo": page_no, "numOfRows": num_of_rows, "keyword": keyword, "facilityNm": keyword, "signguNm": keyword}
    result = call_data_go_kr_api(DISABLED_CONVENIENCE_URL, params=params, service_name=service_name, timeout=8, prefer_json=True)
    if result["status"] == "real_api" and keyword:
        filtered = _keyword_filter(result["items"], (keyword, "반다비"))
        if filtered:
            result = make_api_result(service_name, "real_api", data=filtered, message=result["message"], source="public_data", endpoint_name=service_name)
    return _with_fallback(result, _disabled_convenience_fallback(), "장애인편의시설 현황 fallback을 표시합니다.")


def fetch_mobility_support_realtime(area: str = "김포", page_no: int = 1, num_of_rows: int = 10) -> dict[str, Any]:
    service_name = "교통약자 이동지원 실시간 정보"
    params = {"pageNo": page_no, "numOfRows": num_of_rows, "area": area, "areaNm": area, "sido": "경기", "sgg": area}
    result = call_data_go_kr_api(MOBILITY_SUPPORT_URL, params=params, service_name=service_name, timeout=8)
    if result["status"] == "real_api" and area:
        filtered = _keyword_filter(result["items"], (area, "김포"))
        if filtered:
            result = make_api_result(service_name, "real_api", data=filtered, message=result["message"], source="public_data", endpoint_name=service_name)
    return _with_fallback(result, _mobility_support_fallback(), "이동지원 후보 추천 fallback을 표시합니다.")


def _safe_weather_base_time(now: datetime | None = None) -> tuple[str, str]:
    target = (now or datetime.now()) - timedelta(minutes=45)
    base_times = ["0200", "0500", "0800", "1100", "1400", "1700", "2000", "2300"]
    current = target.strftime("%H%M")
    selected = None
    for base in base_times:
        if current >= base:
            selected = base
    if selected is None:
        target = target - timedelta(days=1)
        selected = "2300"
    return target.strftime("%Y%m%d"), selected


def fetch_weather_short_forecast(nx: int = 55, ny: int = 128, base_date: str | None = None, base_time: str | None = None) -> dict[str, Any]:
    service_name = "기상청 단기예보"
    safe_date, safe_time = _safe_weather_base_time()
    params = {
        "pageNo": 1,
        "numOfRows": 50,
        "dataType": "JSON",
        "base_date": base_date or safe_date,
        "base_time": base_time or safe_time,
        "nx": nx,
        "ny": ny,
    }
    result = call_data_go_kr_api(f"{WEATHER_URL}/getVilageFcst", params=params, service_name=service_name, timeout=8)
    if result["status"] == "real_api":
        summary = summarize_weather_items(result["items"])
        result["summary"] = summary
        result["message"] = sanitize_public_claims(summary)
        return result
    fallback = _with_fallback(result, _weather_fallback(), "기상청 단기예보 fallback을 표시합니다.")
    fallback["summary"] = _weather_fallback()[0]["summary"]
    return fallback


def summarize_weather_items(items: list[Any]) -> str:
    if not items:
        return "기상 항목이 비어 있습니다. 현장 상태 확인이 필요합니다."
    categories: dict[str, Any] = {}
    for item in items:
        if isinstance(item, dict):
            category = str(item.get("category", ""))
            if category and category not in categories:
                categories[category] = item.get("fcstValue", item.get("obsrValue", ""))
    parts = []
    for key in ("SKY", "PTY", "TMP", "POP", "WSD"):
        if key in categories:
            parts.append(f"{key}={categories[key]}")
    return "기상 API 참고 요약: " + (", ".join(parts) if parts else "세부 항목 확인 필요")


def fetch_bus_arrival(city_code: str | None = None, node_id: str | None = None, route_id: str | None = None) -> dict[str, Any]:
    service_name = "TAGO 버스도착정보"
    if not city_code or not node_id:
        return make_api_result(
            service_name,
            "missing_params",
            data=_bus_arrival_fallback(),
            message="city_code와 node_id가 필요합니다.",
            source="fallback",
            endpoint_name=service_name,
        )
    params = {"cityCode": city_code, "nodeId": node_id}
    if route_id:
        params["routeId"] = route_id
    result = call_data_go_kr_api(f"{BUS_ARRIVAL_URL}/getSttnAcctoArvlPrearngeInfoList", params=params, service_name=service_name, timeout=8)
    return _with_fallback(result, _bus_arrival_fallback(), "TAGO 버스도착정보 fallback을 표시합니다.")


def fetch_bus_route(city_code: str | None = None, route_id: str | None = None, route_no: str | None = None) -> dict[str, Any]:
    service_name = "TAGO 버스노선정보"
    if not city_code:
        return make_api_result(
            service_name,
            "missing_params",
            data=_bus_route_fallback(),
            message="city_code가 필요합니다.",
            source="fallback",
            endpoint_name=service_name,
        )
    if route_id:
        endpoint = f"{BUS_ROUTE_URL}/getRouteAcctoThrghSttnList"
        params = {"cityCode": city_code, "routeId": route_id}
    else:
        endpoint = f"{BUS_ROUTE_URL}/getRouteNoList"
        params = {"cityCode": city_code}
        if route_no:
            params["routeNo"] = route_no
    result = call_data_go_kr_api(endpoint, params=params, service_name=service_name, timeout=8)
    return _with_fallback(result, _bus_route_fallback(), "TAGO 버스노선정보 fallback을 표시합니다.")


def fetch_weather_stub() -> dict[str, Any]:
    return make_api_result("날씨 API stub", "fallback", data=_weather_fallback(), message="날씨 API stub fallback입니다.", source="fallback", endpoint_name="weather_stub")


def fetch_bus_stub() -> dict[str, Any]:
    return make_api_result("버스 API stub", "fallback", data=_bus_arrival_fallback(), message="버스 API stub fallback입니다.", source="fallback", endpoint_name="bus_stub")


def fetch_public_facility_stub() -> dict[str, Any]:
    return make_api_result("공공시설 API stub", "fallback", data=_sports_facility_fallback(), message="공공시설 API stub fallback입니다.", source="fallback", endpoint_name="public_facility_stub")
