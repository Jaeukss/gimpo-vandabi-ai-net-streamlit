# 김포 반다비 AI Net 파일럿

교통약자 이동지원, 생활체육 참여, 접근성 검증, 공공데이터 QA를 하나의 흐름으로 묶은 Streamlit 기반 AI 의사결정 보조 MVP입니다.

Repository: `gimpo-vandabi-ai-net-streamlit`

## 핵심 요약

- Streamlit 기본 멀티페이지 구조(`pages/`)를 사용합니다.
- RAG는 `docs/` Markdown/TXT 문서를 BM25로 검색합니다.
- OpenRouter는 검색기가 아니라 답변 생성과 문장 개선에만 사용합니다.
- VWorld는 장소명 검색과 주소 좌표 변환에 사용합니다.
- 공공데이터포털 API 7종은 `DATA_GO_KR_SERVICE_KEY` 하나로 분리 호출합니다.
- 음성, 비전, SendGrid는 optional 기능이며 실패해도 앱 실행을 유지합니다.
- GitHub public 저장소 기준으로 실제 키 파일과 키 값은 포함하지 않습니다.

## 주요 기능

| 기능 | 설명 |
|---|---|
| 이용자 경로분석 | 출발지와 목적지의 참고 지도, 0~100 접근성 참고 점수, 기상 API 상태를 표시합니다. |
| 이동지원 후보 추천 | 교통약자 이동지원 공공데이터와 RAG 근거를 참고해 운영기관 검토용 후보 정보를 정리합니다. |
| 생활체육 리포트 | 참여 기록, RAG 근거, 체육시설 API 참고 정보를 기반으로 생활체육 참여 리포트를 생성합니다. |
| BM25 RAG 챗봇 | `docs/` 문서를 검색하고 OpenRouter 또는 로컬 대체 답변을 반환합니다. |
| AI 비전검증 | 업로드 이미지를 AI 임시 검토 결과로 정리하고 개인정보 마스킹 필요 여부를 안내합니다. |
| 관리자 공문 초안 | 관리자 검증용 공문 초안을 만들고 SendGrid 발송 안전장치를 적용합니다. |
| B2G 대시보드 | Secrets, RAG, CSV, 외부 API, 공공데이터 7종 상태를 버튼 기반으로 점검합니다. |

## 페이지 구성

| 파일 | 화면 | 역할 |
|---|---|---|
| `app.py` | 랜딩 + RAG 테스트 | 프로젝트 안내, B2C/B2G 진입 안내, BM25 RAG 질문 테스트 |
| `pages/01_이용자_경로분석.py` | 이용자 경로분석 | 참고 지도, VWorld 좌표 변환, 기상 API, Viable Path Scoring AI |
| `pages/02_이동지원_추천.py` | 이동지원 후보 추천 | 교통약자 이동지원 참고 정보, RAG 근거, 운영기관 확인 안내 |
| `pages/03_생활체육_리포트.py` | 생활체육 리포트 | 프로그램별 참고 리포트, 체육시설 공공데이터, RAG 근거 |
| `pages/04_AI_비전검증.py` | AI 비전검증 | 이미지 업로드, 위험 요소 후보, 관리자 검토 안내 |
| `pages/05_B2G_대시보드.py` | B2G 운영 참고 대시보드 | Secrets QA, CSV/RAG 상태, 공공데이터 7종 상태 점검 |
| `pages/06_공문_초안_이메일.py` | 공문 초안 및 이메일 | 관리자 검증용 초안 생성, SendGrid 발송 차단/허용 조건 표시 |

## 폴더 구조

```text
.
├─ app.py
├─ requirements.txt
├─ README.md
├─ MANIFEST.md
├─ .streamlit/
│  ├─ config.toml
│  └─ secrets.toml.example
├─ pages/
│  ├─ 01_이용자_경로분석.py
│  ├─ 02_이동지원_추천.py
│  ├─ 03_생활체육_리포트.py
│  ├─ 04_AI_비전검증.py
│  ├─ 05_B2G_대시보드.py
│  └─ 06_공문_초안_이메일.py
├─ modules/
│  ├─ api_clients.py
│  ├─ config.py
│  ├─ data_loader.py
│  ├─ emailer.py
│  ├─ llm_client.py
│  ├─ rag_bm25.py
│  ├─ safety.py
│  ├─ scoring.py
│  ├─ ui_components.py
│  ├─ vision.py
│  └─ voice.py
├─ docs/
├─ data/
├─ references/
└─ prompts/
```

