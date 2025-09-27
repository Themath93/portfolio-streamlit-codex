"""리팩토링된 사이드바 네비게이션 함수"""

import base64
from pathlib import Path
from typing import Any, Dict, Optional
import streamlit as st


def render_sidebar_navigation_refactored(
    portfolio_data: Optional[Dict[str, Any]],
    error_message: Optional[str],
) -> str:
    """사이드바 네비게이션과 프로필 정보를 출력한다 (리팩토링 버전).

    Args:
        portfolio_data (Optional[Dict[str, Any]]): ``portfolio_data.json``에서 로드한 데이터.
        error_message (Optional[str]): 데이터 로드 실패 시 노출할 오류 메시지.

    Returns:
        str: 선택된 페이지 식별자.
    """
    # CSS 로드
    sidecard_css_path = Path("css/sidecard.css")
    if sidecard_css_path.exists():
        css = sidecard_css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    personal_info = (portfolio_data or {}).get("personal_info", {})
    social_links = (portfolio_data or {}).get("social_links", {})
    # 데이터 추출
    name = personal_info.get("name", "이름")
    title = personal_info.get("title", "직책")
    location = personal_info.get("location", "위치")
    email = personal_info.get("email")
    phone = personal_info.get("phone")

    # 프로필 이미지 처리
    profile_image_html = ""
    profile_image_path = Path("images/윤병우_main_image.jpg")
    if profile_image_path.exists():
        try:
            with open(profile_image_path, "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode()
            profile_image_html = f'''
            <img src="data:image/jpeg;base64,{img_data}" 
                 style="width: 100px; height: 100px; border-radius: 50%; object-fit: cover; 
                        border: 4px solid white; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); 
                        transition: all 0.3s ease;" 
                 alt="Profile" onmouseover="this.style.transform='scale(1.05)'" 
                 onmouseout="this.style.transform='scale(1)'">
            '''
        except Exception:
            profile_image_html = ""

    # 메인 HTML 구조 구성
    sidebar_html = f'''
    <div class="profile-card" style="background: white; border-radius: 20px; padding: 2rem 1.5rem; 
                                   margin: 1rem; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); 
                                   text-align: center; border: 1px solid #e9ecef; 
                                   transition: all 0.3s ease;">
        <div class="profile-image-container" style="position: relative; display: inline-block; margin-bottom: 1.5rem;">
            {profile_image_html}
            <div class="status-indicator" style="position: absolute; bottom: 8px; right: 8px; 
                                               width: 16px; height: 16px; background: #28a745; 
                                               border: 3px solid white; border-radius: 50%; 
                                               box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);"></div>
        </div>
        <div class="profile-name" style="color: #212529; font-size: 1.5rem; font-weight: 600; 
                                        margin: 0 0 0.5rem 0; line-height: 1.2;">{name}</div>
        <div class="profile-title" style="color: #6c757d; font-size: 0.95rem; font-weight: 500; 
                                         margin: 0 0 0.3rem 0; display: flex; align-items: center; 
                                         justify-content: center; gap: 0.5rem;">
            <span class="title-badge" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                           color: white; padding: 0.2rem 0.6rem; border-radius: 12px; 
                                           font-size: 0.8rem; font-weight: 500;">{title}</span>
        </div>
        <div class="profile-location" style="color: #868e96; font-size: 0.9rem; display: flex; 
                                           align-items: center; justify-content: center; gap: 0.3rem; 
                                           margin-bottom: 1.5rem;">📍 {location}</div>
    </div>
    '''

    # 연락처 섹션 생성
    if email or phone:
        contact_items = ""
        if email:
            contact_items += f'''
            <a href="mailto:{email}" class="contact-item" 
               style="display: flex; align-items: center; gap: 0.8rem; padding: 0.6rem; 
                      margin-bottom: 0.4rem; background: white; border-radius: 8px; 
                      border: 1px solid #e9ecef; text-decoration: none; color: #495057; 
                      font-size: 0.85rem; transition: all 0.2s ease;" 
               onmouseover="this.style.background='#e3f2fd'; this.style.borderColor='#2196f3'; 
                           this.style.color='#1976d2'; this.style.transform='translateX(2px)'" 
               onmouseout="this.style.background='white'; this.style.borderColor='#e9ecef'; 
                          this.style.color='#495057'; this.style.transform='translateX(0)'">
                <div class="contact-icon">📧</div>
                <span>{email}</span>
            </a>
            '''
        if phone:
            contact_items += f'''
            <div class="contact-item" 
                 style="display: flex; align-items: center; gap: 0.8rem; padding: 0.6rem; 
                        margin-bottom: 0.4rem; background: white; border-radius: 8px; 
                        border: 1px solid #e9ecef; color: #495057; font-size: 0.85rem;">
                <div class="contact-icon">📱</div>
                <span>{phone}</span>
            </div>
            '''
        
        sidebar_html += f'''
        <div class="contact-section" style="background: #f8f9fa; border-radius: 12px; padding: 1rem; 
                                          margin: 1rem; border: 1px solid #e9ecef;">
            <div class="contact-title" style="color: #495057; font-size: 0.9rem; font-weight: 600; 
                                           margin-bottom: 0.8rem; text-align: center; display: flex; 
                                           align-items: center; justify-content: center; gap: 0.5rem;">📞 연락처</div>
            {contact_items}
        </div>
        '''

    # 소셜 링크 섹션 생성
    if social_links:
        def get_image_base64(image_path: str) -> str:
            """이미지를 base64로 인코딩"""
            try:
                with open(image_path, "rb") as img_file:
                    return base64.b64encode(img_file.read()).decode()
            except Exception:
                return ""
        
        # 이미지 경로와 매핑
        social_images = {
            "GitHub 링크": "images/logos/github.png",
            "Notion 포트폴리오 링크": "images/logos/notion.png"
        }
        
        social_fallback_icons = {
            "LinkedIn": "💼", 
            "Portfolio": "🌐",
            "Blog": "📝",
            "Email": "📧"
        }
        
        social_links_html = ""
        for label, url in social_links.items():
            if url:
                # 이미지가 있는 경우 이미지 사용, 없으면 아이콘 사용
                if label in list(social_images.keys()):
                    image_path = social_images[label]
                    if Path(image_path).exists():
                        img_data = get_image_base64(image_path)
                        if img_data:
                            social_links_html += f'''
                            <a href="{url}" target="_blank" class="social-link" title="{label}"
                               style="display: inline-flex; align-items: center; justify-content: center; 
                                      width: 40px; height: 40px; border-radius: 10px; background: #f8f9fa; 
                                      border: 1px solid #e9ecef; text-decoration: none; 
                                      transition: all 0.3s ease; padding: 8px;"
                               onmouseover="this.style.background='#007bff'; this.style.borderColor='#007bff'; 
                                           this.style.transform='translateY(-2px)'; 
                                           this.style.boxShadow='0 4px 12px rgba(0, 123, 255, 0.3)'"
                               onmouseout="this.style.background='#f8f9fa'; this.style.borderColor='#e9ecef'; 
                                          this.style.transform='translateY(0)'; this.style.boxShadow='none'">
                                <img src="data:image/png;base64,{img_data}" 
                                     style="width: 20px; height: 20px; filter: brightness(0) saturate(100%) invert(42%) sepia(15%) saturate(348%) hue-rotate(202deg) brightness(95%) contrast(87%);"
                                     onmouseover="this.style.filter='brightness(0) saturate(100%) invert(100%)'"
                                     onmouseout="this.style.filter='brightness(0) saturate(100%) invert(42%) sepia(15%) saturate(348%) hue-rotate(202deg) brightness(95%) contrast(87%)'">
                            </a>
                            '''
                        else:
                            # 이미지 로드 실패시 폴백 아이콘
                            icon = social_fallback_icons.get(label, "🔗")
                            social_links_html += f'''
                            <a href="{url}" target="_blank" class="social-link" title="{label}"
                               style="display: inline-flex; align-items: center; justify-content: center; 
                                      width: 40px; height: 40px; border-radius: 10px; background: #f8f9fa; 
                                      border: 1px solid #e9ecef; color: #6c757d; text-decoration: none; 
                                      font-size: 1.1rem; transition: all 0.3s ease;"
                               onmouseover="this.style.background='#007bff'; this.style.color='white'; 
                                           this.style.borderColor='#007bff'; this.style.transform='translateY(-2px)'; 
                                           this.style.boxShadow='0 4px 12px rgba(0, 123, 255, 0.3)'"
                               onmouseout="this.style.background='#f8f9fa'; this.style.color='#6c757d'; 
                                          this.style.borderColor='#e9ecef'; this.style.transform='translateY(0)'; 
                                          this.style.boxShadow='none'">
                                {icon}
                            </a>
                            '''
                    else:
                        # 이미지 파일이 없는 경우 폴백 아이콘
                        icon = social_fallback_icons.get(label, "🔗")
                        social_links_html += f'''
                        <a href="{url}" target="_blank" class="social-link" title="{label}"
                           style="display: inline-flex; align-items: center; justify-content: center; 
                                  width: 40px; height: 40px; border-radius: 10px; background: #f8f9fa; 
                                  border: 1px solid #e9ecef; color: #6c757d; text-decoration: none; 
                                  font-size: 1.1rem; transition: all 0.3s ease;"
                           onmouseover="this.style.background='#007bff'; this.style.color='white'; 
                                       this.style.borderColor='#007bff'; this.style.transform='translateY(-2px)'; 
                                       this.style.boxShadow='0 4px 12px rgba(0, 123, 255, 0.3)'"
                           onmouseout="this.style.background='#f8f9fa'; this.style.color='#6c757d'; 
                                      this.style.borderColor='#e9ecef'; this.style.transform='translateY(0)'; 
                                      this.style.boxShadow='none'">
                            {icon}
                        </a>
                        '''
                else:
                    # 이미지 매핑이 없는 경우 아이콘 사용
                    icon = social_fallback_icons.get(label, "🔗")
                    social_links_html += f'''
                    <a href="{url}" target="_blank" class="social-link" title="{label}"
                       style="display: inline-flex; align-items: center; justify-content: center; 
                              width: 40px; height: 40px; border-radius: 10px; background: #f8f9fa; 
                              border: 1px solid #e9ecef; color: #6c757d; text-decoration: none; 
                              font-size: 1.1rem; transition: all 0.3s ease;"
                       onmouseover="this.style.background='#007bff'; this.style.color='white'; 
                                   this.style.borderColor='#007bff'; this.style.transform='translateY(-2px)'; 
                                   this.style.boxShadow='0 4px 12px rgba(0, 123, 255, 0.3)'"
                       onmouseout="this.style.background='#f8f9fa'; this.style.color='#6c757d'; 
                                  this.style.borderColor='#e9ecef'; this.style.transform='translateY(0)'; 
                                  this.style.boxShadow='none'">
                        {icon}
                    </a>
                    '''
        sidebar_html += f'''
        <div class="social-section" style="background: white; border-radius: 12px; padding: 1rem; 
                          margin: 1rem; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05); 
                          border: 1px solid #e9ecef;">
            <div class="social-title" style="color: #495057; font-size: 0.9rem; font-weight: 600; 
                           margin-bottom: 1rem; text-align: center; display: flex; 
                           align-items: center; justify-content: center; gap: 0.5rem;">🌟 소셜 링크</div>
            <div class="social-links-grid" style="display: flex; flex-wrap: wrap; gap: 0.5rem; justify-content: center;">
            {social_links_html}
            </div>
        </div>
        '''

    # 푸터 추가
    sidebar_html += '''
    <div class="sidebar-footer" style="background: #f8f9fa; border-radius: 12px; padding: 1rem; 
                                     margin: 1rem; text-align: center; border: 1px solid #e9ecef;">
        <p style="color: #6c757d; font-size: 0.8rem; line-height: 1.4; margin: 0;">
            포트폴리오는 <a href="https://github.com/Themath93/portfolio-streamlit-codex" target="_blank" 
                         style="color: #007bff; text-decoration: none; font-weight: 500;"
                         onmouseover="this.style.textDecoration='underline'" 
                         onmouseout="this.style.textDecoration='none'">GitHub</a>에서 확인 가능합니다.<br>
            <strong>Codex AI</strong>를 활용하여 개발했습니다.
        </p>
    </div>
    '''

    with st.sidebar:
        # 한 번에 모든 HTML 출력
        st.html(sidebar_html)
        
        # 네비게이션 선택박스는 Streamlit 위젯 사용
        page = st.selectbox(
            "페이지 선택",
            ["🏠 홈", "👤 소개", "💼 프로젝트", "📞 연락처"],
            key="sidebar_page",
            label_visibility="collapsed"
        )

        # 에러 메시지
        if error_message:
            st.error(error_message)

    return page