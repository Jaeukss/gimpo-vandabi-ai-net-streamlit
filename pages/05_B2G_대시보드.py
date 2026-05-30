from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

import modules.rag_bm25 as rag_bm25
from modules.api_clients import (
    data_go_kr_status,
    fetch_bus_stub,
    fetch_public_facility_stub,
    fetch_weather_stub,
    test_vworld_geocode_connection,
    vworld_status,
)
from modules.config import list_config_status
from modules.data_loader import load_csv_inventory, load_low_floor_bus_data, load_mobility_center_data, load_protected_zone_data
from modules.emailer import email_status
from modules.llm_client import test_openrouter_text_connection
from modules.safety import DATA_FALLBACK_NOTICE, get_disclaimer, sanitize_public_claims
from modules.scoring import calculate_viable_path_score
from modules.ui_components import (
    inject_global_styles,
    render_app_header,
    render_disclaimer_box,
    render_metric_card,
    render_page_footer_note,
    render_section_header,
    render_status_badge,
    render_warning_box,
)
from modules.vision import test_vision_model_available, vision_status
from modules.voice import voice_status


st.set_page_config(page_title="B2G 대시보드", page_icon="📊", layout="wide")
inject_global_styles()


def s(text: Any) -> str:
    return sanitize_public_claims(str(text))


def folder_status(path: str, pattern: str = "*") -> dict[str, str | int]:
    base = Path(path)
    if not base.exists() or not base.is_dir():
        return {"folder": path, "status": "prototype_dummy", "count": 0}
    try:
        return {"folder": path, "status": "available", "count": len([item for item in base.glob(pattern) if item.is_file()])}
    except Exception:
        return {"folder": path, "status": "mock_fallback", "count": 0}


def status_style(status: str) -> str:
    if status in {"configured", "enabled_ready", "loaded", "real_api", "real_csv"}:
        return "success"
    if status in {"disabled", "fallback", "mock_fallback", "prototype_dummy", "missing_model"}:
        return "warning"
    if status in {"missing", "missing_key", "missing_config", "empty"}:
        return "danger"
    return "muted"


def render_chart(frame: pd.DataFrame) -> None:
    try:
        import plotly.express as px

        fig = px.bar(frame, x="metric", y="value", color="status", text="value", title=s("파일럿 운영 참고 차트"))
        fig.update_layout(showlegend=True, height=420, paper_bgcolor="#0f172a", plot_bgcolor="#111c33", font_color="#e5edf7")
        st.plotly_chart(fig, width="stretch")
    except Exception:
        st.bar_chart(frame.set_index("metric")["value"])


render_app_header(
    "B2G 운영 참고 대시보드",
    "Secrets 설정 상태, RAG 문서, CSV, fallback 사용 여부를 파일럿 기준으로 점검합니다.",
    "B2G",
)
render_disclaimer_box(get_disclaimer("general"))
render_disclaimer_box(DATA_FALLBACK_NOTICE)

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
vworld = vworld_status()
data_go = data_go_kr_status()

sample_scores = [
    calculate_viable_path_score({"destination": "김포반다비체육센터", "public_transport_available": True})["score"],
    calculate_viable_path_score({"destination": "김포반다비체육센터", "mobility_support_needed": True, "public_transport_available": False})["score"],
    calculate_viable_path_score({"destination": "김포반다비체육센터", "accessibility_support_type": "휠체어 또는 보행 보조 필요"})["score"],
]
average_score = round(sum(sample_scores) / len(sample_scores), 1)
configured_count = sum(1 for status in config_status.values() if status in {"configured", "enabled"})

render_section_header("KPI", "파일럿 KPI 카드", "운영 실적이 아닌 prototype_dummy 점검 수치입니다.")
kpi_cards = [
    ("RAG 문서", rag_index.data_status, f"chunks={len(rag_index.chunks)}", "info"),
    ("CSV 파일", len(inventory), "탐색된 파일 수", "success" if not inventory.empty else "warning"),
    ("Secrets 상태", f"{configured_count}/{len(config_status)}", "값 미표시", "purple"),
    ("이동 가능성 평균", average_score, "prototype_dummy", "warning"),
]
cols = st.columns(4)
for col, (label, value, helper, status) in zip(cols, kpi_cards):
    with col:
        render_metric_card(label, value, helper, status)

ops_cards = [
    ("이동지원 후보 요청", 7, "prototype_dummy", "info"),
    ("AI 제보 검토 대기", 3, "prototype_dummy", "warning"),
    ("생활체육 리포트", 5, "prototype_dummy", "purple"),
    ("외부 API 상태", "fallback 가능", "자동 호출 없음", "muted"),
]
cols = st.columns(4)
for col, (label, value, helper, status) in zip(cols, ops_cards):
    with col:
        render_metric_card(label, value, helper, status)

