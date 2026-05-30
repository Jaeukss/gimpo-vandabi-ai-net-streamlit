from __future__ import annotations

import streamlit as st

from modules.config import get_secret
from modules.emailer import build_official_draft, can_send_email, email_status, improve_draft_with_llm, send_email_with_sendgrid
from modules.safety import get_disclaimer, sanitize_public_claims
from modules.ui_components import info_box, inject_base_styles, metric_card, section_header, warning_box


st.set_page_config(page_title="공문 초안 이메일", page_icon="♿", layout="wide")
inject_base_styles()


def s(text: str) -> str:
    return sanitize_public_claims(text)


section_header("관리자 검증용 공문 초안 및 SendGrid 옵션", "초안 작성과 optional 이메일 발송을 분리합니다.")
info_box(get_disclaimer("general"))

email_info = email_status()
col1, col2, col3 = st.columns(3)
with col1:
    metric_card(s("SendGrid 상태"), s(str(email_info["data_status"])), s("optional"))
with col2:
    metric_card(s("발송 활성화"), s("enabled" if email_info["enabled"] else "disabled"), s("ENABLE_SENDGRID_SEND"))
with col3:
    metric_card(s("발신 이메일"), s("configured" if email_info["has_sender"] else "missing"), s("value hidden"))

with st.form("official_draft_form"):
    title = st.text_input(s("제보 제목"), placeholder=s("예: 접근성 확인 요청"))
    body = st.text_area(s("제보 내용"), placeholder=s("검토가 필요한 내용을 입력"))
    location = st.text_input(s("위치"), placeholder=s("예: 김포반다비체육센터 출입구 인근"))
    recipient = st.text_input(s("수신 부서/담당자"), placeholder=s("예: 담당 부서 확인 필요"))
    sender_default = str(get_secret("EMAIL_ADDRESS", "") or "")
    sender = st.text_input(s("발신자 이메일"), value=sender_default, placeholder=s("발신자 이메일"))
    to_email = st.text_input(s("수신 이메일"), placeholder=s("SendGrid 발송 시에만 필요"))
    submitted = st.form_submit_button(s("공문 초안 생성"))

if submitted:
    draft = build_official_draft(title, body, location, recipient, sender)
    improved = improve_draft_with_llm(draft)
    final_draft = s(str(improved.get("text", draft)))
    st.session_state["official_draft"] = {
        "text": final_draft,
        "title": s(title or "관리자 검증용 공문 초안"),
        "to_email": s(to_email),
        "source": s(str(improved.get("source", "template"))),
    }

saved = st.session_state.get("official_draft")
if saved:
    metric_card(s("초안 생성 소스"), saved["source"], s("OpenRouter optional"))
    st.subheader(s("초안 전문 미리보기"))
    st.text_area(s("관리자 검증용 공문 초안"), saved["text"], height=420)

    confirmed = st.checkbox(s("초안 내용을 확인했으며, 관리자 검증용 자료로만 사용합니다."))
    send_status = can_send_email()
    send_allowed = bool(confirmed and send_status["can_send"])

    if not confirmed:
        warning_box(s("확인 체크박스를 선택해야 발송 버튼을 사용할 수 있습니다."))
    if not send_status["can_send"]:
        warning_box(s("ENABLE_SENDGRID_SEND, SENDGRID_API_KEY, EMAIL_ADDRESS 설정이 모두 충족되지 않아 실제 발송은 비활성화됩니다."))

    if st.button(s("SendGrid로 초안 발송"), disabled=not send_allowed):
        result = send_email_with_sendgrid(saved["to_email"], saved["title"], saved["text"])
        if result.ok:
            info_box(s(result.message))
        else:
            warning_box(s(result.message))
else:
    warning_box(s("입력값을 작성한 뒤 관리자 검증용 공문 초안을 생성하세요."))
