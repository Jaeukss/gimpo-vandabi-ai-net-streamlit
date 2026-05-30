from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

import modules.rag_bm25 as rag_bm25
from modules.api_clients import fetch_bus_stub, fetch_public_facility_stub, fetch_weather_stub
from modules.config import list_config_status
from modules.data_loader import (
    load_csv_inventory,
    load_low_floor_bus_data,
    load_mobility_center_data,
    load_protected_zone_data,
)
from modules.emailer import email_status
from modules.safety import DATA_FALLBACK_NOTICE, get_disclaimer, sanitize_public_claims
from modules.scoring import calculate_viable_path_score
from modules.ui_components import info_box, inject_base_styles, metric_card, section_header, status_badge, warning_box
from modules.vision import vision_status
from modules.voice import voice_status


st.set_page_config(page_title="B2G 대시보드", page_icon="♿", layout="wide")
inject_base_styles()


def s(text: str) -> str:
    return sanitize_public_claims(text)


def folder_status(path: str, pattern: str = "*") -> dict[str, str | int]:
    base = Path(path)
    if not base.exists() or not base.is_dir():
        return {"folder": path, "status": "prototype_dummy", "count": 0}
    try:
        count = len([item for item in base.glob(pattern) if item.is_file()])
        return {"folder": path, "status": "available", "count": count}
    except Exception:
        return {"folder": path, "status": "mock_fallback", "count": 0}


def render_status_card(title: str, value: str | int | float, note: str = "") -> None:
    metric_card(s(title), s(str(value)), s(note))


def render_chart(frame: pd.DataFrame) -> None:
    try:
        import plotly.express as px

        fig = px.bar(frame, x="metric", y="value", color="status", text="value", title=s("파일럿 대시보드 예시"))
        fig.update_layout(showlegend=True, height=420)
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.bar_chart(frame.set_index("metric")["value"])


section_header("B2G 운영 대시보드", "파일럿 대시보드 예시입니다. 실제 운영 통계로 단정하지 않습니다.")
info_box(get_disclaimer("general"))
info_box(DATA_FALLBACK_NOTICE)

rag_index = rag_bm25.build_index("docs")
inventory = load_csv_inventory()
config_status = list_config_status()
mobility = load_mobility_center_data()
protected_zone = load_protected_zone_data()
low_floor_bus = load_low_floor_bus_data()
weather = fetch_weather_stub()
bus = fetch_bus_stub()
facility = fetch_public_facility_stub()
vision = vision_status()
voice = voice_status()
email = email_status()

sample_scores = [
    calculate_viable_path_score({"destination": "김포반다비체육센터", "public_transport_available": True})["score"],
    calculate_viable_path_score({"destination": "김포반다비체육센터", "mobility_support_needed": True, "public_transport_available": False})["score"],
    calculate_viable_path_score({"destination": "김포반다비체육센터", "accessibility_support_type": "휠체어 또는 보행 보조 필요"})["score"],
]
average_score = round(sum(sample_scores) / len(sample_scores), 1)

section_header("핵심 상태 카드", "prototype_dummy 또는 mock_fallback 라벨은 실제 운영 데이터가 아님을 의미합니다.")
cards = [
    ("RAG 문서 로딩 상태", rag_index.data_status, f"chunks={len(rag_index.chunks)}"),
    ("CSV 로딩 상태", "real_csv" if not inventory.empty else "prototype_dummy", f"files={len(inventory)}"),
    ("secrets 설정 여부", f"{sum(config_status.values())}/{len(config_status)}", "values hidden"),
    ("이동 가능성 평균 점수", average_score, "prototype_dummy"),
    ("이동지원 후보 요청 수", 7, "prototype_dummy"),
    ("AI 제보 검토 대기 수", 3, "prototype_dummy"),
    ("생활체육 리포트 수", 5, "prototype_dummy"),
    ("외부 API 상태", "mock_fallback", "weather/bus/facility"),
    ("mock/fallback 사용 여부", "사용 중", "pilot mode"),
]

for start in range(0, len(cards), 3):
    columns = st.columns(3)
    for column, (title, value, note) in zip(columns, cards[start : start + 3]):
        with column:
            render_status_card(str(title), value, str(note))

status_badge(s("prototype_dummy"))
warning_box(s("표시된 운영 지표는 파일럿 대시보드 예시이며 실제 운영 통계가 아닙니다."))

section_header("운영 지표 차트", "plotly 사용 가능 시 plotly, 실패 시 Streamlit bar chart로 표시합니다.")
chart_frame = pd.DataFrame(
    [
        {"metric": "이동 가능성 평균", "value": average_score, "status": "prototype_dummy"},
        {"metric": "이동지원 후보 요청", "value": 7, "status": "prototype_dummy"},
        {"metric": "AI 제보 검토 대기", "value": 3, "status": "prototype_dummy"},
        {"metric": "생활체육 리포트", "value": 5, "status": "prototype_dummy"},
    ]
)
render_chart(chart_frame)

section_header("CSV Inventory", "./data/*.csv와 ./*.csv 탐색 결과입니다.")
if inventory.empty:
    warning_box(s("탐지된 CSV가 없습니다. prototype_dummy 상태로 화면을 유지합니다."))
    st.dataframe(pd.DataFrame(columns=["file_name", "path", "rows", "columns", "status", "data_status"]), use_container_width=True)
else:
    st.dataframe(inventory, use_container_width=True)

section_header("데이터 및 API 상세 상태", "실패해도 앱 실행은 유지됩니다.")
detail_rows = [
    {"item": "mobility_center", "status": mobility.get("data_status", "missing"), "note": f"rows={len(mobility.get('data', []))}"},
    {"item": "protected_zone", "status": protected_zone.get("data_status", "missing"), "note": f"rows={len(protected_zone.get('data', []))}"},
    {"item": "low_floor_bus", "status": low_floor_bus.get("data_status", "missing"), "note": f"rows={len(low_floor_bus.get('data', []))}"},
    {"item": "weather_api", "status": weather["data_status"], "note": weather["source"]},
    {"item": "bus_api", "status": bus["data_status"], "note": bus["source"]},
    {"item": "facility_api", "status": facility["data_status"], "note": facility["source"]},
    {"item": "vision", "status": vision["data_status"], "note": "optional"},
    {"item": "voice", "status": voice["data_status"], "note": "optional"},
    {"item": "email", "status": email["data_status"], "note": "optional"},
]
st.dataframe(pd.DataFrame(detail_rows), use_container_width=True)

section_header("폴더 상태", "docs와 references 폴더가 없어도 앱 실행은 유지됩니다.")
folder_rows = [folder_status("docs", "*.md"), folder_status("docs", "*.md.md"), folder_status("references", "*")]
st.dataframe(pd.DataFrame(folder_rows), use_container_width=True)
