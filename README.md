# Streamlit 포트폴리오 프로젝트

이 프로젝트는 Streamlit을 사용하여 만든 개인 포트폴리오 웹사이트입니다. LangChain과 OpenAI API를 활용한 포트폴리오 챗봇이 포함되어 있어, 업로드된 PDF를 기반으로 대화형 질의응답이 가능합니다.

## 프로젝트 구조

```
portfolio-streamlit-codex/
├── app.py                  # 메인 Streamlit 애플리케이션
├── portfolio_chatbot.py    # LangChain 기반 챗봇 로직
├── assets/
│   ├── portfolio.pdf       # 전체 포트폴리오 챗봇에 사용하는 PDF (샘플)
│   └── projects/           # 프로젝트별 RAG 대화를 위한 PDF 디렉터리 (id.pdf 규칙)
├── requirements.txt        # 필요한 Python 패키지
├── README.md               # 프로젝트 설명서
├── app_simple.py           # 단순화된 예시 앱
├── run_portfolio.py        # 앱 실행 스크립트 예시
└── portfolio_data.py       # (선택사항) 데이터 구조 예시
```

## 설치 및 실행

### 1. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 OpenAI API 키를 저장합니다. 애플리케이션은 실행 시 `.env` 파일을 자동으로 로드합니다.

```
OPENAI_API_KEY=sk-...
```

### 3. 애플리케이션 실행

```bash
streamlit run app.py
```

또는

```bash
python -m streamlit run app.py
```

### 3. 브라우저에서 확인

애플리케이션이 실행되면 자동으로 브라우저가 열리며, `http://localhost:8501`에서 포트폴리오를 확인할 수 있습니다.

## 포트폴리오 구성

### 📄 페이지 구성

1. **🏠 홈** - 환영 메시지, 주요 경력, 대표 프로젝트 요약
2. **👤 소개** - `portfolio_data.json`의 소개/경력 정보를 구조화해 표시
3. **💼 프로젝트** - JSON 프로젝트 정보를 회사별 필터와 함께 제공
4. **🛠️ 기술 스택** - JSON 숙련도 값을 시각화하여 표시
5. **📞 연락처** - 연락처 및 소셜 미디어
6. **🤖 챗봇** - 포트폴리오 PDF 기반 질의응답

### 🎨 주요 기능

- **반응형 디자인**: 모든 디바이스에서 최적화
- **인터랙티브 차트**: Plotly를 사용한 데이터 시각화
- **다중 페이지**: 사이드바 네비게이션
- **연락 폼**: 방문자 메시지 수신
- **JSON 기반 화면 구성**: 홈, 소개, 프로젝트, 기술 스택 페이지가 `portfolio_data.json`을 실시간으로 반영
- **프로젝트 필터링**: 회사별 프로젝트 보기 및 목표/성과 요약 제공
- **LangChain 챗봇**: MultiQueryRetriever와 FAISS를 활용한 포트폴리오 질의응답
- **프로젝트별 RAG 챗봇**: `assets/projects/<프로젝트 ID>.pdf`와 매칭되어 프로젝트 확장 패널에서 바로 대화
- **빠른 홈 이동 버튼**: 모든 페이지 상단에서 홈으로 즉시 이동할 수 있는 네비게이션 버튼 제공

### 🗂 데이터 관리

- 홈 화면은 `portfolio_data.json` 파일의 내용을 기반으로 개인 소개, 경력, 대표 프로젝트를 동적으로 렌더링합니다.
- 소개 페이지는 `about`, `personal_info`, `experience` 섹션을 활용하여 관심사, 강점, 교육, 경력을 자동으로 보여줍니다.
- 프로젝트 페이지는 JSON의 `projects` 배열을 회사별 필터와 함께 렌더링하며, `tech_stack`/`teck_stack` 필드를 모두 인식합니다.
- 기술 스택 페이지는 언어/프레임워크/도구 숙련도를 시각화하고, 한국어 숙련도 표기를 점수로 변환해 차트를 생성합니다.
- 연락처 페이지는 동일한 JSON 데이터를 참조하여 이메일, 전화번호, 소셜 링크를 표시합니다.
- JSON 필드를 수정하면 앱을 재실행하지 않아도 Streamlit의 자동 새로고침을 통해 최신 정보가 즉시 반영됩니다.

