# Streamlit 포트폴리오 프로젝트

이 프로젝트는 Streamlit을 사용하여 만든 개인 포트폴리오 웹사이트입니다. LangChain과 OpenAI API를 활용한 포트폴리오 챗봇이 포함되어 있어, 업로드된 PDF를 기반으로 대화형 질의응답이 가능합니다.

## 프로젝트 구조

```
portfolio-streamlit-codex/
├── app.py                  # 메인 Streamlit 애플리케이션
├── portfolio_chatbot.py    # LangChain 기반 챗봇 로직
├── assets/
│   └── portfolio.pdf       # 챗봇 학습에 사용하는 포트폴리오 PDF (샘플)
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

### 2. 애플리케이션 실행

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

1. **🏠 홈** - 환영 메시지 및 개요
2. **👤 소개** - 개인 정보 및 경력
3. **💼 프로젝트** - 수행한 프로젝트들
4. **🛠️ 기술 스택** - 보유 기술 및 숙련도
5. **📞 연락처** - 연락처 및 소셜 미디어
6. **🤖 챗봇** - 포트폴리오 PDF 기반 질의응답

### 🎨 주요 기능

- **반응형 디자인**: 모든 디바이스에서 최적화
- **인터랙티브 차트**: Plotly를 사용한 데이터 시각화
- **다중 페이지**: 사이드바 네비게이션
- **연락 폼**: 방문자 메시지 수신
- **프로젝트 필터링**: 카테고리별 프로젝트 보기
- **LangChain 챗봇**: MultiQueryRetriever와 FAISS를 활용한 포트폴리오 질의응답

## LangChain 기반 챗봇 사용법

1. **포트폴리오 PDF 교체**: `assets/portfolio.pdf` 파일을 자신의 최신 포트폴리오 PDF로 교체합니다.
2. **OpenAI API Key 설정**:
   - 환경 변수 `OPENAI_API_KEY`를 설정하거나,
   - 앱 실행 후 사이드바에서 API 키를 직접 입력합니다.
3. **애플리케이션 실행**: 위 설치 절차에 따라 앱을 실행합니다.
4. **챗봇 페이지 이동**: 사이드바에서 `🤖 챗봇` 페이지를 선택한 뒤 질문을 입력하면, LangChain `MultiQueryRetriever`와 `faiss-cpu` 벡터 DB, OpenAI `text-embedding-3-small` 임베딩 모델, `gpt-5-mini` 챗 모델을 사용해 답변을 생성합니다.
5. **참고 문맥 확인**: 답변 하단의 "🔍 참고한 문맥 보기"에서 사용된 문서 조각을 확인할 수 있습니다.

## 커스터마이징

### 페이지 콘텐츠 수정

- `app.py`의 각 `render_*` 함수에서 텍스트, 차트, 표 데이터를 변경하여 페이지 내용을 자유롭게 수정할 수 있습니다.
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

- 이메일: your.email@example.com
- GitHub: [@yourusername](https://github.com/yourusername)
- LinkedIn: [Your Name](https://linkedin.com/in/yourusername)

---

⭐ 이 프로젝트가 도움이 되었다면 스타를 눌러주세요!