render_status_badge("파일럿 상태 점검", "info")
render_status_badge("prototype_dummy 포함", "warning")
render_status_badge("키 값 미표시", "success")
render_warning_box("표시된 운영 지표는 파일럿 대시보드 예시이며 실제 운영 통계가 아닙니다.")

render_section_header("SECRETS QA", "Secrets 기반 QA 상태", "실제 키 값, 일부 마스킹 값, 길이 정보는 표시하지 않습니다.")
text_model_status = "configured" if config_status.get("OPENROUTER_API_KEY") == "configured" and config_status.get("OPENROUTER_MODEL") == "configured" else "fallback"
vision_model_status = "configured" if vision["data_status"] == "configured" else "fallback"
vworld_key_status = "configured" if vworld["data_status"] == "configured" else "fallback"
sendgrid_status = str(email["data_status"])
rag_docs_status = "loaded" if len(rag_index.chunks) > 0 else "empty"
csv_status = "loaded" if not inventory.empty else "empty"

qa_rows = [
    {"item": "OpenRouter Text Model", "status": text_model_status, "note": "버튼 실행 시에만 연결 테스트"},
    {"item": "OpenRouter Vision Model", "status": vision_model_status, "note": "이미지 분석은 업로드 후에만 실행"},
    {"item": "VWorld API Key", "status": vworld_key_status, "note": "주소 변환 실패 시 mock 좌표 사용"},
    {"item": "DATA GO KR Key", "status": data_go["data_status"], "note": "실제 endpoint 호출은 9단계 예정"},
    {"item": "SendGrid", "status": sendgrid_status, "note": "기본 disabled 권장"},
    {"item": "RAG Docs", "status": rag_docs_status, "note": rag_index.data_status},
    {"item": "CSV Data", "status": csv_status, "note": "real_csv 또는 mock_fallback"},
]
st.dataframe(pd.DataFrame(qa_rows), width="stretch")

qa_cols = st.columns(3)
with qa_cols[0]:
    if st.button("OpenRouter 텍스트 간단 연결 테스트", use_container_width=True):
        result = test_openrouter_text_connection()
        render_status_badge(s(result["status"]), status_style(str(result["status"])))
        st.caption(s(f"source={result['source']} reason={result['reason']}"))
        st.write(s(result["text"]))
with qa_cols[1]:
    if st.button("Vision 설정 상태 확인", use_container_width=True):
        result = test_vision_model_available()
        render_status_badge(s(result["status"]), status_style(str(result["status"])))
        st.caption(s(f"source={result['source']} reason={result['reason']}"))
        st.write(s(result["message"]))
with qa_cols[2]:
    if st.button("VWorld 주소 변환 간단 테스트", use_container_width=True):
        result = test_vworld_geocode_connection()
        render_status_badge(s(result["status"]), status_style(str(result["status"])))
        st.caption(s(f"reason={result['reason']} has_coordinate={result['has_coordinate']}"))

render_section_header("CHART", "운영 참고 차트", "plotly 사용 가능 시 plotly, 실패 시 Streamlit bar chart로 표시합니다.")
chart_frame = pd.DataFrame(
    [
        {"metric": "이동 가능성 평균", "value": average_score, "status": "prototype_dummy"},
        {"metric": "이동지원 후보 요청", "value": 7, "status": "prototype_dummy"},
        {"metric": "AI 제보 검토 대기", "value": 3, "status": "prototype_dummy"},
        {"metric": "생활체육 리포트", "value": 5, "status": "prototype_dummy"},
    ]
)
render_chart(chart_frame)

render_section_header("STATUS", "데이터 및 API 상세 상태", "실패해도 앱 실행은 유지됩니다.")
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
    {"item": "vworld", "status": vworld["data_status"], "note": "user-triggered test only"},
    {"item": "data_go_kr", "status": data_go["data_status"], "note": "step 9 integration target"},
]
st.dataframe(pd.DataFrame(detail_rows), width="stretch")

with st.expander("CSV Inventory"):
    if inventory.empty:
        render_warning_box("탐색된 CSV가 없습니다. prototype_dummy 상태로 화면은 유지됩니다.")
        st.dataframe(pd.DataFrame(columns=["file_name", "path", "rows", "columns", "status", "data_status"]), width="stretch")
    else:
        st.dataframe(inventory, width="stretch")

with st.expander("폴더 상태"):
    folder_rows = [folder_status("docs", "*.md"), folder_status("docs", "*.md.md"), folder_status("references", "*")]
    st.dataframe(pd.DataFrame(folder_rows), width="stretch")

render_page_footer_note()
