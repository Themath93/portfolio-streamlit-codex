import streamlit as st
from datetime import datetime

# Try to import optional dependencies, fall back gracefully if not available
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# 페이지 설정
st.set_page_config(
    page_title="포트폴리오 - Portfolio",
    page_icon="👨‍💻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 포트폴리오 데이터
@st.cache_data
def get_portfolio_data():
    return {
        "personal_info": {
            "name": "개발자 이름",
            "title": "풀스택 개발자",
            "email": "your.email@example.com",
            "phone": "+82-10-1234-5678",
            "location": "서울, 대한민국"
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
            "languages": {"Python": 90, "JavaScript": 85, "Java": 75, "SQL": 80},
            "frameworks": {"React": 80, "Django": 85, "Flask": 70, "Streamlit": 90, "Pandas": 85},
            "tools": {"Git": 85, "Docker": 70, "AWS": 65, "PostgreSQL": 80}
        },
        "experience": [
            {"year": 2022, "event": "Python 학습 시작"},
            {"year": 2023, "event": "웹 개발 프로젝트"},
            {"year": 2024, "event": "AI/ML 프로젝트"}
        ]
    }

# 사이드바 네비게이션
st.sidebar.title("📂 Navigation")
page = st.sidebar.selectbox(
    "페이지를 선택하세요",
    ["🏠 홈", "👤 소개", "💼 프로젝트", "🛠️ 기술 스택", "📞 연락처"]
)

# 포트폴리오 데이터 로드
data = get_portfolio_data()

# 홈 페이지
if page == "🏠 홈":
    st.title("👋 안녕하세요! 저의 포트폴리오에 오신 것을 환영합니다")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## 🚀 개발자 포트폴리오
        
        이곳은 제가 작업한 프로젝트들과 기술 스택을 소개하는 공간입니다.
        왼쪽 사이드바를 통해 다양한 섹션을 탐색해보세요!
        
        ### ✨ 주요 특징
        - **반응형 웹 디자인**: 모든 디바이스에서 최적화된 경험
        - **인터랙티브 차트**: 데이터 시각화를 통한 직관적인 정보 전달
        - **실시간 업데이트**: 최신 프로젝트와 기술 스택 정보
        """)
        
        # 최근 업데이트 정보
        st.info(f"📅 마지막 업데이트: {datetime.now().strftime('%Y년 %m월 %d일')}")
    
    with col2:
        st.markdown("### 📊 Quick Stats")
        
        # 간단한 통계 정보
        stats_data = [
            ("프로젝트", len(data["projects"])),
            ("사용 언어", len(data["skills"]["languages"])),
            ("경력", "2년+")
        ]
        
        for item, count in stats_data:
            st.metric(item, count)

# 소개 페이지
elif page == "👤 소개":
    st.title("👤 About Me")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image("https://via.placeholder.com/300x300?text=Profile+Photo", 
                caption="프로필 사진", width=250)
    
    with col2:
        st.markdown(f"""
        ## 안녕하세요! 👋
        
        저는 **{data['personal_info']['title']}**로, 웹 개발과 데이터 분석에 열정을 가지고 있습니다.
        
        ### 🎯 관심 분야
        - **웹 개발**: React, Python, Django
        - **데이터 사이언스**: Python, Pandas, Matplotlib
        - **클라우드**: AWS, Docker
        - **AI/ML**: 머신러닝, 딥러닝
        
        ### 🎓 교육
        - 컴퓨터공학 학사 (2020-2024)
        - 각종 온라인 코스 수료
        
        ### 💪 강점
        - 문제 해결 능력
        - 팀워크 및 협업
        - 새로운 기술 학습 의욕
        - 창의적 사고
        
        ### 📍 연락처
        - 📧 {data['personal_info']['email']}
        - 📱 {data['personal_info']['phone']}
        - 📍 {data['personal_info']['location']}
        """)

# 프로젝트 페이지
elif page == "💼 프로젝트":
    st.title("💼 프로젝트 포트폴리오")
    
    # 프로젝트 필터
    project_types = ["전체"] + list(set([p["type"] for p in data["projects"]]))
    project_type = st.selectbox("프로젝트 유형", project_types)
    
    # 프로젝트 필터링
    projects = data["projects"]
    if project_type != "전체":
        projects = [p for p in projects if p["type"] == project_type]
    
    # 프로젝트 카드 표시
    for project in projects:
        with st.expander(f"📁 {project['title']}", expanded=True):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**설명**: {project['description']}")
                st.markdown(f"**카테고리**: {project['type']}")
                
                # 기술 스택 태그
                tech_tags = " ".join([f"`{tech}`" for tech in project['tech_stack']])
                st.markdown(f"**기술 스택**: {tech_tags}")
            
            with col2:
                if project['github']:
                    st.markdown(f"[📱 GitHub 링크]({project['github']})")
                if project['demo']:
                    st.markdown(f"[🌐 데모 보기]({project['demo']})")

# 기술 스택 페이지
elif page == "🛠️ 기술 스택":
    st.title("🛠️ 기술 스택 & 경험")
    
    skills = data["skills"]
    
    # 기술 스택 표시
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💻 프로그래밍 언어")
        
        if PLOTLY_AVAILABLE:
            # Plotly가 사용 가능한 경우 차트 사용
            import plotly.express as px
            fig1 = px.bar(
                x=list(skills["languages"].values()), 
                y=list(skills["languages"].keys()),
                orientation='h',
                color=list(skills["languages"].values()),
                color_continuous_scale="viridis"
            )
            fig1.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)
        else:
            # Plotly가 없는 경우 진행률 막대 사용
            for lang, skill_level in skills["languages"].items():
                st.write(f"**{lang}**")
                st.progress(skill_level / 100)
                st.write(f"{skill_level}%")
        
        st.subheader("🔧 도구 & 플랫폼")
        if PLOTLY_AVAILABLE:
            fig3 = px.bar(
                x=list(skills["tools"].values()), 
                y=list(skills["tools"].keys()),
                orientation='h',
                color=list(skills["tools"].values()),
                color_continuous_scale="plasma"
            )
            fig3.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig3, use_container_width=True)
        else:
            for tool, skill_level in skills["tools"].items():
                st.write(f"**{tool}**")
                st.progress(skill_level / 100)
                st.write(f"{skill_level}%")
    
    with col2:
        st.subheader("📚 프레임워크 & 라이브러리")
        if PLOTLY_AVAILABLE:
            fig2 = px.bar(
                x=list(skills["frameworks"].values()), 
                y=list(skills["frameworks"].keys()),
                orientation='h',
                color=list(skills["frameworks"].values()),
                color_continuous_scale="cividis"
            )
            fig2.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            for framework, skill_level in skills["frameworks"].items():
                st.write(f"**{framework}**")
                st.progress(skill_level / 100)
                st.write(f"{skill_level}%")
        
        # 경험 타임라인
        st.subheader("📅 경험 타임라인")
        if PANDAS_AVAILABLE:
            import pandas as pd
            timeline_df = pd.DataFrame(data["experience"])
            st.dataframe(timeline_df, use_container_width=True)
        else:
            for exp in data["experience"]:
                st.write(f"**{exp['year']}**: {exp['event']}")

# 연락처 페이지
elif page == "📞 연락처":
    st.title("📞 연락처 & 소셜 미디어")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📬 연락 방법")
        
        personal_info = data["personal_info"]
        st.markdown(f"""
        ### 📧 이메일
        **{personal_info['email']}**
        
        ### 📱 전화번호
        **{personal_info['phone']}**
        
        ### 📍 위치
        **{personal_info['location']}**
        """)
        
    with col2:
        st.subheader("🌐 소셜 미디어")
        
        st.markdown("""
        ### 🔗 링크
        - [GitHub](https://github.com/yourusername)
        - [LinkedIn](https://linkedin.com/in/yourusername)
        - [블로그](https://yourblog.com)
        - [Instagram](https://instagram.com/yourusername)
        """)
    
    # 연락 폼
    st.subheader("✉️ 메시지 보내기")
    
    with st.form("contact_form"):
        name = st.text_input("이름")
        email = st.text_input("이메일")
        subject = st.text_input("제목")
        message = st.text_area("메시지", height=150)
        
        submitted = st.form_submit_button("보내기")
        
        if submitted:
            if name and email and message:
                st.success("메시지가 성공적으로 전송되었습니다! 곧 답변드리겠습니다.")
                # 실제 구현에서는 이메일 전송 로직을 추가할 수 있습니다
            else:
                st.error("모든 필드를 입력해주세요.")

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>© 2024 포트폴리오. Streamlit으로 제작되었습니다.</p>
        <p>🚀 Made with ❤️ using Streamlit</p>
    </div>
    """,
    unsafe_allow_html=True
)

# 사이드바에 추가 정보
st.sidebar.markdown("---")
st.sidebar.markdown("### 🛠️ 기술 스택")
st.sidebar.markdown("- Python")
st.sidebar.markdown("- Streamlit") 
st.sidebar.markdown("- Pandas (선택사항)")
st.sidebar.markdown("- Plotly (선택사항)")

# 라이브러리 상태 표시
if not PANDAS_AVAILABLE:
    st.sidebar.warning("⚠️ Pandas가 설치되지 않음")
if not PLOTLY_AVAILABLE:
    st.sidebar.warning("⚠️ Plotly가 설치되지 않음")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📈 방문자 정보")
st.sidebar.info(f"현재 시간: {datetime.now().strftime('%H:%M:%S')}")