## LangChain 기반 챗봇 사용법

1. **포트폴리오 PDF 교체**: `assets/portfolio.pdf` 파일을 자신의 최신 포트폴리오 PDF로 교체합니다.
2. **OpenAI API Key 설정**: `.env` 파일 또는 시스템 환경 변수에 `OPENAI_API_KEY`를 설정합니다. 애플리케이션은 실행 시 `.env` 파일을 자동으로 로드합니다.
3. **애플리케이션 실행**: 위 설치 절차에 따라 앱을 실행합니다.
4. **챗봇 페이지 이동**: 사이드바에서 `🤖 챗봇` 페이지를 선택한 뒤 질문을 입력하면, LangChain `MultiQueryRetriever`와 `faiss-cpu` 벡터 DB, OpenAI `text-embedding-3-small` 임베딩 모델, `gpt-5-mini` 챗 모델을 사용해 답변을 생성합니다.
5. **참고 문맥 확인**: 답변 하단의 "🔍 참고한 문맥 보기"에서 사용된 문서 조각을 확인할 수 있습니다.

### 프로젝트별 RAG 챗봇 사용

1. `portfolio_data.json`의 각 프로젝트 객체에 포함된 `id` 값을 확인합니다.
2. `assets/projects` 디렉터리에 `<id>.pdf` 형식으로 프로젝트 상세 문서를 저장합니다.
3. 앱 실행 후 `💼 프로젝트` 페이지에서 원하는 프로젝트의 확장 패널을 열고 `🤖 프로젝트 챗봇 열기` 버튼을 누릅니다.
4. 프로젝트 전용 대화 입력창을 통해 해당 PDF 기반의 RAG 질의응답을 수행하고, 필요하면 "🔍 참고한 문맥 보기"에서 근거를 확인합니다.

## 커스터마이징

### 페이지 콘텐츠 수정

- `portfolio_data.json`을 수정하면 홈/소개/프로젝트/기술 스택/연락처 페이지의 콘텐츠가 즉시 반영됩니다.
- `app.py`의 각 `render_*` 함수는 JSON 구조에 맞춰 작성되어 있으며, 맞춤형 섹션을 추가하려면 해당 함수의 로직을 확장하면 됩니다.
- 챗봇 프롬프트나 검색 전략을 조정하려면 `portfolio_chatbot.py` 내부 로직을 수정하세요.

### 스타일 변경

- Streamlit 컴포넌트 스타일은 `st.markdown`과 CSS를 활용해 조정할 수 있습니다.

## 배포

### Streamlit Cloud

1. GitHub에 코드 푸시
2. [Streamlit Cloud](https://streamlit.io/cloud)에서 배포
3. 자동으로 웹사이트가 생성됩니다

### Heroku

1. `runtime.txt` 파일 추가 (Python 버전 지정)
2. `setup.sh` 및 `Procfile` 추가
3. Heroku에 배포

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
```

## 개발 환경

- Python 3.8+
- Streamlit 1.28+
- Pandas 2.0+
- Plotly 5.15+
- LangChain 0.1+
- FAISS CPU 1.7+

## 라이선스

MIT License

## 기여

1. 프로젝트 포크
2. 기능 브랜치 생성 (`git checkout -b feature/amazing-feature`)
3. 변경사항 커밋 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 푸시 (`git push origin feature/amazing-feature`)
5. Pull Request 생성

## 문의

- 이메일: lms46784678@gmail.com
- GitHub: [@Themath93](https://github.com/Themath93)

---

⭐ 이 프로젝트가 도움이 되었다면 스타를 눌러주세요!
