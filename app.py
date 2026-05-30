from __future__ import annotations

import streamlit as st

import modules.llm_client as llm_client
import modules.rag_bm25 as rag_bm25
from modules.safety import DATA_FALLBACK_NOTICE, SERVICE_DISCLAIMER
from modules.ui_components import feature_card, info_box, inject_base_styles, metric_card, section_header, status_badge
from modules.voice import render_browser_tts_button, render_voice_command_box


st.set_page_config(
    page_title="김포시 반다비 AI Net",
    page_icon="♿",
    layout="wide",
)

inject_base_styles()

st.title("김포시 반다비 AI Net")
st.caption("공공서비스, 모빌리티, 생활체육 지원을 위한 Streamlit 파일럿 플랫폼")

with st.sidebar:
    section_header("음성 명령", "음성 입력은 optional이며 텍스트 fallback을 제공합니다.")
    voice_result = render_voice_command_box("app_sidebar")
    st.caption(f"intent={voice_result['intent']}")

info_box(SERVICE_DISCLAIMER)

col_status, col_docs, col_data = st.columns(3)
with col_status:
    metric_card("서비스 단계", "1단계", "멀티페이지 프로젝트 골격")
with col_docs:
    metric_card("RAG 문서", "Markdown", ".md 및 .md.md 대응 예정")
with col_data:
    metric_card("Fallback", "Enabled", DATA_FALLBACK_NOTICE)

st.divider()

section_header(
    "주요 화면",
    "왼쪽 사이드바에서 Streamlit 기본 멀티페이지 화면을 선택합니다.",
)

row1 = st.columns(3)
with row1[0]:
    feature_card("이용자 경로분석", "출발지, 도착지, 접근성 요소를 기반으로 참고 분석 결과를 구성합니다.")
with row1[1]:
    feature_card("이동지원 후보 추천", "운영기관 검토 요청에 필요한 이동지원 후보 정보를 정리합니다.")
with row1[2]:
    feature_card("생활체육 리포트", "김포반다비센터 생활체육 추천과 지도자 확인 필요 항목을 정리합니다.")

row2 = st.columns(3)
with row2[0]:
    feature_card("AI 비전검증", "이미지 업로드 기반 접근성 확인 흐름을 optional 기능으로 확장합니다.")
with row2[1]:
    feature_card("B2G 대시보드", "CSV 데이터와 운영 지표를 안전하게 표시하는 관리자 화면입니다.")
with row2[2]:
    feature_card("공문 초안 이메일", "관리자 검증용 공문 초안과 SendGrid 발송 옵션을 분리합니다.")

st.divider()

section_header("운영 원칙")
status_badge("Public repo safe")
st.write("- API 키는 `st.secrets` 또는 환경변수에서만 읽습니다.")
st.write("- `.streamlit/secrets.toml`은 생성하지 않습니다.")
st.write("- 외부 API 실패, 문서 없음, CSV 없음 상황에서도 앱 실행을 유지합니다.")

st.divider()

section_header(
    "RAG 문서 질문 테스트",
    "`docs/`의 `.md`, `.md.md`, `.txt` 문서를 BM25로 검색하고 OpenRouter 또는 로컬 fallback 답변을 표시합니다.",
)

rag_index = rag_bm25.build_index("docs")
rag_col1, rag_col2, rag_col3 = st.columns(3)
with rag_col1:
    metric_card("docs 상태", rag_index.data_status, f"documents={len(rag_index.documents)}")
with rag_col2:
    metric_card("검색기", rag_index.search_status, f"chunks={len(rag_index.chunks)}")
with rag_col3:
    metric_card("읽기 오류", len(rag_index.errors), "errors")

if rag_index.errors:
    with st.expander("문서 읽기 오류"):
        for error in rag_index.errors:
            st.write(f"- {error}")

rag_question = st.text_input(
    "문서 질문",
    placeholder="예: 반다비 프로그램 이용 시 확인해야 할 점은?",
)
rag_top_k = st.slider("검색 결과 수", min_value=1, max_value=8, value=5)

if st.button("RAG 검색 및 답변 생성", type="primary"):
    if not rag_question.strip():
        st.warning("질문을 입력하세요.")
    else:
        results = rag_bm25.search(rag_question, top_k=rag_top_k, index=rag_index)
        context = rag_bm25.format_context(results)

        if results:
            st.dataframe(
                [
                    {
                        "rank": item["rank"],
                        "source_file": item["source_file"],
                        "heading": item["heading"],
                        "score": item["score"],
                    }
                    for item in results
                ],
                use_container_width=True,
            )
        else:
            st.info("검색된 문서 근거가 없습니다. fallback 답변을 표시합니다.")

        with st.expander("검색 context"):
            st.text_area("context", context, height=260)

        answer = llm_client.generate_rag_answer(rag_question, context)
        st.subheader("답변")
        st.write(answer["text"])
        render_browser_tts_button(str(answer["text"])[:700])
        st.caption(f"source={answer.get('source', 'fallback')}, reason={answer.get('reason', '')}")
