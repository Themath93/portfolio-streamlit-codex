"""홈 페이지 렌더링 전용 모듈."""
import base64
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st


def load_css() -> str:
    """홈 페이지 CSS를 로드한다.
    
    Returns:
        str: CSS 스타일 문자열
    """
    css_path = Path("css/home.css")
    if css_path.exists():
        return css_path.read_text(encoding="utf-8")
    return ""


def encode_image_to_base64(image_path: Path) -> str:
    """이미지를 base64로 인코딩한다.
    
    Args:
        image_path (Path): 이미지 파일 경로
        
    Returns:
        str: base64 인코딩된 이미지 문자열
    """
    if image_path.exists():
        with image_path.open("rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    return ""


def build_skill_domains(skills: Any) -> List[Tuple[str, List[str]]]:
    """기술 정보를 데이터·백엔드·데브옵스 도메인으로 정리한다.

    Args:
        skills (Any): ``portfolio_data.json``의 ``skills`` 항목 값.

    Returns:
        List[Tuple[str, List[str]]]: 도메인 이름과 기술 문자열 목록 쌍 리스트.
    """
    domain_order = ["데이터 엔지니어링", "백엔드", "데브옵스"]

    def normalize_entries(value: Any) -> List[str]:
        """기술 정보를 문자열 목록으로 평탄화한다.

        Args:
            value (Any): 변환할 기술 정보.

        Returns:
            List[str]: 사용자가 읽기 쉬운 문자열 목록.
        """
        if isinstance(value, dict):
            normalized_items: List[str] = []
            for key, descriptor in value.items():
                label = str(key)
                if isinstance(descriptor, (list, tuple)):
                    descriptor_text = ", ".join(str(item) for item in descriptor if item)
                else:
                    descriptor_text = str(descriptor) if descriptor else ""
                if descriptor_text:
                    normalized_items.append(f"{label} ({descriptor_text})")
                else:
                    normalized_items.append(label)
            return normalized_items
        if isinstance(value, list):
            flattened: List[str] = []
            for item in value:
                flattened.extend(normalize_entries(item))
            return flattened
        if value:
            return [str(value)]
        return []

    if not isinstance(skills, dict):
        return []

    explicit_domains = skills.get("domains")
    if isinstance(explicit_domains, dict):
        ordered_domains: List[Tuple[str, List[str]]] = []
        for domain in domain_order:
            entries = normalize_entries(explicit_domains.get(domain, []))
            if entries:
                ordered_domains.append((domain, entries))
        for domain_name, values in explicit_domains.items():
            if domain_name not in domain_order:
                entries = normalize_entries(values)
                if entries:
                    ordered_domains.append((domain_name, entries))
        return ordered_domains

    category_to_domain = {
        "languages": "데이터 엔지니어링",
        "data": "데이터 엔지니어링", 
        "data_engineering": "데이터 엔지니어링",
        "frameworks": "백엔드",
        "backend": "백엔드",
        "libraries": "백엔드",
        "tools": "데브옵스",
        "devops": "데브옵스",
        "infrastructure": "데브옵스",
    }

    aggregated: Dict[str, List[str]] = {domain: [] for domain in domain_order}
    for category, value in skills.items():
        if category == "domains":
            continue
        normalized_category = str(category).lower()
        target_domain = category_to_domain.get(normalized_category, "데이터 엔지니어링")
        aggregated.setdefault(target_domain, [])
        aggregated[target_domain].extend(normalize_entries(value))

    ordered_result: List[Tuple[str, List[str]]] = []
    for domain in domain_order:
        entries = list(dict.fromkeys(aggregated.get(domain, [])))
        if entries:
            ordered_result.append((domain, entries))
    for domain_name, values in aggregated.items():
        if domain_name not in domain_order:
            entries = list(dict.fromkeys(values))
            if entries:
                ordered_result.append((domain_name, entries))
    return ordered_result


def render_home_page_refactored(
    portfolio_data: Optional[Dict[str, Any]], 
    error_message: Optional[str]
) -> str:
    """홈 페이지 HTML을 생성한다.
    
    Args:
        portfolio_data: 포트폴리오 데이터
        error_message: 에러 메시지
        
    Returns:
        str: 렌더링된 HTML 문자열
    """
    if error_message:
        return f"""
        <div class="home-container">
            <div style="color: #ef4444; padding: 2rem; text-align: center; background: #fef2f2; border-radius: 12px;">
                <h2>오류 발생</h2>
                <p>{error_message}</p>
                <p style="font-size: 0.9rem; color: #6b7280;">portfolio_data.json 파일이 존재하고 올바른 형식인지 확인해주세요.</p>
            </div>
        </div>
        """
    
    if not portfolio_data:
        return """
        <div class="home-container">
            <div style="color: #6b7280; padding: 2rem; text-align: center; background: #f9fafb; border-radius: 12px;">
                <h2>포트폴리오 데이터 없음</h2>
                <p>표시할 포트폴리오 데이터가 없습니다. JSON 파일을 업데이트한 뒤 다시 시도해주세요.</p>
            </div>
        </div>
        """

    # 데이터 추출
    personal_info = portfolio_data.get("personal_info", {})
    about_info = portfolio_data.get("about", {})
    experience_items = portfolio_data.get("experience", [])
    skills = portfolio_data.get("skills", {})
    
    name = personal_info.get("name", "포트폴리오")
    title = personal_info.get("title", "전문가")
    description = about_info.get("description", "")
    interests = about_info.get("interests", [])
    educations = about_info.get("educations", [])
    
    # 이미지 인코딩
    engineer_image_path = Path("images/home/home_engineer.png")
    engineer_image_base64 = encode_image_to_base64(engineer_image_path)
    
    # 스킬 도메인 구성
    skill_domains = build_skill_domains(skills)
    
    # Hero 섹션 HTML
    hero_image_html = ""
    if engineer_image_base64:
        hero_image_html = f"""
        <div class="hero-image">
            <img src="data:image/png;base64,{engineer_image_base64}" alt="Engineer Illustration" />
        </div>
        """
    else:
        hero_image_html = """
        <div class="hero-image">
            <div style="background: #f3f4f6; height: 400px; border-radius: 20px; display: flex; align-items: center; justify-content: center; color: #6b7280;">
                <p>이미지를 찾을 수 없습니다</p>
            </div>
        </div>
        """
    
    # 관심 주제 HTML
    interests_html = ""
    if isinstance(interests, list) and interests:
        interests_tags = "".join([
            f'<span class="interest-tag">{interest}</span>'
            for interest in interests
        ])
        interests_html = f"""
        <div class="interests-section">
            <h2 class="section-title">🎯 관심 주제</h2>
            <div class="interests-grid">
                {interests_tags}
            </div>
        </div>
        """
    
    # 교육 HTML
    education_html = ""
    if educations:
        education_items = "".join([
            f'<div class="info-item"><div class="info-content">{education}</div></div>'
            for education in educations
        ])
        education_html = f"""
        <div class="info-card">
            <h3 class="info-card-title">🎓 교육</h3>
            {education_items}
        </div>
        """
    else:
        education_html = """
        <div class="info-card">
            <h3 class="info-card-title">🎓 교육</h3>
            <div class="info-item">
                <div class="info-content" style="color: #9ca3af;">등록된 학력이 없습니다.</div>
            </div>
        </div>
        """
    
    # 경력 HTML
    experience_html = ""
    if experience_items:
        experience_items_html = "".join([
            f'''
            <div class="info-item">
                <div class="info-period">{item.get("period", "기간 미상")}</div>
                <div class="info-content">{item.get("event", "세부 내용 미상")}</div>
            </div>
            '''
            for item in experience_items
        ])
        experience_html = f"""
        <div class="info-card">
            <h3 class="info-card-title">💼 경력</h3>
            {experience_items_html}
        </div>
        """
    else:
        experience_html = """
        <div class="info-card">
            <h3 class="info-card-title">💼 경력</h3>
            <div class="info-item">
                <div class="info-content" style="color: #9ca3af;">등록된 경력 정보가 없습니다.</div>
            </div>
        </div>
        """
    
    # 기술 스택 HTML
    skills_html = ""
    if skill_domains:
        skill_domains_html = "".join([
            f'''
            <div class="skill-domain">
                <h4 class="skill-domain-title">{domain_name}</h4>
                <ul class="skill-list">
                    {"".join([f'<li class="skill-item">{skill}</li>' for skill in skills_list])}
                </ul>
            </div>
            '''
            for domain_name, skills_list in skill_domains
        ])
        skills_html = f"""
        <div class="skills-section">
            <h2 class="section-title">⚡ 보유 기술</h2>
            <div class="skills-grid">
                {skill_domains_html}
            </div>
        </div>
        """
    else:
        skills_html = """
        <div class="skills-section">
            <h2 class="section-title">⚡ 보유 기술</h2>
            <div style="text-align: center; color: #9ca3af; padding: 2rem;">
                기술 정보를 skills 항목에 등록하면 이 영역에 표시됩니다.
            </div>
        </div>
        """
    
    # 현재 날짜
    current_date = datetime.now().strftime('%Y년 %m월 %d일')
    
    # 전체 HTML 구성
    html_content = f"""
    <div class="home-container">
        <!-- Hero Section -->
        <div class="hero-section">
            <div class="hero-content">
                <div class="greeting">Hello !!!</div>
                <h1 class="hero-title">I'm {name} !</h1>
                <h2 class="hero-subtitle">{title}</h2>
                <p class="hero-description">{description}</p>
                <a href="https://lizard-dive-9a3.notion.site/37b80353afce44a19913c66614f23674?pvs=74" class="download-btn">
                    📄 노션 포트폴리오 링크
                </a>
            </div>
            {hero_image_html}
        </div>
        
        {interests_html}
        
        <!-- 교육 및 경력 Section -->
        <div class="info-section">
            {education_html}
            {experience_html}
        </div>
        
        {skills_html}
        
        <div class="update-info">
            📅 마지막 업데이트: {current_date}
        </div>
    </div>
    """
    
    return html_content


def render_home_with_chatbot(
    portfolio_data: Optional[Dict[str, Any]],
    error_message: Optional[str]
) -> None:
    """홈 페이지와 챗봇을 함께 렌더링한다.
    
    Args:
        portfolio_data: 포트폴리오 데이터  
        error_message: 에러 메시지
    """
    # CSS 로드
    css_content = load_css()
    
    # CSS 적용
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    
    # 홈 페이지 HTML 렌더링
    home_html = render_home_page_refactored(portfolio_data, error_message)
    st.html(home_html)
    
    # 챗봇 섹션을 위한 추가 스타일링
    st.markdown("""
    <div class="chatbot-section">
        <div style="height: 2rem;"></div>
    </div>
    """, unsafe_allow_html=True)