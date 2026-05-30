# 김포 반다비 AI Net Streamlit Manifest

이 문서는 공개 저장소 기준으로 주요 폴더와 파일 역할을 설명한다. 실제 비밀키 파일은 포함하지 않는다.

## 루트 파일

- `app.py`: Streamlit 랜딩 화면, RAG 질문 테스트, 시연 안내 진입점.
- `requirements.txt`: Streamlit Cloud와 로컬 실행용 Python 의존성.
- `README.md`: 실행 방법, 배포 방법, 시연 동선, 보안 주의, 현재 한계.
- `.gitignore`: 로컬 비밀 파일, 캐시, 에디터 파일 제외 규칙.

## `.streamlit/`

- `config.toml`: Streamlit 테마와 기본 실행 설정.
- `secrets.toml.example`: Secrets 키 이름만 담은 예시 파일.
- `.streamlit/secrets.toml`은 저장소에 포함하지 않는다.

## `pages/`

Streamlit 기본 멀티페이지 화면 6개를 담는다.

- `01_이용자_경로분석.py`: 참고 지도와 Viable Path Scoring AI.
- `02_이동지원_추천.py`: 이동지원 후보 추천과 운영기관 검토 안내.
- `03_생활체육_리포트.py`: 생활체육 참여 참고 리포트.
- `04_AI_비전검증.py`: 이미지 기반 AI 임시 검토.
- `05_B2G_대시보드.py`: 파일럿 운영 참고 대시보드.
- `06_공문_초안_이메일.py`: 관리자 검증용 공문 초안과 이메일 발송 안전장치.

## `modules/`

공통 기능 모듈을 담는다.

- `config.py`: Streamlit Secrets 또는 환경변수 읽기.
- `safety.py`: 금지 표현 치환, 안전 고지, public claim 정리.
- `ui_components.py`: 공통 카드, 배지, 히어로, 안내 박스 UI.
- `data_loader.py`: CSV 탐색, 안전 로딩, mock fallback.
- `api_clients.py`: VWorld geocode와 외부 API stub/fallback.
- `scoring.py`: Viable Path Scoring AI rule-based 계산.
- `rag_bm25.py`: docs Markdown/TXT 기반 BM25 RAG.
- `llm_client.py`: OpenRouter optional 호출과 fallback 답변.
- `voice.py`: 음성 명령 optional UI와 텍스트 fallback.
- `vision.py`: 이미지 AI 임시 검토와 demo fallback.
- `emailer.py`: 관리자 검증용 초안과 SendGrid 안전장치.

## `docs/`

BM25 RAG 검색 대상 문서 폴더다.

- `.md`, `.md.md`, `.txt` 파일을 읽는다.
- 실제 서비스 문서 기반 검색 근거로 사용한다.
- 문서가 없어도 앱은 `empty_docs` fallback 상태로 실행된다.

## `data/`

김포 관련 CSV 데이터를 담는다.

- 교통약자 이동지원센터 CSV
- 노인장애인보호구역 CSV
- 저상버스 관련 CSV
- CSV가 없거나 읽기 실패해도 mock fallback으로 앱 실행을 유지한다.

## `references/`

이전 RAG/Streamlit 참고자료를 보관한다.

- 구조와 안전 패턴 참고용이다.
- 그대로 복붙하지 않고 현재 프로젝트 구조에 맞게 재해석한다.
- 실제 키 또는 로컬 secrets 자료는 포함하지 않는다.

## `prompts/`

개발 프롬프트나 추가 지시문을 둘 수 있는 선택 폴더다.

- 폴더가 없어도 앱 실행에는 영향이 없다.
- 실제 API 키나 로컬 비밀 파일을 넣지 않는다.

## 포함하지 않는 파일

- `api_key*`
- `.env`
- `.env.local`
- `.streamlit/secrets.toml`
- 실제 API 키 값
- 로컬 캐시와 벡터 인덱스
