"""Streamlit 기반 포트폴리오 애플리케이션."""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from portfolio_chatbot import (
    build_langchain_history,
    build_vector_store,
    create_portfolio_chain,
    load_portfolio_documents,
)

PDF_PATH = Path("assets/portfolio.pdf")
PROJECT_PDF_DIRECTORY = Path("assets/projects")
PORTFOLIO_DATA_PATH = Path("portfolio_data.json")

load_dotenv()

PROJECT_PDF_DIRECTORY.mkdir(parents=True, exist_ok=True)


SKILL_LEVEL_SCORES = {
    "최상": 95,
    "상": 90,
    "중상": 80,
    "중": 70,
    "중하": 60,
    "하": 50,
}


def configure_page() -> None:
    """Streamlit 페이지 기본 구성을 수행한다.

    Returns:
        None: 반환값이 없다.
    """
    st.set_page_config(
        page_title="포트폴리오 - Portfolio",
        page_icon="👨‍💻",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def initialize_session_state() -> None:
    """애플리케이션에 필요한 세션 상태를 초기화한다.

    Returns:
        None: 반환값이 없다.
    """
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "openai_api_key" not in st.session_state:
        st.session_state["openai_api_key"] = os.getenv("OPENAI_API_KEY", "")
    if "openai_api_key_input" not in st.session_state:
        st.session_state["openai_api_key_input"] = st.session_state["openai_api_key"]
    if "project_chat_histories" not in st.session_state:
        st.session_state["project_chat_histories"] = {}
    if "active_project_chat" not in st.session_state:
        st.session_state["active_project_chat"] = None


@st.cache_data(show_spinner=False)
def load_portfolio_data_cached(json_path_str: str) -> Dict[str, Any]:
    """포트폴리오 JSON 데이터를 로드하여 캐시에 보관한다.

    Args:
        json_path_str (str): 포트폴리오 데이터 JSON 파일 경로 문자열.

    Returns:
        Dict[str, Any]: JSON 파일에서 파싱한 포트폴리오 데이터 사전.

    Raises:
        FileNotFoundError: 지정한 JSON 파일이 존재하지 않을 때 발생한다.
        ValueError: JSON 구문 오류 등으로 데이터를 파싱할 수 없을 때 발생한다.
    """

    json_path = Path(json_path_str)
    if not json_path.exists():
        raise FileNotFoundError(f"포트폴리오 데이터 파일을 찾을 수 없습니다: {json_path}")

    try:
        with json_path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"포트폴리오 데이터 파일을 파싱하는 중 오류가 발생했습니다: {error}"
        ) from error


@st.cache_resource(show_spinner=False)
def initialize_chat_chain_cached(pdf_path_str: str):
    """포트폴리오 챗봇 체인을 초기화하고 캐시한다.

    Args:
        pdf_path_str (str): 포트폴리오 PDF의 경로 문자열.

    Returns:
        Any: LangChain 실행 체인 인스턴스.
    """
    pdf_path = Path(pdf_path_str)
    if not pdf_path.exists():
        raise FileNotFoundError(f"포트폴리오 PDF를 찾을 수 없습니다: {pdf_path}")

    documents = load_portfolio_documents(pdf_path)
    vector_store = build_vector_store(documents)
    return create_portfolio_chain(vector_store)


