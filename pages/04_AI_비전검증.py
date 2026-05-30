from __future__ import annotations

import streamlit as st

from modules.safety import get_disclaimer, sanitize_public_claims
from modules.ui_components import info_box, inject_base_styles, metric_card, section_header, status_badge, warning_box
from modules.vision import analyze_accessibility_image, mask_notice, vision_status


st.set_page_config(page_title="AI 비전검증", page_icon="♿", layout="wide")
inject_base_styles()


def s(text: str) -> str:
    return sanitize_public_claims(text)


REPORT_TYPES = ["경사로 불편", "보행 장애물", "안내표지 부족", "장애인 화장실 접근성", "기타"]


section_header("AI 비전검증", "업로드 이미지를 AI 임시 검토 결과로 정리합니다.")
info_box(get_disclaimer("vision"))

status = vision_status()
col1, col2 = st.columns(2)
with col1:
    metric_card(s("Vision 설정"), s(str(status["data_status"])), s("optional"))
with col2:
    metric_card(s("개인정보 마스킹"), s("관리자 확인 필요"), s("privacy"))

with st.form("vision_form"):
    report_type = st.selectbox(s("제보 유형"), [s(item) for item in REPORT_TYPES])
    location = st.text_input(s("위치"), placeholder=s("예: 김포반다비체육센터 출입구 인근"))
    description = st.text_area(s("설명"), placeholder=s("불편 사항과 확인이 필요한 지점을 입력"))
    uploaded = st.file_uploader(s("이미지 업로드"), type=["png", "jpg", "jpeg", "webp"])
    submitted = st.form_submit_button(s("AI 임시 검토 실행"))

if uploaded is not None:
    st.image(uploaded, caption=s("업로드 이미지 미리보기"), use_container_width=True)

if submitted:
    image_bytes = uploaded.getvalue() if uploaded is not None else None
    result = analyze_accessibility_image(image_bytes, report_type, f"{location}\n{description}")

    st.subheader(s("AI 임시 검토 결과"))
    result_col1, result_col2, result_col3 = st.columns(3)
    with result_col1:
        metric_card(s("위험 수준"), s(str(result.get("risk_level", "확인 필요"))), s("temporary"))
    with result_col2:
        metric_card(s("관리자 확인"), s("필요" if result.get("review_required") else "권장"), s("review"))
    with result_col3:
        metric_card(s("분석 소스"), s(str(result.get("source", "demo_fallback"))), s("fallback aware"))

    for item in result.get("detected_items", []):
        info_box(s(str(item)))

    warning_box(s(str(result.get("recommended_next_step", "관리자 검증 후 담당 부서 확인 자료로 정리"))))
    warning_box(s(str(result.get("mask_notice", mask_notice()))))
    warning_box(s(str(result.get("notice", ""))))
    status_badge(s("AI 임시 검토 결과"))
else:
    warning_box(s("이미지, 제보 유형, 위치 설명을 입력한 뒤 AI 임시 검토를 실행하세요."))
