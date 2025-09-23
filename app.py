import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="포트폴리오 - Portfolio",
    page_icon="👨‍💻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사이드바 네비게이션
st.sidebar.title("📂 Navigation")
page = st.sidebar.selectbox(
    "페이지를 선택하세요",
    ["🏠 홈", "👤 소개", "💼 프로젝트", "🛠️ 기술 스택", "📞 연락처"]
)

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
        st.markdown("""
        ### 📊 Quick Stats
        """)
        
        # 간단한 통계 정보
        stats_data = {
            "항목": ["프로젝트", "사용 언어", "경력"],
            "개수": [5, 8, "2년+"]
        }
        st.table(pd.DataFrame(stats_data))

# 소개 페이지
elif page == "👤 소개":
    st.title("👤 About Me")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image("https://via.placeholder.com/300x300?text=Profile+Photo", 
                caption="프로필 사진", width=250)
    
    with col2:
        st.markdown("""
        ## 안녕하세요! 👋
        
        저는 **풀스택 개발자**로, 웹 개발과 데이터 분석에 열정을 가지고 있습니다.
        
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
        """)

# 프로젝트 페이지
elif page == "💼 프로젝트":
    st.title("💼 프로젝트 포트폴리오")
    
    # 프로젝트 필터
    project_type = st.selectbox("프로젝트 유형", ["전체", "웹 개발", "데이터 분석", "AI/ML"])
    
    # 샘플 프로젝트 데이터
    projects = [
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
    ]
    
    # 프로젝트 필터링
    if project_type != "전체":
        projects = [p for p in projects if p["type"] == project_type]
    
    # 프로젝트 카드 표시
    for i, project in enumerate(projects):
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
    
    # 기술 스택 데이터
    skills_data = {
        "언어": ["Python", "JavaScript", "Java", "SQL"],
        "숙련도": [90, 85, 75, 80]
    }
    
    frameworks_data = {
        "프레임워크/라이브러리": ["React", "Django", "Flask", "Streamlit", "Pandas"],
        "숙련도": [80, 85, 70, 90, 85]
    }
    
    tools_data = {
        "도구": ["Git", "Docker", "AWS", "PostgreSQL"],
        "숙련도": [85, 70, 65, 80]
    }
    
    # 차트로 시각화
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💻 프로그래밍 언어")
        fig1 = px.bar(
            x=skills_data["숙련도"], 
            y=skills_data["언어"],
            orientation='h',
            color=skills_data["숙련도"],
            color_continuous_scale="viridis"
        )
        fig1.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)
        
        st.subheader("🔧 도구 & 플랫폼")
        fig3 = px.bar(
            x=tools_data["숙련도"], 
            y=tools_data["도구"],
            orientation='h',
            color=tools_data["숙련도"],
            color_continuous_scale="plasma"
        )
        fig3.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        st.subheader("📚 프레임워크 & 라이브러리")
        fig2 = px.bar(
            x=frameworks_data["숙련도"], 
            y=frameworks_data["프레임워크/라이브러리"],
            orientation='h',
            color=frameworks_data["숙련도"],
            color_continuous_scale="cividis"
        )
        fig2.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
        
        # 경험 타임라인
        st.subheader("📅 경험 타임라인")
        timeline_data = pd.DataFrame({
            "연도": [2022, 2023, 2024],
            "경험": ["Python 학습 시작", "웹 개발 프로젝트", "AI/ML 프로젝트"]
        })
        st.table(timeline_data)

# 연락처 페이지
elif page == "📞 연락처":
    st.title("📞 연락처 & 소셜 미디어")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📬 연락 방법")
        
        st.markdown("""
        ### 📧 이메일
        **your.email@example.com**
        
        ### 📱 전화번호
        **+82-10-1234-5678**
        
        ### 📍 위치
        **서울, 대한민국**
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
            else:
                st.error("모든 필드를 입력해주세요.")

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>© 2024 포트폴리오. Streamlit으로 제작되었습니다.</p>
    </div>
    """,
    unsafe_allow_html=True
)