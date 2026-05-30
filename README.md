# 김포시 반다비 AI Net Streamlit

김포시 반다비 AI Net 파일럿 서비스용 Streamlit 멀티페이지 앱입니다. 공공서비스, 모빌리티, 생활체육 참여 지원, RAG 문서 검색, optional LLM, 비전 검토, 이메일 초안 기능을 fallback 우선 구조로 제공합니다.

## 주요 기능

- 이용자 경로 참고 분석 및 Viable Path Scoring AI
- 교통약자 이동지원 후보 추천과 운영기관 검토 자료 정리
- 김포반다비센터 생활체육 리포트 생성
- Markdown 문서 기반 BM25 RAG 질문 테스트
- OpenRouter 기반 optional 답변 개선
- 이미지 업로드 기반 AI 임시 검토
- 관리자 검증용 공문 초안 및 SendGrid optional 발송
- B2G 파일럿 대시보드 예시
- 음성 명령 텍스트 fallback 및 브라우저 TTS optional

## 폴더 구조

```text
app.py
requirements.txt
README.md
.gitignore

.streamlit/
  config.toml
  secrets.toml.example

pages/
  01_이용자_경로분석.py
  02_이동지원_추천.py
  03_생활체육_리포트.py
  04_AI_비전검증.py
  05_B2G_대시보드.py
  06_공문_초안_이메일.py

modules/
  config.py
  safety.py
  ui_components.py
  data_loader.py
  api_clients.py
  scoring.py
  rag_bm25.py
  llm_client.py
  voice.py
  vision.py
  emailer.py
```

## 로컬 실행

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Streamlit Community Cloud 배포

1. GitHub public repository에 프로젝트를 올립니다.
2. Streamlit Community Cloud에서 repository와 `app.py`를 선택합니다.
3. 필요한 경우 App settings의 Secrets에 키 이름만 맞춰 값을 등록합니다.
4. `docs/`와 `data/`는 없어도 앱은 실행됩니다.

## Public Repo 보안

- 실제 API 키는 코드, README, GitHub에 포함하지 않습니다.
- 키는 `st.secrets` 또는 환경변수에서만 읽습니다.
- 로컬 비밀 파일은 Git 추적 대상에서 제외합니다.
- `.streamlit/secrets.toml.example`에는 키 이름만 둡니다.

## Secrets 설정

`.streamlit/secrets.toml.example`를 참고해 Streamlit Cloud Secrets 또는 환경변수에 필요한 항목만 설정합니다. 예시 파일에는 실제 값을 넣지 않습니다.

필요한 키 이름:
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `OPENAI_API_KEY`
- `HF_TOKEN`
- `VWORLD_API_KEY`
- `DATA_GO_KR_SERVICE_KEY`
- `SENDGRID_API_KEY`
- `EMAIL_ADDRESS`
- `ENABLE_SENDGRID_SEND`
- `VISION_MODEL`

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

## Fallback 동작

- OpenRouter 키가 없어도 BM25 검색과 템플릿 답변은 동작합니다.
- VWorld 키가 없어도 mock 좌표로 참고 위치를 표시합니다.
- SendGrid 설정이 없으면 발송 버튼이 비활성화됩니다.
- Vision 설정이 없으면 demo fallback 검토 결과를 표시합니다.
- 음성 컴포넌트가 없으면 텍스트 명령 입력으로 대체합니다.

## 안전 표현 원칙

- 실행 완료, 공식 처리 완료, 건강 관련 최종 결정으로 오해될 표현은 사용하지 않습니다.
- 결과는 후보 추천, 검토 요청, 참고 분석, 관리자 검증용 초안, 지도자 확인 필요 표현으로 제한합니다.
- AI 검출 결과는 공식 자료가 아니며 관리자 확인이 필요합니다.

## 현재 한계

- 지도는 참고 위치 표시이며 실제 이동 경로 계산이 아닙니다.
- B2G 지표는 파일럿 예시이며 실제 운영 통계가 아닙니다.
- 생활체육 리포트는 참여 지원 참고 정보이며 지도자 확인이 필요합니다.
- 비전검증은 임시 검토이며 현장 확인을 대체하지 않습니다.
