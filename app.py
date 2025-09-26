"""Streamlit 기반 포트폴리오 애플리케이션."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Match, Optional, Sequence, Tuple

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from portfolio_chatbot import (
    PortfolioChatAssistant,
    build_langchain_history,
    build_vector_store,
    create_portfolio_assistant,
    create_portfolio_chain,
    load_project_documents,
)

ASSETS_DIRECTORY = Path("assets")
PROJECT_PDF_DIRECTORY = Path("assets/projects")
PORTFOLIO_DATA_PATH = Path("portfolio_data.json")

load_dotenv()

PROJECT_PDF_DIRECTORY.mkdir(parents=True, exist_ok=True)


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
    if "project_chat_histories" not in st.session_state:
        st.session_state["project_chat_histories"] = {}
    if "active_project_chat" not in st.session_state:
        st.session_state["active_project_chat"] = None
    if "follow_up_options" not in st.session_state:
        st.session_state["follow_up_options"] = []
    if "auto_generated_question" not in st.session_state:
        st.session_state["auto_generated_question"] = None
    if "sidebar_page" not in st.session_state:
        st.session_state["sidebar_page"] = "🏠 홈"
    if "navigate_to_home" not in st.session_state:
        st.session_state["navigate_to_home"] = False
    if "latest_exchange" not in st.session_state:
        st.session_state["latest_exchange"] = None


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
def initialize_portfolio_assistant_cached(
    assets_dir_str: str, json_path_str: str
) -> PortfolioChatAssistant:
    """홈 화면에서 사용하는 포트폴리오 챗봇 어시스턴트를 초기화한다.

    Args:
        assets_dir_str (str): 에셋 디렉터리 경로 문자열.
        json_path_str (str): 포트폴리오 JSON 파일 경로 문자열.

    Returns:
        PortfolioChatAssistant: LangChain 기반 포트폴리오 어시스턴트 인스턴스.
    """

    assets_dir = Path(assets_dir_str)
    json_path = Path(json_path_str)
    return create_portfolio_assistant(assets_dir, json_path)


@st.cache_resource(show_spinner=False)
def initialize_project_chat_chain_cached(pdf_path_str: str):
    """프로젝트 전용 PDF 챗봇 체인을 초기화하고 캐시한다.

    Args:
        pdf_path_str (str): 프로젝트 PDF 경로 문자열.

    Returns:
        Any: LangChain 실행 체인 인스턴스.
    """

    pdf_path = Path(pdf_path_str)
    documents = load_project_documents(pdf_path, file_name=pdf_path.name)
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


def render_sidebar_navigation(
    portfolio_data: Optional[Dict[str, Any]],
    error_message: Optional[str],
) -> str:
    """사이드바 네비게이션과 프로필 정보를 출력한다.

    Args:
        portfolio_data (Optional[Dict[str, Any]]): ``portfolio_data.json``에서 로드한 데이터.
        error_message (Optional[str]): 데이터 로드 실패 시 노출할 오류 메시지.

    Returns:
        str: 선택된 페이지 식별자.
    """

    personal_info = (portfolio_data or {}).get("personal_info", {})
    social_links = (portfolio_data or {}).get("social_links", {})

    profile_image_path = Path("images/윤병우_main_image.jpg")
    if profile_image_path.exists():
        st.sidebar.image(
            str(profile_image_path),
            use_container_width=True,
        )

    name = personal_info.get("name")
    title = personal_info.get("title")
    location = personal_info.get("location")

    if name:
        st.sidebar.markdown(f"### {name}")
    if title:
        st.sidebar.caption(title)
    if location:
        st.sidebar.markdown(f"📍 {location}")

    contact_lines: List[str] = []
    email = personal_info.get("email")
    phone = personal_info.get("phone")
    if email:
        contact_lines.append(f"📧 [{email}](mailto:{email})")
    if phone:
        contact_lines.append(f"📱 {phone}")
    if contact_lines:
        st.sidebar.markdown("\n".join(contact_lines))

    if social_links:
        st.sidebar.markdown("#### 🔗 링크")
        for label, url in social_links.items():
            if url:
                st.sidebar.markdown(f"- [{label}]({url})")

    st.sidebar.divider()

    st.sidebar.subheader("📂 탐색")
    page = st.sidebar.selectbox(
        "페이지를 선택하세요",
        ["🏠 홈", "👤 소개", "💼 프로젝트", "📞 연락처"],
        key="sidebar_page",
    )

    if error_message:
        st.sidebar.error(error_message)

    st.sidebar.info(
        "이 포트폴리오는 [GitHub 저장소](https://github.com/Themath93/portfolio-streamlit-codex)에서 확인할 수 있습니다. "
        "Codex 를 사용하여 개발했습니다."
    )
    return page


def render_home_navigation_button() -> None:
    """페이지 상단에 홈으로 이동하는 버튼을 출력한다.

    Returns:
        None: 반환값이 없다.
    """
    button_key = f"home_nav_button_{st.session_state.get('sidebar_page', 'home')}"

    if st.session_state.get("sidebar_page") != "🏠 홈":
        if st.button("🏠 홈으로 돌아가기", key=button_key):
            st.session_state["navigate_to_home"] = True
            st.experimental_rerun()


def prepare_chat_chain(pdf_path: Path) -> Tuple[Optional[Any], Optional[str]]:
    """챗봇 체인을 준비하고 오류 메시지를 반환한다.

    환경 변수 `OPENAI_API_KEY`가 설정되어 있어야 OpenAI 기반 체인을 초기화할 수 있다.

    Args:
        pdf_path (Path): 포트폴리오 PDF 파일 경로.

    Returns:
        Tuple[Optional[Any], Optional[str]]: 준비된 체인과 오류 메시지.
    """

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None, "환경 변수 `OPENAI_API_KEY`를 설정한 뒤 다시 시도해주세요."

    if not pdf_path.exists():
        return None, f"포트폴리오 PDF 파일이 존재하지 않습니다: {pdf_path}"

    try:
        chain = initialize_project_chat_chain_cached(str(pdf_path))
    except Exception as error:  # pylint: disable=broad-except
        return None, f"챗봇 초기화 중 오류가 발생했습니다: {error}"

    return chain, None


def prepare_chat_assistant(
    assets_dir: Path, json_path: Path
) -> Tuple[Optional[PortfolioChatAssistant], Optional[str]]:
    """홈 화면 챗봇 어시스턴트를 준비한다.

    Args:
        assets_dir (Path): 포트폴리오 에셋 디렉터리 경로.
        json_path (Path): 포트폴리오 JSON 데이터 경로.

    Returns:
        Tuple[Optional[PortfolioChatAssistant], Optional[str]]: 어시스턴트와 오류 메시지.
    """

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None, "환경 변수 `OPENAI_API_KEY`를 설정한 뒤 다시 시도해주세요."

    try:
        assistant = initialize_portfolio_assistant_cached(
            str(assets_dir), str(json_path)
        )
    except Exception as error:  # pylint: disable=broad-except
        return None, f"홈 챗봇 초기화 중 오류가 발생했습니다: {error}"

    return assistant, None


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


def _parse_project_period_start(period: str) -> datetime:
    """프로젝트 기간 문자열에서 시작 월을 파싱한다.

    Args:
        period (str): ``YYYY.MM ~ YYYY.MM`` 형식의 기간 문자열.

    Returns:
        datetime: 추출한 시작 연월을 나타내는 ``datetime`` 객체. 파싱 실패 시 ``datetime.max``를 반환한다.
    """

    if not period:
        return datetime.max

    match = re.search(r"(\d{4})[./-]\s*(\d{1,2})", period)
    if not match:
        return datetime.max

    year_str, month_str = match.groups()
    try:
        return datetime(int(year_str), int(month_str), 1)
    except ValueError:
        return datetime.max


def _project_sort_key(project: Dict[str, Any]) -> Tuple[datetime, str]:
    """프로젝트 정렬을 위한 키 튜플을 생성한다.

    Args:
        project (Dict[str, Any]): 프로젝트 정보를 담은 사전.

    Returns:
        Tuple[datetime, str]: 시작 연월과 프로젝트 제목을 담은 정렬 키.
    """

    period_value = project.get("period", "")
    start_period = _parse_project_period_start(str(period_value))
    title_value = project.get("title", "") or ""
    return start_period, title_value


def _emphasize_key_phrases(text: str) -> str:
    """핵심 수치와 키워드를 강조하여 시각적으로 돋보이게 만든다.

    Args:
        text (str): 강조 처리를 적용할 원본 문자열.

    Returns:
        str: 강조 처리가 적용된 문자열. 입력이 비어 있으면 빈 문자열을 반환한다.
    """

    if not text:
        return ""

    updated_text = str(text)

    numeric_patterns = [
        re.compile(r"\d{4}\.\d{2}"),
        re.compile(r"\d+(?:[.,]\d+)?%"),
        re.compile(r"\d+(?:[.,]\d+)?\s*(?:만|억|배|분|초|건|원|회)"),
        re.compile(r"\d+(?:[.,]\d+)?\s*(?:시간|개월|일)")
    ]

    def replace_with_bold(match: Match[str]) -> str:
        matched_text = match.group(0)
        if matched_text.startswith("**") and matched_text.endswith("**"):
            return matched_text
        return f"**{matched_text}**"

    for pattern in numeric_patterns:
        updated_text = pattern.sub(replace_with_bold, updated_text)

    highlight_keywords = [
        "실시간",
        "준실시간",
        "절감",
        "단축",
        "증가",
        "향상",
        "개선",
        "출시",
        "안정적",
        "확장성",
        "성공"
    ]

    for keyword in highlight_keywords:
        pattern = re.compile(rf"(?<!\*){re.escape(keyword)}(?!\*)")
        updated_text = pattern.sub(f"**{keyword}**", updated_text)

    return updated_text


def render_home_chatbot_section(
    assistant: Optional[PortfolioChatAssistant],
    assistant_error: Optional[str],
) -> None:
    """홈 화면 하단의 LangChain 챗봇 섹션을 렌더링한다.

    Args:
        assistant (Optional[PortfolioChatAssistant]): 대화 생성을 담당할 어시스턴트.
        assistant_error (Optional[str]): 초기화 오류 메시지.
    """

    st.markdown("---")
    st.markdown("## 🤖 LangChain + FAISS 포트폴리오 챗봇")

    if assistant_error:
        st.error(assistant_error)
        return

    if assistant is None:
        st.info(
            "OpenAI API 키를 설정하면 포트폴리오 챗봇과 대화할 수 있습니다. "
            "`.env` 파일 또는 환경 변수에 `OPENAI_API_KEY`를 등록한 뒤 페이지를 새로고침하세요."
        )
        return

    latest_exchange = st.session_state.get("latest_exchange")
    if latest_exchange:
        st.markdown("#### 최근 질의응답 스냅샷")
        with st.container():
            with st.chat_message("user"):
                st.markdown(latest_exchange.get("question", ""))
            with st.chat_message("assistant"):
                st.markdown(latest_exchange.get("answer", ""))
                caption_text = (
                    "🔍 벡터 검색 기반 답변"
                    if latest_exchange.get("used_retriever")
                    else "💡 요약 정보 기반 답변"
                )
                st.caption(caption_text)

    suggestions = st.session_state.get("follow_up_options", [])
    if suggestions:
        with st.container():
            st.markdown("#### 서류 검토 담당자가 궁금해할 질문 추천")
            st.caption("선택 후 버튼을 누르면 해당 질문으로 대화가 이어집니다.")
            selected_question = st.selectbox(
                "후속 질문 선택",
                options=suggestions,
                key="follow_up_select",
            )
            if st.button("선택한 질문으로 이어가기", key="follow_up_trigger"):
                st.session_state["auto_generated_question"] = selected_question
                st.session_state["follow_up_options"] = []
                st.experimental_rerun()

    auto_question = st.session_state.pop("auto_generated_question", None)
    manual_prompt = st.chat_input("포트폴리오에 대해 궁금한 점을 입력하세요.")
    user_prompt = auto_question or manual_prompt

    if not user_prompt:
        return

    previous_history = list(st.session_state["chat_history"])
    st.session_state["follow_up_options"] = []
    st.session_state["chat_history"].append({"role": "user", "content": user_prompt})

    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("답변을 준비하고 있습니다..."):
                stream_iterator, metadata = assistant.generate_answer_stream(
                    user_prompt, previous_history
                )
        except Exception:  # pylint: disable=broad-except
            error_text = (
                "죄송합니다. 챗봇 응답을 생성하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            )
            st.error(error_text)
            st.session_state["chat_history"].append(
                {"role": "assistant", "content": error_text}
            )
            return

        answer = st.write_stream(stream_iterator)
        result = metadata.finalize(answer)

        used_retriever = result.get("used_retriever", False)
        caption_text = "🔍 벡터 검색 기반 답변" if used_retriever else "💡 요약 정보 기반 답변"
        st.caption(caption_text)

        st.session_state["chat_history"].append({"role": "assistant", "content": answer})
        st.session_state["latest_exchange"] = {
            "question": user_prompt,
            "answer": answer,
            "used_retriever": used_retriever,
        }
        st.session_state["chat_history"] = st.session_state["chat_history"][-12:]

        context_docs: Sequence[Any] = result.get("context", [])
        if context_docs:
            with st.expander("🔍 참고한 문맥 보기"):
                for index, doc in enumerate(context_docs, start=1):
                    metadata = getattr(doc, "metadata", {}) or {}
                    source = metadata.get("source")
                    title = f"**문서 {index}**"
                    if source:
                        title += f" · {source}"
                    st.markdown(title)
                    st.write(getattr(doc, "page_content", ""))

        follow_up_options = (result.get("follow_ups") or [])[:3]
        st.session_state["follow_up_options"] = follow_up_options


def render_home_page(
    portfolio_data: Optional[Dict[str, Any]],
    error_message: Optional[str],
    assistant: Optional[PortfolioChatAssistant],
    assistant_error: Optional[str],
) -> None:
    """포트폴리오 데이터를 기반으로 홈 화면 콘텐츠를 렌더링한다.

    Args:
        portfolio_data (Optional[Dict[str, Any]]): ``portfolio_data.json``에서 로드한 데이터.
        error_message (Optional[str]): 데이터 로드 실패 시 사용자에게 안내할 오류 메시지.
        assistant (Optional[PortfolioChatAssistant]): 홈 화면에서 사용할 챗봇 어시스턴트.
        assistant_error (Optional[str]): 챗봇 초기화 오류 메시지.
    """

    render_home_navigation_button()

    if error_message:
        st.error(error_message)
        st.info("`portfolio_data.json` 파일이 존재하고 올바른 형식인지 확인해주세요.")
        return

    if not portfolio_data:
        st.info("표시할 포트폴리오 데이터가 없습니다. JSON 파일을 업데이트한 뒤 다시 시도해주세요.")
        return

    personal_info = portfolio_data.get("personal_info", {})
    about_info = portfolio_data.get("about", {})
    experience_items = portfolio_data.get("experience", [])
    skills = portfolio_data.get("skills", {}) if isinstance(portfolio_data, dict) else {}

    name = personal_info.get("name", "포트폴리오")
    title = personal_info.get("title", "전문가")

    interests = about_info.get("interests")
    hero_keywords: List[str] = []
    if isinstance(interests, list) and interests:
        hero_keywords = [str(keyword) for keyword in interests[:3]]
    elif isinstance(skills, dict):
        language_keys = list((skills.get("languages") or {}).keys())
        if language_keys:
            hero_keywords = [str(keyword) for keyword in language_keys[:3]]

    st.title(f"{name}의 포트폴리오")
    st.subheader(f"{title} · AI & 데이터 옹호자")
    if hero_keywords:
        st.markdown(" ".join(f"`{keyword}`" for keyword in hero_keywords))

    description = about_info.get("description")
    if description:
        st.write(description)
    else:
        st.info("자기소개를 `portfolio_data.json`의 `about.description`에 입력하면 이 영역에 표시됩니다.")

    st.divider()

    if isinstance(interests, list) and interests:
        st.subheader("관심 주제")
        st.markdown(" ".join(f"`{interest}`" for interest in interests))
        st.divider()

    educations = about_info.get("educations")
    if educations or experience_items:
        st.subheader("학력 및 경력")
        edu_col, exp_col = st.columns(2, gap="large")

        if educations:
            edu_col.markdown("#### 학력")
            for education in educations:
                edu_col.markdown(f"- {education}")
        else:
            edu_col.info("등록된 학력이 없습니다.")

        if experience_items:
            exp_col.markdown("#### 경력")
            for item in experience_items:
                period = item.get("period", "기간 미상")
                event = item.get("event", "세부 내용 미상")
                exp_col.markdown(f"- **{period}** · {event}")
        else:
            exp_col.info("등록된 경력 정보가 없습니다.")

        st.divider()

    skill_domains = build_skill_domains(skills)
    st.subheader("보유 기술")
    if skill_domains:
        domain_columns = st.columns(len(skill_domains), gap="large")
        for column, (domain_name, entries) in zip(domain_columns, skill_domains):
            column.markdown(f"#### {domain_name}")
            for entry in entries:
                column.markdown(f"- {entry}")
    else:
        st.info("기술 정보를 `skills` 항목에 등록하면 이 영역에 표시됩니다.")

    st.caption(f"📅 마지막 업데이트: {datetime.now().strftime('%Y년 %m월 %d일')}")

    render_home_chatbot_section(assistant, assistant_error)

def render_about_page(portfolio_data: Optional[Dict[str, Any]]) -> None:
    """소개 페이지 콘텐츠를 포트폴리오 데이터 기반으로 출력한다.

    Args:
        portfolio_data (Optional[Dict[str, Any]]): ``portfolio_data.json``에서 로드한 데이터.
    """

    st.title("👤 소개")
    render_home_navigation_button()

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


def render_projects_page(portfolio_data: Optional[Dict[str, Any]]) -> None:
    """프로젝트 데이터를 기반으로 상세 정보를 렌더링한다.

    Args:
        portfolio_data (Optional[Dict[str, Any]]): ``portfolio_data.json``에서 로드한 데이터.
    """

    st.title("💼 프로젝트 포트폴리오")
    render_home_navigation_button()

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

    sorted_projects = sorted(filtered_projects, key=_project_sort_key)

    for index, project in enumerate(sorted_projects):
        project_id = project.get("id", "")
        title_text = project.get("title", "이름 미정 프로젝트")
        with st.expander(f"📁 {title_text}", expanded=True):
            col1, col2 = st.columns([3, 2])

            with col1:
                company_text = project.get("company", "기관 미상")
                period_text = _emphasize_key_phrases(project.get("period", "기간 미상"))
                st.markdown(f"- 회사: **{company_text}**")
                st.markdown(f"- 기간: {period_text}")
                goal = project.get("goal")
                if goal:
                    goal_text = _emphasize_key_phrases(goal)
                    st.markdown(f"- 목표: {goal_text}")
                description = project.get("description")
                if description:
                    description_text = _emphasize_key_phrases(description)
                    st.markdown(f"- 설명: {description_text}")
                output = project.get("output")
                if output:
                    output_text = _emphasize_key_phrases(output)
                    st.markdown(f"- 성과: {output_text}")

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
            render_project_chat_section(project_id, title_text)


def render_contact_page(portfolio_data: Optional[Dict[str, Any]]) -> None:
    """포트폴리오 데이터를 활용하여 연락처 정보를 출력하고 메시지 폼을 제공한다.

    Args:
        portfolio_data (Optional[Dict[str, Any]]): `portfolio_data.json`에서 로드한 데이터.
    """

    st.title("📞 연락처 & 소셜 미디어")
    render_home_navigation_button()

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


def render_project_chat_section(project_id: str, project_title: str) -> None:
    """프로젝트 전용 챗봇 인터페이스를 렌더링한다.

    Args:
        project_id (str): ``portfolio_data.json``의 프로젝트 식별자.
        project_title (str): 사용자에게 표시할 프로젝트 제목.
    """

    st.markdown("---")
    st.subheader(f"🤖 {project_title} 대화형 문서 요약")

    pdf_path = resolve_project_pdf_path(project_id)
    if pdf_path is None:
        st.warning(
            "프로젝트에 연결된 PDF가 존재하지 않습니다. 'assets/projects' 경로에 파일을 배치해주세요."
        )
        return

    chat_chain, error_message = prepare_chat_chain(pdf_path)
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
    if st.session_state.pop("navigate_to_home", False):
        st.session_state["sidebar_page"] = "🏠 홈"
    portfolio_data, portfolio_error = prepare_portfolio_data(PORTFOLIO_DATA_PATH)
    page = render_sidebar_navigation(portfolio_data, portfolio_error)

    assistant: Optional[PortfolioChatAssistant] = None
    assistant_error: Optional[str] = None
    if page == "🏠 홈":
        assistant, assistant_error = prepare_chat_assistant(
            ASSETS_DIRECTORY, PORTFOLIO_DATA_PATH
        )

    if page == "🏠 홈":
        render_home_page(portfolio_data, portfolio_error, assistant, assistant_error)
    elif page == "👤 소개":
        render_about_page(portfolio_data)
    elif page == "💼 프로젝트":
        render_projects_page(portfolio_data)
    elif page == "📞 연락처":
        render_contact_page(portfolio_data)

    render_footer()


if __name__ == "__main__":
    main()
