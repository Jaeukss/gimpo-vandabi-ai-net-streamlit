from __future__ import annotations

import streamlit as st

import modules.rag_bm25 as rag_bm25
from modules.llm_client import generate_rag_answer
from modules.safety import get_disclaimer, sanitize_public_claims
from modules.ui_components import info_box, inject_base_styles, metric_card, section_header, warning_box


st.set_page_config(page_title="생활체육 리포트", page_icon="♿", layout="wide")
inject_base_styles()


PROGRAMS = ["수영", "아쿠아로빅", "GX", "기구 필라테스", "보치아", "컬링", "플로어테니스", "피클볼"]
SUPPORT_TYPES = [
    "휠체어 또는 보행 보조 필요",
    "음성 안내 또는 유도 동선 필요",
    "단계별 안내 또는 보호자·동행 지원 필요",
    "일반",
]


def s(text: str) -> str:
    return sanitize_public_claims(text)


def build_template_report(inputs: dict, context: str) -> str:
    discomfort_text = "있음" if inputs["has_discomfort"] else "없음"
    instructor_text = "필요" if inputs["needs_instructor_check"] else "권장"
    fixed_notice = (
        "본 리포트는 건강 관련 최종 결정을 대체하지 않습니다. "
        "생활체육 참여를 돕기 위한 참고 정보이며, 참여 강도 변경은 지도자 확인 후 진행해야 합니다."
    )
    report = f"""
## 요약
- 선택 프로그램: {inputs["program"]}
- 참여 횟수: {inputs["participation_count"]}회
- 피로도: {inputs["fatigue"]}/10
- 불편감 여부: {discomfort_text}
- 달성도: {inputs["achievement"]}/10

## 참여 변화 참고
- 현재 입력 기준으로 참여 지속성과 피로도 변화를 함께 관찰하는 단계입니다.
- 불편감이 있으면 강도 변경보다 지도자 확인을 우선합니다.

## 다음 참여 가이드
- 다음 목표: {inputs["next_goal"] or "다음 참여 목표 미입력"}
- 접근성 지원 필요 유형: {inputs["support_type"]}
- 참여 전 이동 동선, 대기 공간, 보조 안내 가능 여부를 확인합니다.

## 지도자 확인 필요 사항
- 지도자 확인 필요 여부: {instructor_text}
- 피로도, 불편감, 접근성 지원 필요 유형을 지도자에게 공유합니다.

## 참고 근거
{context}

## 주의 문구
{fixed_notice}
"""
    return s(report.strip())


section_header("김포반다비센터 생활체육 추천 리포트", "참여 기록과 문서 근거를 바탕으로 지도자 확인용 참고 리포트를 생성합니다.")
info_box(get_disclaimer("sports"))

with st.form("sports_report_form"):
    col1, col2 = st.columns(2)
    with col1:
        program = st.selectbox(s("프로그램 선택"), [s(item) for item in PROGRAMS])
        participation_count = st.number_input(s("참여 횟수"), min_value=0, max_value=100, value=4, step=1)
        fatigue = st.slider(s("피로도"), min_value=0, max_value=10, value=4)
        has_discomfort = st.checkbox(s("불편감 여부"), value=False)
    with col2:
        achievement = st.slider(s("달성도"), min_value=0, max_value=10, value=6)
        next_goal = st.text_input(s("다음 목표"), placeholder=s("예: 주 1회 꾸준히 참여"))
        support_type = st.selectbox(s("접근성 지원 필요 유형"), [s(item) for item in SUPPORT_TYPES])
        needs_instructor_check = st.checkbox(s("지도자 확인 필요 여부"), value=True)

    submitted = st.form_submit_button(s("생활체육 리포트 생성"))

if submitted:
    rag_query = f"반다비 프로그램 생활체육 리포트 {program} 참여 피로도 달성도 지도자 확인"
    rag_index = rag_bm25.build_index("docs")
    rag_results = rag_bm25.search(rag_query, top_k=4, index=rag_index)
    context = rag_bm25.format_context(rag_results)

    inputs = {
        "program": program,
        "participation_count": participation_count,
        "fatigue": fatigue,
        "has_discomfort": has_discomfort,
        "achievement": achievement,
        "next_goal": next_goal,
        "support_type": support_type,
        "needs_instructor_check": needs_instructor_check,
    }
    template_report = build_template_report(inputs, context)

    llm_context = f"작성 초안:\n{template_report}\n\n참고 근거:\n{context}"
    llm_result = generate_rag_answer("생활체육 리포트 문장을 문서 근거 안에서 안전하게 정리해 주세요.", llm_context)
    final_report = s(str(llm_result.get("text", ""))) if llm_result.get("ok") else template_report

    col1, col2, col3 = st.columns(3)
    with col1:
        metric_card(s("문서 상태"), rag_index.data_status, f"results={len(rag_results)}")
    with col2:
        metric_card(s("답변 소스"), s(str(llm_result.get("source", "template"))), s("OpenRouter optional"))
    with col3:
        metric_card(s("프로그램"), s(program), s("생활체육"))

    st.markdown(final_report)

    with st.expander(s("RAG 참고 근거")):
        if rag_results:
            for item in rag_results:
                st.write(s(f"{item['rank']}. {item['source_file']} | {item['heading']} | score={item['score']}"))
            st.text_area(s("근거 context"), context, height=260)
        else:
            st.write(s("현재 등록된 문서에서 관련 근거가 확인되지 않습니다."))
else:
    warning_box(s("입력값을 작성한 뒤 생활체육 리포트를 생성하세요."))
