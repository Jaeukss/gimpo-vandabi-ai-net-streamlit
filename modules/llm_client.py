"""OpenRouter LLM client with strict fallback behavior."""

from __future__ import annotations

from typing import Any

from modules.config import get_secret
from modules.safety import get_disclaimer, sanitize_public_claims


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "openrouter/free"
LATEST_NOTICE = "최신 정보는 김포반다비체육센터 또는 김포시교통약자이동지원센터 확인이 필요합니다."

RAG_SYSTEM_PROMPT = (
    "등록된 docs 근거 안에서만 답한다. "
    "문서에 없는 내용은 '현재 등록된 문서에서 확인되지 않습니다.'라고 답한다. "
    "실행 완료, 이용 가능 여부 결정, 건강 관련 최종 결정으로 오해될 표현은 금지한다. "
    f"답변 끝에 '{LATEST_NOTICE}'를 붙인다."
)


def _fallback_result(source: str, text: str, reason: str = "") -> dict[str, Any]:
    return {
        "ok": False,
        "source": source,
        "text": sanitize_public_claims(text),
        "reason": reason,
    }


def _classify_exception(exc: Exception) -> str:
    name = exc.__class__.__name__.lower()
    message = str(exc).lower()
    if "timeout" in name or "timeout" in message:
        return "timeout"
    if "rate" in name or "429" in message:
        return "rate_limit"
    if "notfound" in name or "model" in message:
        return "model_error"
    return "request_error"


def _append_latest_notice(text: str) -> str:
    cleaned = (text or "").strip()
    if LATEST_NOTICE not in cleaned:
        cleaned = f"{cleaned}\n\n{LATEST_NOTICE}".strip()
    return cleaned


def generate_with_openrouter(
    prompt: str,
    system_prompt: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 800,
) -> dict[str, Any]:
    api_key = get_secret("OPENROUTER_API_KEY")
    model = get_secret("OPENROUTER_MODEL", default=DEFAULT_OPENROUTER_MODEL)

    if not api_key:
        return _fallback_result(
            "fallback_missing_key",
            "OpenRouter 키가 설정되지 않아 로컬 fallback 답변을 사용합니다.",
            "missing_key",
        )

    try:
        from openai import OpenAI
    except Exception:
        return _fallback_result(
            "fallback_sdk_import_error",
            "OpenAI SDK를 불러오지 못해 로컬 fallback 답변을 사용합니다.",
            "sdk_import_error",
        )

    try:
        client = OpenAI(api_key=str(api_key), base_url=OPENROUTER_BASE_URL, timeout=20.0)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        completion = client.chat.completions.create(
            model=str(model),
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        text = completion.choices[0].message.content or ""
        return {
            "ok": True,
            "source": "openrouter",
            "text": sanitize_public_claims(text),
            "model": str(model),
        }
    except Exception as exc:
        reason = _classify_exception(exc)
        return _fallback_result(
            f"fallback_{reason}",
            "OpenRouter 호출에 실패해 로컬 fallback 답변을 사용합니다.",
            reason,
        )


def _template_rag_answer(question: str, context: str) -> str:
    if not context or context == "검색된 문서 근거가 없습니다.":
        return sanitize_public_claims(
            "현재 등록된 문서에서 확인되지 않습니다.\n\n"
            f"{LATEST_NOTICE}"
        )

    return sanitize_public_claims(
        "현재 등록된 문서 근거 기준의 참고 답변입니다.\n\n"
        f"질문: {question}\n\n"
        f"{context[:1800]}\n\n"
        f"{LATEST_NOTICE}"
    )


def generate_rag_answer(question: str, context: str) -> dict[str, Any]:
    disclaimer = get_disclaimer("general")
    prompt = (
        f"{disclaimer}\n\n"
        f"질문:\n{question}\n\n"
        f"docs 근거:\n{context}\n\n"
        "근거에 없는 내용은 추정하지 말고 확인되지 않는다고 답한다."
    )

    result = generate_with_openrouter(
        prompt=prompt,
        system_prompt=RAG_SYSTEM_PROMPT,
        temperature=0.2,
        max_tokens=800,
    )

    if result.get("ok"):
        result["text"] = sanitize_public_claims(_append_latest_notice(str(result.get("text", ""))))
        return result

    return {
        "ok": False,
        "source": result.get("source", "fallback"),
        "text": _template_rag_answer(question, context),
        "reason": result.get("reason", ""),
    }


def fallback_answer(question: str, context: str = "") -> str:
    return _template_rag_answer(question, context)


def fallback_rag_answer(question: str, context: str = "") -> dict[str, Any]:
    return {
        "ok": False,
        "source": "fallback_template",
        "text": _template_rag_answer(question, context),
        "reason": "local_fallback",
    }


def generate_openrouter_answer(question: str, context: str = "") -> tuple[str, dict[str, Any]]:
    """Backward-compatible wrapper from the earlier project skeleton."""
    result = generate_rag_answer(question, context)
    return result["text"], {"mode": result.get("source", "fallback"), "reason": result.get("reason", "")}
