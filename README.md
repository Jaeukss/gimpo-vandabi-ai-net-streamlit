# 김포 반다비 AI Net 파일럿

교통약자 이동지원, 생활체육 참여, 접근성 검증을 연결하는 Streamlit 기반 AI 의사결정 보조 MVP입니다.

## 핵심 기능

- 이용자 경로분석: 출발지와 목적지 기준 참고 지도, 0~100 접근성 참고 점수, 기상 API 상태를 표시합니다.
- 이동지원 후보 추천: 공공데이터 API와 RAG 문서를 참고해 운영기관 검토용 후보 정보를 정리합니다.
- 생활체육 리포트: 참여 기록, RAG 근거, 공공체육시설 API 참고 정보를 바탕으로 지도자 확인용 참고 리포트를 생성합니다.
- AI 비전검증: 이미지 업로드 기반 위험 요소 후보, 개인정보 마스킹 필요 여부, 관리자 검토 필요 여부를 정리합니다.
- B2G 운영 참고 대시보드: Secrets, API, RAG, CSV, 공공데이터 7종 상태를 파일럿 점검용 KPI로 표시합니다.
- 공문 초안 및 이메일 안전장치: 관리자 검증용 공문 초안을 만들고 SendGrid 전송 조건을 분리합니다.

## 페이지 구성

| 파일 | 화면 | 역할 |
|---|---|---|
| `pages/01_이용자_경로분석.py` | 이용자 경로분석 | 참고 지도, 접근성 참고 점수, 기상 API 상태 |
| `pages/02_이동지원_추천.py` | 이동지원 후보 추천 | 후보 추천과 운영기관 검토 안내 |
| `pages/03_생활체육_리포트.py` | 생활체육 리포트 | 참여 기록 기반 참고 리포트 |
| `pages/04_AI_비전검증.py` | AI 비전검증 | 이미지 기반 위험 요소 후보 정리 |
| `pages/05_B2G_대시보드.py` | B2G 운영 참고 대시보드 | Secrets, RAG, CSV, 공공데이터 7종 버튼 기반 점검 |
| `pages/06_공문_초안_이메일.py` | 공문 초안 및 이메일 | 관리자 검증용 초안과 SendGrid 안전장치 |

## 로컬 실행

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

## Streamlit Cloud 배포

- Repository: GitHub 공개 저장소
- Branch: `main`
- Main file path: `app.py`
- Secrets: Streamlit Cloud의 App settings > Secrets에 입력
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
- `ENABLE_SENDGRID_SEND`는 기본 `false`를 권장합니다.
- 실제 키 값, 일부 마스킹 키, 전체 요청 URL은 README, 코드, 로그, 화면에 표시하지 않습니다.

## 안전 고지

- 본 서비스는 이동지원 확정, 배차 확정, 공식 민원 접수, 의료 진단을 수행하지 않습니다.
- 결과는 공공데이터, RAG 문서, LLM 응답, 대체 응답 로직을 이용한 참고 정보입니다.
- 실제 이동지원, 시설 조치, 생활체육 강도 변경은 운영기관 또는 지도자 확인이 필요합니다.
- AI 검출 결과는 공식 민원 또는 행정처분 자료가 아니며 관리자 검증과 담당자 확인이 필요합니다.

## 공공데이터 API 7종 실연동 상태

`DATA_GO_KR_SERVICE_KEY` 하나로 API별 operation path를 분리 호출합니다. 10단계 기준 시연 확인 상태는 다음과 같습니다.

- 전국체육시설 정보: `real_api` 확인
- 공공체육시설 상세 정보: `real_api` 확인
- 장애인편의시설 현황: `real_api` 확인
- 교통약자 이동지원 실시간 정보: `real_api` 확인
- 기상청 단기예보: `real_api` 확인
- TAGO 버스노선정보: `real_api` 확인
- TAGO 버스도착정보: `real_api_no_data` 가능

