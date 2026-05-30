from __future__ import annotations

from datetime import time

import streamlit as st

import modules.rag_bm25 as rag_bm25
from modules.safety import get_disclaimer, sanitize_public_claims
from modules.ui_components import feature_card, info_box, inject_base_styles, metric_card, section_header, status_badge, warning_box


st.set_page_config(page_title="이동지원 추천", page_icon="♿", layout="wide")
inject_base_styles()


def s(text: str) -> str:
    return sanitize_public_claims(text)


def build_mobility_recommendation(wheelchair_user: bool, origin: str, destination: str) -> dict[str, str]:
    if wheelchair_user:
        candidate = "특별교통수단 우선 검토"
        reason = "휠체어 이용 조건이 있어 차량 승하차 지원 가능 여부 확인이 필요합니다."
    else:
        candidate = "대체수단과 특별교통수단 병행 검토"
        reason = "보행 가능 조건과 대중교통 접근성을 함께 확인할 수 있습니다."

    return {
        "candidate": s(candidate),
        "route": s(f"{origin or '출발지 미입력'} → {destination or '목적지 미입력'}"),
        "reason": s(reason),
        "next_step": s("운영기관 검토 요청 자료로 정리"),
    }


section_header("교통약자 이동지원 후보 추천", "이동지원 후보와 운영기관 검토 요청에 필요한 정보를 정리합니다.")
info_box(get_disclaimer("mobility"))

card1, card2 = st.columns(2)
with card1:
    feature_card("특별교통수단 안내", "휠체어 이용, 보행 보조 필요, 동행 필요 여부 등을 기준으로 운영기관 검토 항목을 정리합니다.")
with card2:
    feature_card("대체수단 안내", "대중교통, 동행 이동, 현장 접근성 확인 등 복수 후보를 함께 비교합니다.")

with st.form("mobility_form"):
    col1, col2 = st.columns(2)
    with col1:
        wheelchair_user = st.checkbox(s("휠체어 이용 여부"), value=False)
        origin = st.text_input(s("출발지"), placeholder=s("예: 장기역 인근"))
        desired_date = st.date_input(s("희망일"))
    with col2:
        destination = st.text_input(s("목적지"), value=s("김포반다비체육센터"))
        desired_time = st.time_input(s("희망 시간"), value=time(10, 0))
        support_note = st.text_area(s("추가 확인사항"), placeholder=s("동행, 승하차 지원, 안내 필요 여부 등"))

    submitted = st.form_submit_button(s("이동지원 후보 추천"))

query = "교통약자 이동지원 차량 신청 예약 콜센터 특별교통수단"
rag_index = rag_bm25.build_index("docs")
rag_results = rag_bm25.search(query, top_k=4, index=rag_index)
rag_context = rag_bm25.format_context(rag_results)

if submitted:
    recommendation = build_mobility_recommendation(wheelchair_user, origin, destination)
    st.session_state["mobility_recommendation"] = {
        "recommendation": recommendation,
        "desired_date": str(desired_date),
        "desired_time": str(desired_time),
        "support_note": support_note,
        "rag_data_status": rag_index.data_status,
        "rag_result_count": len(rag_results),
        "rag_context": rag_context,
        "rag_results": rag_results,
    }

saved = st.session_state.get("mobility_recommendation")

if saved:
    recommendation = saved["recommendation"]
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        metric_card(s("추천 후보"), recommendation["candidate"], s("candidate"))
    with col_b:
        metric_card(s("희망 일정"), f"{saved['desired_date']} {saved['desired_time']}", s("사용자 입력"))
    with col_c:
        metric_card(s("문서 상태"), saved["rag_data_status"], f"results={saved['rag_result_count']}")

    info_box(s(f"이동 구간: {recommendation['route']}"))
    info_box(s(f"추천 사유: {recommendation['reason']}"))
    info_box(s(f"다음 단계: {recommendation['next_step']}"))
    if saved["support_note"]:
        warning_box(s(f"추가 확인사항: {saved['support_note']}"))

    with st.expander(s("교통약자 이동지원 관련 RAG 근거")):
        if saved["rag_results"]:
            for item in saved["rag_results"]:
                st.write(s(f"{item['rank']}. {item['source_file']} | {item['heading']} | score={item['score']}"))
            st.text_area(s("근거 context"), saved["rag_context"], height=260)
        else:
            st.write(s("현재 등록된 문서에서 관련 근거가 확인되지 않습니다."))

    if st.button(s("운영기관 검토 요청")):
        status_badge(s("UI 상태 등록"))
        info_box(s("요청 후보가 화면 상태로만 등록되었습니다. 실제 접수 처리 또는 이용 가능 여부 결정이 아닙니다."))
else:
    with st.expander(s("교통약자 이동지원 관련 RAG 근거 미리보기")):
        st.write(s(f"docs 상태: {rag_index.data_status}, 검색 결과: {len(rag_results)}건"))
        st.text_area(s("근거 context"), rag_context, height=220)

warning_box(s("이 화면은 이동지원 후보 추천용입니다. 실제 실행 또는 이용 가능 여부 결정은 운영기관 확인이 필요합니다."))
