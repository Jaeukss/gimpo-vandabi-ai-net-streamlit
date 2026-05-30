"""Optional accessibility image analysis with demo fallback."""

from __future__ import annotations

import base64
from typing import Any

from modules.config import get_secret
from modules.llm_client import OPENROUTER_BASE_URL
from modules.safety import sanitize_public_claims


VISION_NOTICE = (
    "AI 검출 결과는 공식 민원 또는 행정처분 자료가 아닙니다. "
    "관리자 검증, 개인정보 마스킹, 담당 공무원 확인 후 공식 절차로 전환될 수 있습니다."
)


def mask_notice() -> str:
    return sanitize_public_claims("사람 얼굴, 차량번호, 연락처, 주소 상세정보 등 개인정보 마스킹 필요 여부를 관리자 확인 단계에서 점검해야 합니다.")


def vision_status() -> dict[str, str | bool]:
    api_key = get_secret("OPENROUTER_API_KEY")
    model = get_secret("VISION_MODEL")
    if api_key and model:
        return {"configured": True, "data_status": "configured", "message": "비전 모델 설정이 감지되었습니다."}
    if api_key:
        return {"configured": False, "data_status": "missing_model", "message": "VISION_MODEL 설정이 없어 demo fallback을 사용합니다."}
    return {"configured": False, "data_status": "missing_key", "message": "비전 모델 키가 없어 demo fallback을 사용합니다."}


def demo_vision_fallback(report_type: str, description: str = "") -> dict[str, Any]:
    report = report_type or "기타"
    lowered = f"{report} {description}".lower()
    risk_level = "중간"
    if any(term in lowered for term in ("장애물", "화장실", "경사로")):
        risk_level = "높음"
    elif "표지" in lowered:
        risk_level = "중간"
    else:
        risk_level = "낮음"

    detected_items = [sanitize_public_claims(report)]
    if description:
        detected_items.append(sanitize_public_claims("사용자 설명 기반 확인 항목 포함"))

    return {
        "ok": False,
        "risk_level": risk_level,
        "detected_items": detected_items,
        "review_required": True,
        "privacy_masking_required": True,
        "recommended_next_step": sanitize_public_claims("관리자 검증 후 담당 부서 확인 자료로 정리"),
        "notice": sanitize_public_claims(VISION_NOTICE),
        "mask_notice": mask_notice(),
        "source": "demo_fallback",
    }


def analyze_accessibility_image(image_bytes: bytes | None, report_type: str, description: str = "") -> dict[str, Any]:
    api_key = get_secret("OPENROUTER_API_KEY")
    model = get_secret("VISION_MODEL")

    if not api_key:
        result = demo_vision_fallback(report_type, description)
        result["source"] = "missing_key"
        return result

    if not model:
        return demo_vision_fallback(report_type, description)

    if not image_bytes:
        return demo_vision_fallback(report_type, description)

    try:
        from openai import OpenAI

        image_b64 = base64.b64encode(image_bytes).decode("ascii")
        client = OpenAI(api_key=str(api_key), base_url=OPENROUTER_BASE_URL, timeout=20.0)
        completion = client.chat.completions.create(
            model=str(model),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "접근성 이미지 임시 검토를 수행한다. 공식 판단으로 단정하지 않는다. "
                        "개인정보 마스킹 필요 여부와 관리자 확인 필요 여부를 포함한다."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"제보 유형: {report_type}\n설명: {description}\n"
                                "risk_level, detected_items, review_required, recommended_next_step을 한국어로 요약."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                        },
                    ],
                },
            ],
            temperature=0.1,
            max_tokens=500,
        )
        text = sanitize_public_claims(completion.choices[0].message.content or "")
        return {
            "ok": True,
            "risk_level": "관리자 확인 필요",
            "detected_items": [text],
            "review_required": True,
            "privacy_masking_required": True,
            "recommended_next_step": sanitize_public_claims("관리자 검증 후 담당 부서 확인 자료로 정리"),
            "notice": sanitize_public_claims(VISION_NOTICE),
            "mask_notice": mask_notice(),
            "source": "vision_model",
        }
    except Exception:
        return demo_vision_fallback(report_type, description)


def summarize_image_upload(filename: str | None, size: int | None = None) -> dict[str, str | int | None]:
    return {
        "filename": sanitize_public_claims(filename or ""),
        "size": size,
        "status": "업로드 확인",
        "note": sanitize_public_claims("AI 비전검증은 optional 기능이며 실패 시 demo fallback을 사용합니다."),
    }