`real_api`는 실제 공공데이터 응답을 받은 상태입니다. `real_api_no_data`는 API 호출은 정상이나 현재 조건에 해당하는 데이터가 없는 상태입니다. `fallback`은 실API 성공이 아니라 앱 안정성을 위한 대체 응답입니다.

## 5분 시연 동선

1. 첫 화면에서 프로젝트 목적과 B2C/B2G 영역을 확인합니다.
2. `01 경로분석`에서 출발지와 목적지를 입력하고 지도, 접근성 참고 점수, 기상 API 상태를 확인합니다.
3. `02 이동지원 추천`에서 후보 추천과 운영기관 검토 안내를 확인합니다.
4. `05 B2G 대시보드`에서 공공데이터 7종 상태 점검 버튼을 눌러 `real_api`와 `real_api_no_data`를 구분 확인합니다.
5. `06 공문 초안`에서 관리자 검증용 초안과 SendGrid 비활성 안전장치를 확인합니다.

## 10분 시연 동선

1. 첫 화면에서 RAG 문서 질문 테스트를 실행합니다.
2. `01 경로분석`에서 VWorld 실패 시 시연용 대체 좌표 안내와 기상 API 상태를 확인합니다.
3. `02 이동지원 추천`에서 교통약자 이동지원 공공데이터 참고 정보를 확인합니다.
4. `03 생활체육 리포트`에서 프로그램별 참고 리포트와 공공체육시설 정보를 확인합니다.
5. `04 AI 비전검증`에서 이미지를 업로드하고 AI 임시 검토 결과, 개인정보 마스킹 안내를 확인합니다.
6. `05 B2G 대시보드`에서 Secrets QA, CSV/RAG 상태, 공공데이터 7종 상태표를 확인합니다.
7. `06 공문 초안`에서 초안 생성 후 확인 체크박스와 `ENABLE_SENDGRID_SEND=false` 차단 상태를 확인합니다.

## docs 사용법

- `docs/`에 `.md`, `.md.md`, `.txt` 파일을 넣으면 BM25 RAG 검색 대상이 됩니다.
- 문서가 없으면 `empty_docs` 또는 대체 응답 상태로 화면이 유지됩니다.
- 읽기 실패 파일은 건너뛰고 앱 실행은 유지됩니다.

## data CSV 사용법

- `data/*.csv`와 루트의 `*.csv`를 자동 탐색합니다.
- 인코딩은 `utf-8-sig`, `cp949`, `euc-kr` 순서로 시도합니다.
- 파일이 없거나 읽기 실패 상태에서도 안전 대체 데이터로 화면을 유지합니다.

## Optional API

- OpenRouter: RAG 답변과 공문 초안 문장 개선에 사용합니다.
- Vision 모델: 이미지 기반 AI 임시 검토에 사용합니다.
- VWorld: 주소 좌표 변환에 사용합니다.
- DATA_GO_KR_SERVICE_KEY: 공공데이터 API 7종 조회에 사용합니다.
- SendGrid: 사용자가 확인하고 설정이 모두 충족된 경우에만 이메일 전송을 시도합니다. 기본값은 disabled입니다.

## 현재 한계

- TAGO 버스도착정보는 실시간 데이터 특성상 현재 조건에 도착 예정 데이터가 없을 수 있습니다.
- 일부 API는 운영 상태나 응답 스키마 변경으로 대체 응답이 표시될 수 있습니다.
- 비전 분석은 공식 판정이 아닌 관리자 검토 보조입니다.
- SendGrid 전송은 안전상 기본 비활성입니다.
- 지도는 참고 위치 표시이며 실제 이동 경로 계산이 아닙니다.

## 향후 개선

- 시연 후 실제 운영기관 검토 항목 반영
- 공공데이터 응답 스키마 변화 모니터링
- 접근성 현장 검증 데이터 보강
- Streamlit Cloud 로그 기반 QA 체크리스트 보강
