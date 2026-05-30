# 김포 반다비 AI Net 파일럿

Streamlit 기반 AI 의사결정 보조 MVP입니다. 교통약자 이동지원, 생활체육 참여, 접근성 검증을 하나의 파일럿 서비스 동선으로 연결합니다.

## 한 줄 설명

교통약자 이동지원, 생활체육 참여, 접근성 검증을 연결하는 Streamlit 기반 AI 의사결정 보조 MVP.

## 핵심 기능

- 이용자 경로분석: 출발지와 목적지의 참고 좌표, 접근성 점수, 확인 필요 요인을 표시합니다.
- 이동지원 후보 추천: 특별교통수단과 대체수단 후보를 운영기관 검토용으로 정리합니다.
- 생활체육 리포트: 참여 기록과 RAG 근거를 바탕으로 지도자 확인용 참고 리포트를 생성합니다.
- AI 비전검증: 이미지 업로드 후 위험 요소 후보, 개인정보 마스킹 필요 여부, 관리자 검토 필요 여부를 정리합니다.
- B2G 운영 참고 대시보드: API, RAG, CSV, fallback 상태를 파일럿 점검용 KPI로 표시합니다.
- 공문 초안 및 이메일 발송 안전장치: 관리자 검증용 공문 초안을 만들고 SendGrid 발송 조건을 분리합니다.

## 페이지 구성

| 파일 | 화면 | 역할 |
|---|---|---|
| `pages/01_이용자_경로분석.py` | 이용자 경로분석 | 참고 지도, 접근성 점수, 확인 필요 요인 표시 |
| `pages/02_이동지원_추천.py` | 이동지원 후보 추천 | 후보 추천과 운영기관 검토 안내 |
| `pages/03_생활체육_리포트.py` | 생활체육 리포트 | 참여 기록 기반 참고 리포트 생성 |
| `pages/04_AI_비전검증.py` | AI 비전검증 | 이미지 기반 위험 요소 후보 정리 |
| `pages/05_B2G_대시보드.py` | B2G 운영 참고 대시보드 | 파일럿 상태, API/RAG/fallback 상태 점검 |
| `pages/06_공문_초안_이메일.py` | 공문 초안 및 이메일 | 관리자 검증용 초안 생성과 SendGrid 안전장치 |

## 로컬 실행 방법

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

## Streamlit Cloud 배포 방법

- Repository: GitHub 공개 저장소를 선택합니다.
- Branch: `main`
- Main file path: `app.py`
- Secrets: Streamlit Cloud의 App settings > Secrets에 입력합니다.
- GitHub repo에는 `.streamlit/secrets.toml`을 올리지 않습니다.

## Secrets 예시

실제 키 값은 넣지 말고 Streamlit Cloud Secrets 또는 로컬 환경변수에만 설정합니다.

```toml
OPENROUTER_API_KEY = ""
OPENROUTER_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
VISION_MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
VWORLD_API_KEY = ""
DATA_GO_KR_SERVICE_KEY = ""
SENDGRID_API_KEY = ""
EMAIL_ADDRESS = ""
ENABLE_SENDGRID_SEND = "false"
```

## 보안 주의

- `api_key*.txt` 업로드 금지
- `.env` 업로드 금지
- `.streamlit/secrets.toml` 업로드 금지
- 키는 Streamlit Secrets 또는 환경변수에서만 읽습니다.
- `ENABLE_SENDGRID_SEND`는 기본 `false` 권장입니다.
- 실제 키 값은 README, 코드, 로그, 화면에 표시하지 않습니다.

## 안전 고지

- 본 서비스는 이동지원 확정, 배차 확정, 공식 민원 접수, 의료 진단을 수행하지 않습니다.
- 결과는 공공데이터, RAG 문서, LLM 응답, fallback 로직을 이용한 참고 정보입니다.
- 실제 이동지원, 시설 조치, 생활체육 강도 변경은 운영기관 또는 지도자 확인이 필요합니다.
- AI 검출 결과는 공식 민원 또는 행정처분 자료가 아니며, 관리자 검증과 담당자 확인이 필요합니다.

## Demo Flow

1. 첫 화면에서 프로젝트 목적과 B2C/B2G 영역을 확인합니다.
2. `01 경로분석`에서 출발지/목적지를 입력한 뒤 지도와 접근성 점수를 확인합니다.
3. `02 이동지원 추천`에서 후보 추천과 운영기관 검토 안내를 확인합니다.
4. `03 생활체육 리포트`에서 프로그램과 참여 정보를 입력해 참고 리포트를 생성합니다.
5. `04 AI 비전검증`에서 이미지를 업로드하고 위험 요소 후보를 확인합니다.
6. `05 B2G 대시보드`에서 API/RAG/fallback 상태를 확인합니다.
7. `06 공문 초안`에서 관리자 검증용 초안을 생성하고 SendGrid 비활성 안전장치를 확인합니다.

## docs 사용법

- `docs/`에 `.md`, `.md.md`, `.txt` 파일을 넣으면 BM25 RAG 검색 대상이 됩니다.
- 문서가 없으면 `empty_docs` 상태와 fallback 답변이 표시됩니다.
- 읽기 실패 파일은 건너뛰고 앱 실행은 유지됩니다.

## data CSV 사용법

- `data/*.csv`와 루트의 `*.csv`를 자동 탐색합니다.
- 인코딩은 `utf-8-sig`, `cp949`, `euc-kr` 순서로 시도합니다.
- 읽기 실패 또는 파일 없음 상태에서는 mock fallback 데이터가 표시됩니다.

## Optional API

- OpenRouter: RAG 답변과 공문 초안 문장 개선에 사용합니다.
- VWorld: 주소 좌표 변환에 사용합니다.
- SendGrid: 사용자가 확인하고 설정이 모두 충족된 경우에만 초안 이메일 발송을 시도합니다.
- Vision 모델: 이미지 기반 AI 임시 검토에 사용합니다.

## 현재 한계

- 일부 공공데이터 API는 fallback 중심입니다.
- 실제 공공데이터 API 7개 endpoint별 실연동은 후속 단계입니다.
- 비전 분석은 공식 판정이 아닌 관리자 검토 보조입니다.
- SendGrid 발송은 안전상 기본 비활성입니다.
- 지도는 참고 위치 표시이며 실제 이동 경로 계산이 아닙니다.

## 향후 단계

- 8단계: 실제 Secrets 기반 기능별 QA
- 9단계: 공공데이터 API 7개 실연동
- 10단계: 최종 시연 안정화와 리스크 제거