def prepare_portfolio_data(json_path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """포트폴리오 데이터 로드를 수행하고 오류 메시지를 반환한다.

    Args:
        json_path (Path): 포트폴리오 JSON 데이터 파일 경로.

    Returns:
        Tuple[Optional[Dict[str, Any]], Optional[str]]: 로드된 데이터와 오류 메시지.
    """

    try:
        return load_portfolio_data_cached(str(json_path)), None
    except FileNotFoundError as error:
        return None, str(error)
    except ValueError as error:  # pylint: disable=broad-except
        return None, str(error)


def render_sidebar_navigation() -> Tuple[str, Optional[str]]:
    """사이드바 네비게이션과 API 키 입력 폼을 출력한다.

    Returns:
        Tuple[str, Optional[str]]: 선택된 페이지와 설정된 OpenAI API 키.
    """
    st.sidebar.title("📂 Navigation")
    page = st.sidebar.selectbox(
        "페이지를 선택하세요",
        ["🏠 홈", "👤 소개", "💼 프로젝트", "🛠️ 기술 스택", "📞 연락처", "🤖 챗봇"],
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("🔐 OpenAI 설정")
    api_key_input = st.sidebar.text_input(
        "OpenAI API Key",
        value=st.session_state.get("openai_api_key_input", ""),
        type="password",
        help="환경 변수로 설정하지 않았다면 여기에 API 키를 입력하세요.",
    )

    if api_key_input:
        st.session_state["openai_api_key"] = api_key_input
        st.session_state["openai_api_key_input"] = api_key_input
        os.environ["OPENAI_API_KEY"] = api_key_input
    elif st.session_state.get("openai_api_key"):
        os.environ["OPENAI_API_KEY"] = st.session_state["openai_api_key"]

    api_key = st.session_state.get("openai_api_key") or os.getenv("OPENAI_API_KEY")

    st.sidebar.info(
        "챗봇 기능은 LangChain과 OpenAI API를 사용하여 포트폴리오 PDF를 분석합니다. "
        "API 키를 입력하면 대화형 질의응답을 시작할 수 있습니다."
    )
    return page, api_key


def prepare_chat_chain(api_key: Optional[str], pdf_path: Path) -> Tuple[Optional[Any], Optional[str]]:
    """챗봇 체인을 준비하고 오류 메시지를 반환한다.

    Args:
        api_key (Optional[str]): 설정된 OpenAI API 키.
        pdf_path (Path): 포트폴리오 PDF 파일 경로.

    Returns:
        Tuple[Optional[Any], Optional[str]]: 준비된 체인과 오류 메시지.
    """

    if not api_key:
        return None, "OpenAI API Key를 입력하거나 환경 변수로 설정해주세요."

    if not pdf_path.exists():
        return None, f"포트폴리오 PDF 파일이 존재하지 않습니다: {pdf_path}"

    try:
        chain = initialize_chat_chain_cached(str(pdf_path))
    except Exception as error:  # pylint: disable=broad-except
        return None, f"챗봇 초기화 중 오류가 발생했습니다: {error}"

    return chain, None


def resolve_project_pdf_path(project_id: str) -> Optional[Path]:
    """프로젝트 식별자에 대응하는 PDF 경로를 반환한다.

    Args:
        project_id (str): ``portfolio_data.json``에 정의된 프로젝트 식별자.

    Returns:
        Optional[Path]: 매칭되는 PDF 경로. 파일이 존재하지 않으면 ``None``.
    """

    if not project_id:
        return None

    candidate_path = PROJECT_PDF_DIRECTORY / f"{project_id}.pdf"
    return candidate_path if candidate_path.exists() else None


def _normalize_project_stack(project: Dict[str, Any]) -> List[str]:
    """프로젝트 사전에서 기술 스택 정보를 표준화된 리스트로 반환한다.

    Args:
        project (Dict[str, Any]): 프로젝트 정보를 담은 사전.

    Returns:
        List[str]: 문자열로 구성된 기술 스택 목록. 정보가 없다면 빈 리스트를 반환한다.
    """

    stack_value = project.get("tech_stack") or project.get("teck_stack") or []
    if isinstance(stack_value, (list, tuple, set)):
        return [str(item) for item in stack_value]
    if isinstance(stack_value, str):
        return [stack.strip() for stack in stack_value.split(",") if stack.strip()]
    return []


def _build_skill_dataframe(skill_items: Dict[str, Any], label_column: str) -> pd.DataFrame:
    """기술 사전을 시각화에 활용할 수 있는 데이터프레임으로 변환한다.

    Args:
        skill_items (Dict[str, Any]): 기술 이름을 키로, 숙련도 표기를 값으로 갖는 사전.
        label_column (str): 기술 이름을 표시할 열 제목.

    Returns:
        pd.DataFrame: 기술, 숙련도 점수, 숙련도 표기를 포함하는 데이터프레임.
    """

    records: List[Dict[str, Any]] = []
    for skill_name, raw_level in (skill_items or {}).items():
        level_label = str(raw_level)
        level_score = SKILL_LEVEL_SCORES.get(level_label, 60)
        records.append(
            {
                label_column: skill_name,
                "숙련도 점수": level_score,
                "숙련도": level_label,
            }
        )

    return pd.DataFrame(records)


def _extract_experience_periods(experience_items: Iterable[Dict[str, Any]]) -> pd.DataFrame:
    """경력 정보 컬렉션을 표 형태로 변환한다.

    Args:
        experience_items (Iterable[Dict[str, Any]]): 기간 및 주요 활동을 담은 경력 정보 목록.

    Returns:
        pd.DataFrame: 경력 기간과 활동을 포함한 데이터프레임. 데이터가 없다면 빈 데이터프레임을 반환한다.
    """

    records = [
        {"기간": item.get("period", "기간 미상"), "주요 활동": item.get("event", "내용 미상")}
        for item in experience_items
    ]
    return pd.DataFrame(records)


def render_home_page(
    portfolio_data: Optional[Dict[str, Any]],
    error_message: Optional[str],
) -> None:
    """포트폴리오 데이터를 기반으로 홈 화면 콘텐츠를 렌더링한다.

    Args:
        portfolio_data (Optional[Dict[str, Any]]): ``portfolio_data.json``에서 로드한 데이터.
        error_message (Optional[str]): 데이터 로드 실패 시 사용자에게 안내할 오류 메시지.
    """

    st.title("👋 안녕하세요! 포트폴리오에 오신 것을 환영합니다")

    if error_message:
        st.error(error_message)
        st.info("`portfolio_data.json` 파일이 존재하고 올바른 형식인지 확인해주세요.")
        return

    if not portfolio_data:
        st.info("표시할 포트폴리오 데이터가 없습니다. JSON 파일을 업데이트한 뒤 다시 시도해주세요.")
        return

    personal_info = portfolio_data.get("personal_info", {})
    about_info = portfolio_data.get("about", {})
    projects = portfolio_data.get("projects", [])
    experience_items = portfolio_data.get("experience", [])
    skills = portfolio_data.get("skills", {})
    languages = skills.get("languages", {}) if isinstance(skills, dict) else {}

    name = personal_info.get("name", "포트폴리오 주인")
    title = personal_info.get("title")
    headline = f"{name} · {title}" if title else name

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(headline)
        description = about_info.get("description")
        if description:
            st.write(description)

        interests = about_info.get("interests")
        if isinstance(interests, list) and interests:
            st.markdown("### 💡 관심 분야")
            st.markdown("\n".join([f"- {interest}" for interest in interests]))

        education = about_info.get("education")
        if education:
            st.markdown("### 🎓 교육")
            st.write(education)

        strengths = about_info.get("strengths")
        if isinstance(strengths, list) and strengths:
            st.markdown("### 💪 강점")
            st.markdown("\n".join([f"- {strength}" for strength in strengths]))

        if experience_items:
            st.markdown("### 🧭 주요 경력")
            for item in experience_items:
                period = item.get("period", "기간 미상")
                event = item.get("event", "세부 내용 미상")
                st.markdown(f"- **{period}** · {event}")

    with col2:
        st.markdown("### 📬 연락처")
        contact_entries = [
            ("이메일", personal_info.get("email")),
            ("전화번호", personal_info.get("phone")),
            ("위치", personal_info.get("location")),
        ]
        for label, value in contact_entries:
            if value:
                st.markdown(f"- **{label}**: {value}")

        social_links = portfolio_data.get("social_links", {})
        if social_links:
            st.markdown("### 🌐 소셜 링크")
            for label, url in social_links.items():
                if url:
                    st.markdown(f"- [{label}]({url})")

    st.markdown("---")

    metrics_columns = st.columns(3)
    metrics_columns[0].metric("프로젝트 수", len(projects))
    metrics_columns[1].metric("사용 언어", len(languages))
    metrics_columns[2].metric("경력 이력", len(experience_items))

    st.caption(f"📅 마지막 업데이트: {datetime.now().strftime('%Y년 %m월 %d일')}")

    if projects:
        st.markdown("### 🚀 대표 프로젝트")
        for project in projects[:3]:
            title_text = project.get("title", "이름 미정 프로젝트")
            description_text = project.get("description") or "프로젝트 설명이 제공되지 않았습니다."
            company = project.get("company")
            period = project.get("period")
            goal = project.get("goal")
            output = project.get("output")

            st.markdown(f"**{title_text}**")
            if company or period:
                st.caption(" · ".join(filter(None, [company, period])))
            st.write(description_text)
            if goal:
                st.markdown(f"- 목표: {goal}")
            if output:
                st.markdown(f"- 성과: {output}")

            tech_stack = _normalize_project_stack(project)
            if tech_stack:
                st.caption("기술 스택: " + ", ".join(tech_stack))


def render_about_page(portfolio_data: Optional[Dict[str, Any]]) -> None:
    """소개 페이지 콘텐츠를 포트폴리오 데이터 기반으로 출력한다.

    Args:
        portfolio_data (Optional[Dict[str, Any]]): ``portfolio_data.json``에서 로드한 데이터.
    """

    st.title("👤 소개")

    if not portfolio_data:
        st.info("포트폴리오 데이터가 존재하지 않아 기본 소개 정보를 표시합니다.")
        return

    personal_info = portfolio_data.get("personal_info", {})
    about_info = portfolio_data.get("about", {})
    experience_items = portfolio_data.get("experience", [])

    name = personal_info.get("name")
    title = personal_info.get("title")
    headline = " · ".join(filter(None, [name, title])) if (name or title) else "포트폴리오 소개"

    st.subheader(headline)

    description = about_info.get("description")
    if description:
        st.write(description)

    col1, col2 = st.columns(2)

    with col1:
        interests = about_info.get("interests")
        if isinstance(interests, list) and interests:
            st.markdown("### 🎯 관심 분야")
            st.markdown("\n".join([f"- {interest}" for interest in interests]))

        strengths = about_info.get("strengths")
        if isinstance(strengths, list) and strengths:
            st.markdown("### 💪 강점")
            st.markdown("\n".join([f"- {strength}" for strength in strengths]))

    with col2:
        education = about_info.get("education")
        if education:
            st.markdown("### 🎓 교육")
            st.write(education)

        contact_entries = [
            ("이메일", personal_info.get("email")),
            ("전화번호", personal_info.get("phone")),
            ("위치", personal_info.get("location")),
        ]
        st.markdown("### 📬 연락처")
        for label, value in contact_entries:
            if value:
                st.markdown(f"- **{label}**: {value}")

    experience_df = _extract_experience_periods(experience_items)
    if not experience_df.empty:
        st.markdown("### 🧭 경력 타임라인")
        st.table(experience_df)


def render_projects_page(
    portfolio_data: Optional[Dict[str, Any]], api_key: Optional[str]
) -> None:
    """프로젝트 데이터를 기반으로 상세 정보를 렌더링한다.

    Args:
        portfolio_data (Optional[Dict[str, Any]]): ``portfolio_data.json``에서 로드한 데이터.
        api_key (Optional[str]): OpenAI API 키. 프로젝트별 챗봇 초기화에 사용된다.
    """

    st.title("💼 프로젝트 포트폴리오")

    projects: List[Dict[str, Any]] = []
    if portfolio_data:
        raw_projects = portfolio_data.get("projects", [])
        if isinstance(raw_projects, list):
            projects = [project for project in raw_projects if isinstance(project, dict)]

    if not projects:
        st.info("등록된 프로젝트가 없습니다. JSON 파일을 업데이트해주세요.")
        return

    companies = sorted({project.get("company", "기타") for project in projects})
    filter_options = ["전체"] + companies
    selected_company = st.selectbox("회사별로 프로젝트를 필터링하세요", filter_options)

    filtered_projects = (
        [project for project in projects if project.get("company", "기타") == selected_company]
        if selected_company != "전체"
        else projects
    )

    for index, project in enumerate(filtered_projects):
        project_id = project.get("id", "")
        title_text = project.get("title", "이름 미정 프로젝트")
        with st.expander(f"📁 {title_text}", expanded=True):
            col1, col2 = st.columns([3, 2])

            with col1:
                st.markdown(f"**회사**: {project.get('company', '기관 미상')}")
                st.markdown(f"**기간**: {project.get('period', '기간 미상')}")
                goal = project.get("goal")
                if goal:
                    st.markdown(f"**목표**: {goal}")
                description = project.get("description")
                if description:
                    st.markdown(f"**설명**: {description}")
                output = project.get("output")
                if output:
                    st.markdown(f"**성과**: {output}")

            with col2:
                tech_stack = _normalize_project_stack(project)
                if tech_stack:
                    st.markdown("**기술 스택**")
                    st.markdown(", ".join(tech_stack))

                pdf_path = resolve_project_pdf_path(project_id)
                if pdf_path is None:
                    st.info(
                        "프로젝트 세부 문서 PDF가 존재하지 않습니다. 'assets/projects' 경로에 파일을 추가해주세요."
                    )
                else:
                    button_key = f"start_chat_{project_id or index}"
                    if st.button("🤖 프로젝트 챗봇 열기", key=button_key):
                        st.session_state["active_project_chat"] = project_id

        if st.session_state.get("active_project_chat") == project_id:
            render_project_chat_section(project_id, title_text, api_key)


def render_skills_page(portfolio_data: Optional[Dict[str, Any]]) -> None:
    """기술 스택과 경력 정보를 시각화한다.

    Args:
        portfolio_data (Optional[Dict[str, Any]]): ``portfolio_data.json``에서 로드한 데이터.
    """

    st.title("🛠️ 기술 스택 & 경험")

    if not portfolio_data:
        st.info("포트폴리오 데이터가 없어 기본 예시를 표시하지 않습니다. JSON 파일을 확인해주세요.")
        return

    skills_data = portfolio_data.get("skills", {}) if isinstance(portfolio_data, dict) else {}
    languages_df = _build_skill_dataframe(skills_data.get("languages", {}), "언어")
    frameworks_df = _build_skill_dataframe(skills_data.get("frameworks", {}), "프레임워크/라이브러리")
    tools_df = _build_skill_dataframe(skills_data.get("tools", {}), "도구")
    experience_df = _extract_experience_periods(portfolio_data.get("experience", []))

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💻 프로그래밍 언어")
        if not languages_df.empty:
            fig1 = px.bar(
                languages_df,
                x="숙련도 점수",
                y="언어",
                orientation="h",
                color="숙련도 점수",
                hover_data=["숙련도"],
                color_continuous_scale="viridis",
            )
            fig1.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("등록된 프로그래밍 언어 정보가 없습니다.")

        st.subheader("🔧 도구 & 플랫폼")
        if not tools_df.empty:
            fig3 = px.bar(
                tools_df,
                x="숙련도 점수",
                y="도구",
                orientation="h",
                color="숙련도 점수",
                hover_data=["숙련도"],
                color_continuous_scale="plasma",
            )
            fig3.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("등록된 도구 정보가 없습니다.")

    with col2:
        st.subheader("📚 프레임워크 & 라이브러리")
        if not frameworks_df.empty:
            fig2 = px.bar(
                frameworks_df,
                x="숙련도 점수",
                y="프레임워크/라이브러리",
                orientation="h",
                color="숙련도 점수",
                hover_data=["숙련도"],
                color_continuous_scale="cividis",
            )
            fig2.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("등록된 프레임워크 정보가 없습니다.")

        st.subheader("📅 경력 타임라인")
        if not experience_df.empty:
            st.table(experience_df)
        else:
            st.info("경력 정보가 없습니다. JSON 파일을 업데이트해주세요.")


def render_contact_page(portfolio_data: Optional[Dict[str, Any]]) -> None:
    """포트폴리오 데이터를 활용하여 연락처 정보를 출력하고 메시지 폼을 제공한다.

    Args:
        portfolio_data (Optional[Dict[str, Any]]): `portfolio_data.json`에서 로드한 데이터.
    """

    st.title("📞 연락처 & 소셜 미디어")

    personal_info = (portfolio_data or {}).get("personal_info", {})
    social_links = (portfolio_data or {}).get("social_links", {})

    default_contact = {
        "email": "your.email@example.com",
        "phone": "+82-10-1234-5678",
        "location": "서울, 대한민국",
    }

    email_value = personal_info.get("email") or default_contact["email"]
    phone_value = personal_info.get("phone") or default_contact["phone"]
    location_value = personal_info.get("location") or default_contact["location"]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📬 연락 방법")
        st.markdown("### 📧 이메일")
        st.markdown(f"**{email_value}**")

        st.markdown("### 📱 전화번호")
        st.markdown(f"**{phone_value}**")

        st.markdown("### 📍 위치")
        st.markdown(f"**{location_value}**")

    with col2:
        st.subheader("🌐 소셜 미디어")
        if social_links:
            st.markdown("### 🔗 링크")
            for label, url in social_links.items():
                if url:
                    st.markdown(f"- [{label}]({url})")
        else:
            st.info("등록된 소셜 링크가 없습니다. `portfolio_data.json`을 업데이트해보세요.")

    st.subheader("✉️ 메시지 보내기")
    with st.form("contact_form"):
        name = st.text_input("이름")
        email = st.text_input("이메일", value=email_value)
        subject = st.text_input("제목")
        message = st.text_area("메시지", height=150)

        submitted = st.form_submit_button("보내기")

        if submitted:
            if name and email and message:
                st.success("메시지가 성공적으로 전송되었습니다! 곧 답변드리겠습니다.")
            else:
                st.error("모든 필드를 입력해주세요.")


def render_chat_page(chat_chain: Optional[Any], error_message: Optional[str]) -> None:
    """포트폴리오 챗봇 인터페이스를 렌더링한다.

    Args:
        chat_chain (Optional[Any]): LangChain 실행 체인 인스턴스.
        error_message (Optional[str]): 초기화 과정에서 발생한 오류 메시지.
    """
    st.title("🤖 포트폴리오 챗봇")
    st.markdown(
        "LangChain, OpenAI, FAISS를 활용하여 포트폴리오 PDF 기반 답변을 제공합니다.\n"
        "프로젝트, 경력, 기술 스택에 대해 무엇이든 질문해보세요."
    )

    if error_message:
        st.error(error_message)
        return

    if chat_chain is None:
        st.info("챗봇을 초기화할 준비가 되었습니다. 질문을 입력하면 대화를 시작합니다.")
        return

    for message in st.session_state["chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_prompt = st.chat_input("포트폴리오에 대해 궁금한 점을 입력하세요.")
    if not user_prompt:
        return

    history_messages = build_langchain_history(st.session_state["chat_history"])
    st.session_state["chat_history"].append({"role": "user", "content": user_prompt})

    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("답변 생성 중..."):
            try:
                result: Dict[str, Any] = chat_chain.invoke(
                    {
                        "input": user_prompt,
                        "chat_history": history_messages,
                    }
                )
            except Exception as error:  # pylint: disable=broad-except
                error_text = "죄송합니다. 답변 생성 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
                st.error(error_text)
                st.session_state["chat_history"].append(
                    {"role": "assistant", "content": error_text}
                )
                return

            answer = result.get("answer", "요청에 대한 답변을 생성하지 못했습니다.")
            st.markdown(answer)
            st.session_state["chat_history"].append({"role": "assistant", "content": answer})

            context_docs: Sequence[Any] = result.get("context", [])
            if context_docs:
                with st.expander("🔍 참고한 문맥 보기"):
                    for index, doc in enumerate(context_docs, start=1):
                        st.markdown(f"**문서 {index}**")
                        st.write(doc.page_content)


def render_project_chat_section(
    project_id: str, project_title: str, api_key: Optional[str]
) -> None:
    """프로젝트 전용 챗봇 인터페이스를 렌더링한다.

    Args:
        project_id (str): ``portfolio_data.json``의 프로젝트 식별자.
        project_title (str): 사용자에게 표시할 프로젝트 제목.
        api_key (Optional[str]): OpenAI API 키.
    """

    st.markdown("---")
    st.subheader(f"🤖 {project_title} 대화형 문서 요약")

    pdf_path = resolve_project_pdf_path(project_id)
    if pdf_path is None:
        st.warning(
            "프로젝트에 연결된 PDF가 존재하지 않습니다. 'assets/projects' 경로에 파일을 배치해주세요."
        )
        return

    chat_chain, error_message = prepare_chat_chain(api_key, pdf_path)
    if error_message:
        st.error(error_message)
        return

    histories: Dict[str, List[Dict[str, str]]] = st.session_state.setdefault(
        "project_chat_histories", {}
    )
    history = histories.setdefault(project_id, [])

    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_prompt = st.chat_input(
        f"{project_title} 프로젝트 문서에 대해 질문을 입력하세요.",
        key=f"project_chat_input_{project_id}",
    )
    if not user_prompt:
        return

    history_messages = build_langchain_history(history)
    history.append({"role": "user", "content": user_prompt})

    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("문서를 검토하여 답변을 작성 중입니다..."):
            try:
                result: Dict[str, Any] = chat_chain.invoke(
                    {"input": user_prompt, "chat_history": history_messages}
                )
            except Exception:  # pylint: disable=broad-except
                error_text = (
                    "죄송합니다. 프로젝트 문서를 분석하는 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
                )
                st.error(error_text)
                history.append({"role": "assistant", "content": error_text})
                return

            answer = result.get("answer", "요청한 정보에 대한 답변을 찾을 수 없습니다.")
            st.markdown(answer)
            history.append({"role": "assistant", "content": answer})

            context_docs: Sequence[Any] = result.get("context", [])
            if context_docs:
                with st.expander("🔍 참고한 문맥 보기"):
                    for index, doc in enumerate(context_docs, start=1):
                        st.markdown(f"**문서 {index}**")
                        st.write(doc.page_content)


def render_footer() -> None:
    """페이지 하단의 푸터를 출력한다.

    Returns:
        None: 반환값이 없다.
    """
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center'>
            <p>© 2024 포트폴리오. Streamlit으로 제작되었습니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """포트폴리오 애플리케이션의 진입점을 정의한다.

    Returns:
        None: 반환값이 없다.
    """
    configure_page()
    initialize_session_state()
    page, api_key = render_sidebar_navigation()

    portfolio_data, portfolio_error = prepare_portfolio_data(PORTFOLIO_DATA_PATH)
    if portfolio_error:
        st.sidebar.error("포트폴리오 데이터를 불러오지 못했습니다. 홈 화면에서 상세 내용을 확인해주세요.")

    chat_chain: Optional[Any] = None
    chat_error: Optional[str] = None
    if page == "🤖 챗봇":
        chat_chain, chat_error = prepare_chat_chain(api_key, PDF_PATH)

    if page == "🏠 홈":
        render_home_page(portfolio_data, portfolio_error)
    elif page == "👤 소개":
        render_about_page(portfolio_data)
    elif page == "💼 프로젝트":
        render_projects_page(portfolio_data, api_key)
    elif page == "🛠️ 기술 스택":
        render_skills_page(portfolio_data)
    elif page == "📞 연락처":
        render_contact_page(portfolio_data)
    elif page == "🤖 챗봇":
        render_chat_page(chat_chain, chat_error)

    render_footer()


if __name__ == "__main__":
    main()
