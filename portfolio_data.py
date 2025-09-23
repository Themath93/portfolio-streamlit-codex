import json
from datetime import datetime

# 간단한 포트폴리오 앱 (외부 라이브러리 없는 버전)
def create_basic_portfolio():
    """
    외부 라이브러리가 설치되지 않은 경우를 위한 기본 포트폴리오 구조
    """
    print("=== 포트폴리오 기본 구조 ===")
    print("이 프로젝트는 Streamlit 기반 포트폴리오 웹사이트입니다.")
    print()
    
    # 포트폴리오 데이터 구조
    portfolio_data = {
        "personal_info": {
            "name": "개발자 이름",
            "title": "풀스택 개발자",
            "email": "your.email@example.com",
            "phone": "+82-10-1234-5678",
            "location": "서울, 대한민국"
        },
        "about": {
            "description": "웹 개발과 데이터 분석에 열정을 가진 풀스택 개발자입니다.",
            "interests": ["웹 개발", "데이터 사이언스", "클라우드", "AI/ML"],
            "education": "컴퓨터공학 학사 (2020-2024)",
            "strengths": ["문제 해결 능력", "팀워크 및 협업", "새로운 기술 학습", "창의적 사고"]
        },
        "projects": [
            {
                "title": "E-커머스 웹사이트",
                "type": "웹 개발",
                "description": "React와 Django를 사용한 온라인 쇼핑몰",
                "tech_stack": ["React", "Django", "PostgreSQL", "AWS"],
                "github": "https://github.com/example/project1",
                "demo": "https://example.com"
            },
            {
                "title": "데이터 시각화 대시보드",
                "type": "데이터 분석",
                "description": "Streamlit을 사용한 인터랙티브 대시보드",
                "tech_stack": ["Python", "Streamlit", "Plotly", "Pandas"],
                "github": "https://github.com/example/project2",
                "demo": "https://example.com"
            },
            {
                "title": "머신러닝 예측 모델",
                "type": "AI/ML",
                "description": "부동산 가격 예측 모델",
                "tech_stack": ["Python", "Scikit-learn", "Jupyter", "Matplotlib"],
                "github": "https://github.com/example/project3",
                "demo": None
            }
        ],
        "skills": {
            "languages": {
                "Python": 90,
                "JavaScript": 85,
                "Java": 75,
                "SQL": 80
            },
            "frameworks": {
                "React": 80,
                "Django": 85,
                "Flask": 70,
                "Streamlit": 90,
                "Pandas": 85
            },
            "tools": {
                "Git": 85,
                "Docker": 70,
                "AWS": 65,
                "PostgreSQL": 80
            }
        },
        "experience": [
            {"year": 2022, "event": "Python 학습 시작"},
            {"year": 2023, "event": "웹 개발 프로젝트"},
            {"year": 2024, "event": "AI/ML 프로젝트"}
        ],
        "social_links": {
            "github": "https://github.com/yourusername",
            "linkedin": "https://linkedin.com/in/yourusername",
            "blog": "https://yourblog.com",
            "instagram": "https://instagram.com/yourusername"
        }
    }
    
    return portfolio_data

def print_portfolio_structure():
    """포트폴리오 구조 출력"""
    data = create_basic_portfolio()
    
    print("1. 개인 정보:")
    for key, value in data["personal_info"].items():
        print(f"   - {key}: {value}")
    
    print("\n2. 프로젝트:")
    for i, project in enumerate(data["projects"], 1):
        print(f"   {i}. {project['title']} ({project['type']})")
        print(f"      설명: {project['description']}")
        print(f"      기술: {', '.join(project['tech_stack'])}")
    
    print("\n3. 기술 스택:")
    for category, skills in data["skills"].items():
        print(f"   {category}:")
        for skill, level in skills.items():
            print(f"      - {skill}: {level}%")
    
    print(f"\n마지막 업데이트: {datetime.now().strftime('%Y년 %m월 %d일')}")

if __name__ == "__main__":
    print_portfolio_structure()

# 포트폴리오 데이터를 JSON 파일로 저장
def save_portfolio_data():
    data = create_basic_portfolio()
    with open('portfolio_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("포트폴리오 데이터가 portfolio_data.json에 저장되었습니다.")

if __name__ == "__main__":
    save_portfolio_data()