## 로컬 실행

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

앱 진입점은 `app.py`입니다. 내부 라우팅이 아니라 Streamlit 기본 멀티페이지 구조를 사용합니다.

## Streamlit Cloud 배포

Streamlit Cloud 설정값:

| 항목 | 값 |
|---|---|
| Repository | GitHub public repository |
| Branch | `main` |
| Main file path | `app.py` |
| Secrets | Streamlit Cloud App settings에서 입력 |

GitHub 저장소에는 `.streamlit/secrets.toml`을 올리지 않습니다. 배포 환경에서는 Streamlit Secrets 또는 환경변수만 사용합니다.

## Secrets 설정 예시

실제 키 값은 아래 예시에 넣지 않습니다. 운영 값은 Streamlit Cloud Secrets 또는 로컬 환경변수에만 설정합니다.

```toml
OPENROUTER_API_KEY = ""
OPENROUTER_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
VISION_MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
OPENAI_API_KEY = ""
HF_TOKEN = ""
VWORLD_API_KEY = ""
DATA_GO_KR_SERVICE_KEY = ""
SENDGRID_API_KEY = ""
EMAIL_ADDRESS = ""
ENABLE_SENDGRID_SEND = "false"
```

## 보안 원칙

- `api_key*`, `.env`, `.env.local`, `.streamlit/secrets.toml`은 저장소에 포함하지 않습니다.
- API 키는 `st.secrets` 또는 환경변수에서만 읽습니다.
- 실제 키 값, 일부 마스킹 키, 전체 요청 URL은 화면, 로그, README에 표시하지 않습니다.
- `ENABLE_SENDGRID_SEND` 기본값은 `false`입니다.
- SendGrid는 사용자가 확인 체크박스를 선택하고 설정이 모두 충족된 경우에만 전송을 시도합니다.

## 안전 고지

본 서비스는 이동지원 확정, 배차 확정, 공식 민원 접수, 의료 진단을 수행하지 않습니다. 결과는 공공데이터, RAG 문서, LLM 응답, 대체 응답 로직을 이용한 참고 정보입니다.

실제 이동지원, 시설 조치, 생활체육 강도 변경은 운영기관 또는 지도자 확인이 필요합니다. AI 검출 결과는 공식 민원 또는 행정처분 자료가 아니며 관리자 검증과 담당자 확인이 필요합니다.

## 공공데이터 API 7종

`DATA_GO_KR_SERVICE_KEY` 하나로 아래 API를 기능별로 분리 호출합니다. 전체 요청 URL과 키 값은 표시하지 않습니다.

| 구분 | 현재 처리 |
|---|---|
| 전국체육시설 정보 | `real_api` 확인 |
| 공공체육시설 상세 정보 | `real_api` 확인 |
| 장애인편의시설 현황 | `real_api` 확인 |
| 교통약자 이동지원 실시간 정보 | `real_api` 확인 |
| 기상청 단기예보 | `real_api` 확인 |
| TAGO 버스노선정보 | `real_api` 확인 |
| TAGO 버스도착정보 | `real_api_no_data` 가능 |

상태 의미:

| 상태 | 의미 |
|---|---|
| `real_api` | 실제 공공데이터 응답과 항목이 확인된 상태 |
| `real_api_no_data` | API 호출은 정상이나 현재 조건에 해당하는 데이터가 없는 상태 |
| `fallback` | 실API 성공이 아니라 앱 안정성을 위한 대체 응답 |
| `missing_key` | 필요한 Secret이 설정되지 않은 상태 |
| `api_error`, `timeout`, `network_error`, `parse_error` | 외부 API 응답 실패 또는 파싱 실패 상태 |

## VWorld 좌표 변환

VWorld는 장소명과 주소형 입력을 분리 처리합니다.

| 입력 유형 | 처리 방식 |
|---|---|
| 장소명, 건물명, 시설명 | VWorld Search API `type=PLACE` 우선 사용 |
| 도로명주소 | Address API `GetCoord` `ROAD` 사용 |
| 지번주소 | Address API `GetCoord` `PARCEL` 재시도 |
| 실패 또는 키 누락 | 시연용 대체 좌표 사용, `real_api`로 표시하지 않음 |

