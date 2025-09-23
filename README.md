# Streamlit 포트폴리오 프로젝트

이 프로젝트는 Streamlit을 사용하여 만든 개인 포트폴리오 웹사이트입니다.

## 프로젝트 구조

```
portfolio-streamlit-codex/
├── app.py                  # 메인 Streamlit 애플리케이션
├── portfolio_data.py       # 포트폴리오 데이터 및 기본 구조
├── requirements.txt        # 필요한 Python 패키지
├── README.md              # 프로젝트 설명서
├── .gitignore             # Git 무시 파일
└── pages/                 # (선택사항) 추가 페이지들
    ├── 01_About.py
    ├── 02_Projects.py
    ├── 03_Skills.py
    └── 04_Contact.py
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

### 🎨 주요 기능

- **반응형 디자인**: 모든 디바이스에서 최적화
- **인터랙티브 차트**: Plotly를 사용한 데이터 시각화
- **다중 페이지**: 사이드바 네비게이션
- **연락 폼**: 방문자 메시지 수신
- **프로젝트 필터링**: 카테고리별 프로젝트 보기

## 커스터마이징

### 개인 정보 수정

`portfolio_data.py` 파일을 편집하여 개인 정보를 업데이트할 수 있습니다:

```python
portfolio_data = {
    "personal_info": {
        "name": "귀하의 이름",
        "title": "귀하의 직책",
        "email": "귀하의 이메일",
        # ...
    }
    # ...
}
```

### 프로젝트 추가

`portfolio_data.py`의 `projects` 배열에 새로운 프로젝트를 추가:

```python
{
    "title": "새로운 프로젝트",
    "type": "프로젝트 유형",
    "description": "프로젝트 설명",
    "tech_stack": ["기술1", "기술2"],
    "github": "GitHub 링크",
    "demo": "데모 링크"
}
```

### 스타일 변경

`app.py`에서 Streamlit의 CSS를 수정하여 스타일을 변경할 수 있습니다.

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
