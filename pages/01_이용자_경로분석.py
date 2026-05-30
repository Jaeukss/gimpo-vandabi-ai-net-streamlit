from __future__ import annotations

from datetime import time

import pandas as pd
import streamlit as st

from modules.api_clients import geocode_vworld, mock_coordinate
from modules.safety import get_disclaimer, sanitize_public_claims
from modules.scoring import calculate_viable_path_score
from modules.ui_components import info_box, inject_base_styles, metric_card, section_header, warning_box


st.set_page_config(page_title="이용자 경로분석", page_icon="♿", layout="wide")
inject_base_styles()


def s(text: str) -> str:
    return sanitize_public_claims(text)


def resolve_coordinate(address: str, fallback_kind: str) -> dict:
    geocode, meta = geocode_vworld(address)
    if geocode:
        try:
            return {
                "lat": float(geocode["y"]),
                "lon": float(geocode["x"]),
                "label": address,
                "data_status": meta.get("data_status", "real_api"),
                "reason": meta.get("reason", ""),
            }
        except Exception:
            pass

    mock = mock_coordinate(fallback_kind)
    return {
        "lat": float(mock["lat"]),
        "lon": float(mock["lon"]),
        "label": address or mock["label"],
        "data_status": meta.get("data_status", "mock_fallback"),
        "reason": meta.get("reason", "mock coordinate"),
    }


def render_reference_map(origin: dict, destination: dict) -> None:
    st.caption(s("아래 지도는 참고 위치 표시이며 실제 최단 경로를 의미하지 않습니다."))
    try:
        import folium
        from streamlit_folium import st_folium

        center = [(origin["lat"] + destination["lat"]) / 2, (origin["lon"] + destination["lon"]) / 2]
        fmap = folium.Map(location=center, zoom_start=12)
        folium.Marker(
            [origin["lat"], origin["lon"]],
            tooltip=s("출발지 참고 위치"),
            popup=s(f"출발지: {origin['label']}"),
            icon=folium.Icon(color="blue", icon="user"),
        ).add_to(fmap)
        folium.Marker(
            [destination["lat"], destination["lon"]],
            tooltip=s("목적지 참고 위치"),
            popup=s(f"목적지: {destination['label']}"),
            icon=folium.Icon(color="green", icon="flag"),
        ).add_to(fmap)
        folium.PolyLine(
            [[origin["lat"], origin["lon"]], [destination["lat"], destination["lon"]]],
            color="#0b7285",
            weight=3,
            opacity=0.65,
            dash_array="8",
            tooltip=s("참고 위치 연결선"),
        ).add_to(fmap)
        st_folium(fmap, height=420, use_container_width=True)
    except Exception:
        try:
            st.map(
                pd.DataFrame(
                    [
                        {"lat": origin["lat"], "lon": origin["lon"]},
                        {"lat": destination["lat"], "lon": destination["lon"]},
                    ]
                ),
                latitude="lat",
                longitude="lon",
            )
        except Exception:
            st.write(s(f"출발지 좌표: {origin['lat']}, {origin['lon']}"))
            st.write(s(f"목적지 좌표: {destination['lat']}, {destination['lon']}"))


section_header("이용자 경로분석", "접근성, 이동지원 필요 여부, 날씨 영향, 대중교통 가능성을 함께 검토합니다.")
info_box(get_disclaimer("mobility"))

with st.form("route_form"):
    col1, col2 = st.columns(2)
    with col1:
        origin = st.text_input(s("출발지"), placeholder=s("예: 김포시청, 장기역, 운양역"))
        use_date = st.date_input(s("이용 희망일"))
        support_type = st.selectbox(
            s("접근성 지원 필요 유형"),
            [
                s("휠체어 또는 보행 보조 필요"),
                s("음성 안내 또는 유도 동선 필요"),
                s("단계별 안내 또는 보호자·동행 지원 필요"),
                s("일반"),
            ],
        )
        mobility_needed = st.checkbox(s("이동지원 필요 여부"), value=False)
        weather_enabled = st.checkbox(s("날씨 영향 반영 여부"), value=True)
    with col2:
        destination = st.text_input(s("목적지"), value=s("김포반다비체육센터"))
        use_time = st.time_input(s("이용 희망 시간"), value=time(10, 0))
        companion_needed = st.checkbox(s("동행 필요 여부"), value=False)
        public_transport_available = st.checkbox(s("대중교통 이용 가능 여부"), value=True)

    submitted = st.form_submit_button(s("경로 참고 분석"))

if submitted:
    origin_coord = resolve_coordinate(origin, "default_origin")
    destination_coord = resolve_coordinate(destination, "default_destination")

    inputs = {
        "origin": origin,
        "destination": destination,
        "use_date": str(use_date),
        "use_time": str(use_time),
        "accessibility_support_type": support_type,
        "mobility_support_needed": mobility_needed,
        "companion_needed": companion_needed,
        "weather_enabled": weather_enabled,
        "public_transport_available": public_transport_available,
        "origin_geocode_status": origin_coord["data_status"],
        "destination_geocode_status": destination_coord["data_status"],
    }
    result = calculate_viable_path_score(inputs)

    section_header("참고 위치 표시", "VWorld 실패 또는 키 없음 상태에서는 mock 좌표를 사용합니다.")
    render_reference_map(origin_coord, destination_coord)

    col_score, col_level, col_source = st.columns(3)
    with col_score:
        metric_card(s("Viable Path Score"), result["score"], s(result["model_type"]))
    with col_level:
        metric_card(s("이동성 등급"), s(result["mobility_level"]), s(result["ai_name"]))
    with col_source:
        metric_card(s("좌표 상태"), f"{origin_coord['data_status']} / {destination_coord['data_status']}", s("origin / destination"))

    st.subheader(s("점수 항목"))
    st.dataframe(
        pd.DataFrame(
            [{"항목": key, "점수": value} for key, value in result["item_scores"].items()]
        ),
        use_container_width=True,
    )

    st.subheader(s("위험요소"))
    for item in result["risk_factors"]:
        warning_box(s(item))

    st.subheader(s("권장 조치"))
    for item in result["recommended_actions"]:
        info_box(s(item))

    st.subheader(s("설명"))
    st.write(s(result["explanation"]))

    with st.expander(s("데이터 출처와 한계")):
        st.write([s(item) for item in result["data_sources"]])
        st.write([s(item) for item in result["limitations"]])
else:
    warning_box(s("입력값을 작성한 뒤 경로 참고 분석을 실행하세요."))