예시 입력:

- `운양역`
- `김포반다비체육센터`
- `경기도 김포시 사우중로 1`

## RAG 문서 사용법

`docs/` 폴더에 다음 확장자의 파일을 넣으면 BM25 검색 대상이 됩니다.

- `.md`
- `.md.md`
- `.txt`

문서가 없으면 `empty_docs` 상태로 표시되며 앱 실행은 유지됩니다. 읽기 실패 파일은 건너뜁니다.

## CSV 데이터 사용법

`data/*.csv`와 루트의 `*.csv`를 자동 탐색합니다.

인코딩은 다음 순서로 시도합니다.

1. `utf-8-sig`
2. `cp949`
3. `euc-kr`

CSV가 없거나 읽기 실패해도 안전 대체 데이터로 화면을 유지합니다.

## Optional 기능

| 기능 | 설정 | 실패 시 동작 |
|---|---|---|
| OpenRouter Text | `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` | 로컬 대체 답변 |
| OpenRouter Vision | `OPENROUTER_API_KEY`, `VISION_MODEL` | 시연용 대체 응답 |
| VWorld | `VWORLD_API_KEY` | 시연용 대체 좌표 |
| 공공데이터 | `DATA_GO_KR_SERVICE_KEY` | API별 상태 코드와 대체 응답 |
| SendGrid | `SENDGRID_API_KEY`, `EMAIL_ADDRESS`, `ENABLE_SENDGRID_SEND` | 기본 차단 |
| 음성 입력 | `streamlit-mic-recorder` | 텍스트 대체 입력 |

## 5분 시연 동선

1. 첫 화면에서 프로젝트 목적과 B2C/B2G 영역을 확인합니다.
2. `01 경로분석`에서 `운양역`과 `김포반다비체육센터`를 입력해 지도, 좌표 출처, 접근성 참고 점수를 확인합니다.
3. `02 이동지원 추천`에서 후보 추천과 운영기관 확인 안내를 확인합니다.
4. `05 B2G 대시보드`에서 공공데이터 7종 상태 점검 버튼을 눌러 `real_api`와 `real_api_no_data`를 구분합니다.
5. `06 공문 초안`에서 관리자 검증용 초안과 SendGrid 비활성 안전장치를 확인합니다.

## 10분 시연 동선

1. 첫 화면에서 RAG 문서 질문 테스트를 실행합니다.
2. `01 경로분석`에서 VWorld 장소 검색, 주소 변환, 기상 API 상태를 확인합니다.
3. `02 이동지원 추천`에서 교통약자 이동지원 공공데이터 참고 정보를 확인합니다.
4. `03 생활체육 리포트`에서 프로그램별 참고 리포트와 체육시설 정보를 확인합니다.
5. `04 AI 비전검증`에서 이미지를 업로드하고 AI 임시 검토 결과와 개인정보 마스킹 안내를 확인합니다.
6. `05 B2G 대시보드`에서 Secrets QA, CSV/RAG 상태, 공공데이터 7종 상태표, VWorld 장소명/주소 테스트를 확인합니다.
7. `06 공문 초안`에서 초안 생성 후 확인 체크박스와 `ENABLE_SENDGRID_SEND=false` 차단 상태를 확인합니다.

## 현재 한계

- 지도는 참고 위치 표시이며 실제 이동 경로 계산이 아닙니다.
- TAGO 버스도착정보는 실시간 데이터 특성상 현재 조건에 도착 예정 데이터가 없을 수 있습니다.
- 외부 API는 운영 상태나 응답 스키마 변경에 따라 대체 응답이 표시될 수 있습니다.
- 비전검증은 공식 판정이 아닌 관리자 검토 보조입니다.
- SendGrid 전송은 안전상 기본 비활성입니다.

## 향후 개선

- 실제 운영기관 검토 기준 반영
- 공공데이터 응답 스키마 변화 모니터링
- 접근성 현장 검증 데이터 보강
- 시연 로그 기반 QA 체크리스트 보강
- 배포 환경별 API 연결 상태 리포트 자동화
