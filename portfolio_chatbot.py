"""포트폴리오 챗봇 생성을 담당하는 도우미 모듈."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.schema import AIMessage, BaseMessage, Document, HumanMessage, SystemMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from utils.pdf_to_text_process import convert_pdf_to_text


def load_portfolio_documents(assets_dir: Path, json_path: Path) -> List[Document]:
    """에셋 디렉터리와 JSON 파일을 로드해 임베딩 가능한 문서 목록을 생성한다.

    Args:
        assets_dir (Path): 포트폴리오 관련 정적 자산이 위치한 디렉터리 경로.
        json_path (Path): `portfolio_data.json` 파일 경로.

    Returns:
        List[Document]: LangChain 문서 객체 리스트.

    Raises:
        FileNotFoundError: 지정한 디렉터리 또는 JSON 파일이 존재하지 않을 때 발생한다.
    """

    if not assets_dir.exists() or not assets_dir.is_dir():
        raise FileNotFoundError(f"에셋 디렉터리를 찾을 수 없습니다: {assets_dir}")
    if not json_path.exists():
        raise FileNotFoundError(f"포트폴리오 데이터 파일을 찾을 수 없습니다: {json_path}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    documents: List[Document] = []

    for path in sorted(assets_dir.rglob("*")):
        if path.is_dir():
            continue
        suffix = path.suffix.lower()
        metadata = {"source": str(path.relative_to(assets_dir))}
        if suffix == ".pdf":
            loader = PyPDFLoader(str(path))
            pdf_docs = loader.load()
            documents.extend(splitter.split_documents(pdf_docs))
        elif suffix in {".txt", ".md"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            documents.extend(splitter.split_documents([Document(page_content=text, metadata=metadata)]))

    json_text = json_path.read_text(encoding="utf-8")
    json_document = Document(page_content=json_text, metadata={"source": json_path.name})
    documents.extend(splitter.split_documents([json_document]))

    if not documents:
        raise ValueError("임베딩할 문서를 찾을 수 없습니다. PDF 또는 텍스트 자료를 추가해주세요.")

    return documents


def load_project_documents(pdf_path: Path) -> List[Document]:
    """단일 프로젝트 PDF를 청크 단위 문서로 변환한다.

    Args:
        pdf_path (Path): 임베딩 대상이 되는 프로젝트 PDF 경로.

    Returns:
        List[Document]: 분할된 문서 리스트.

    Raises:
        FileNotFoundError: PDF 파일이 존재하지 않을 때 발생한다.
    """

    if not pdf_path.exists():
        raise FileNotFoundError(f"프로젝트 PDF를 찾을 수 없습니다: {pdf_path}")

    pdf_text = convert_pdf_to_text(pdf_path)
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    documents = splitter.split_documents([Document(page_content=pdf_text, metadata={"source": pdf_path.name})])
    return documents


def build_vector_store(documents: Iterable[Document]) -> FAISS:
    """문서 임베딩을 생성하고 FAISS 기반 벡터 저장소를 초기화한다.

    Args:
        documents (Iterable[Document]): 임베딩할 문서 객체 모음.

    Returns:
        FAISS: 포트폴리오 정보를 담고 있는 벡터 저장소 인스턴스.
    """

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return FAISS.from_documents(list(documents), embedding=embeddings)


def create_multi_query_retriever(vector_store: FAISS) -> MultiQueryRetriever:
    """MultiQueryRetriever를 생성하여 다양한 관점의 검색을 지원한다.

    Args:
        vector_store (FAISS): 검색 대상이 되는 벡터 저장소.

    Returns:
        MultiQueryRetriever: 복수 질의 기반의 리트리버 인스턴스.
    """

    query_llm = ChatOpenAI(model="gpt-5-mini", temperature=0.2)
    base_retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    return MultiQueryRetriever.from_llm(retriever=base_retriever, llm=query_llm)


def create_portfolio_chain(vector_store: FAISS) -> Any:
    """포트폴리오 질의 응답 체인을 구성한다.

    Args:
        vector_store (FAISS): 검색을 수행할 벡터 저장소.

    Returns:
        Any: 검색과 응답 생성을 결합한 실행 체인.
    """

    answer_llm = ChatOpenAI(model="gpt-5-mini", temperature=0.2)
    retriever = create_multi_query_retriever(vector_store)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "당신은 사용자의 포트폴리오를 안내하는 전문 챗봇입니다. "
                "다음에 제공되는 문서 조각을 기반으로 사실에 충실한 답변을 제공하세요. "
                "답변에는 문맥이 부족할 경우 그렇게 명시하고, 확인되지 않은 정보는 추측하지 마세요.",
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            (
                "human",
                "사용자 질문: {input}\n\n"
                "포트폴리오 문맥:\n{context}\n\n"
                "위 정보를 활용해 전문적이고 간결한 한국어 답변을 작성하세요.",
            ),
        ]
    )
    document_chain = create_stuff_documents_chain(answer_llm, prompt)
    return create_retrieval_chain(retriever, document_chain)


def build_langchain_history(history: Sequence[dict]) -> List[BaseMessage]:
    """Streamlit 세션 히스토리를 LangChain 메시지 형식으로 변환한다.

    Args:
        history (Sequence[dict]): `role`, `content` 키를 포함한 대화 내역.

    Returns:
        List[BaseMessage]: LangChain에서 사용하는 메시지 객체 리스트.
    """

    converted: List[BaseMessage] = []
    for message in history:
        role = message.get("role")
        content = message.get("content", "")
        if role == "user":
            converted.append(HumanMessage(content=content))
        elif role == "assistant":
            converted.append(AIMessage(content=content))
    return converted


def _serialize_portfolio_summary(json_path: Path) -> str:
    """포트폴리오 JSON 파일을 요약 문자열로 직렬화한다.

    Args:
        json_path (Path): 포트폴리오 데이터 JSON 경로.

    Returns:
        str: LLM에 제공할 수 있는 JSON 문자열.
    """

    data = json.loads(json_path.read_text(encoding="utf-8"))
    return json.dumps(data, ensure_ascii=False, indent=2)


@dataclass
class PortfolioChatAssistant:
    """포트폴리오 대화를 총괄하는 LangChain 기반 어시스턴트."""

    retrieval_chain: Any
    summary_text: str
    response_llm: ChatOpenAI
    classifier_llm: ChatOpenAI
    follow_up_llm: ChatOpenAI
    classifier_prompt: ChatPromptTemplate
    direct_prompt: ChatPromptTemplate
    follow_up_prompt: ChatPromptTemplate

    def decide_retrieval(self, question: str) -> bool:
        """질문에 대해 문서 검색이 필요한지 판별한다.

        Args:
            question (str): 사용자가 입력한 자연어 질문.

        Returns:
            bool: 검색이 필요하면 ``True``.
        """

        messages = self.classifier_prompt.format_messages(
            question=question,
            summary=self.summary_text,
        )
        response = self.classifier_llm.invoke(messages)
        decision = response.content.strip().upper()
        return "RETRIEVE" in decision

    def generate_answer(self, question: str, history: Sequence[dict]) -> Dict[str, Any]:
        """질문에 대한 답변과 후속 질문을 생성한다.

        Args:
            question (str): 사용자의 입력.
            history (Sequence[dict]): 대화 히스토리.

        Returns:
            Dict[str, Any]: 답변, 참고 문맥, 후속 질문, 검색 여부를 포함한 결과.
        """

        should_retrieve = self.decide_retrieval(question)
        langchain_history = build_langchain_history(history)

        if should_retrieve:
            result: Dict[str, Any] = self.retrieval_chain.invoke(
                {"input": question, "chat_history": langchain_history}
            )
            answer = result.get("answer", "요청에 대한 답변을 생성하지 못했습니다.")
            context = result.get("context", [])
        else:
            messages = self.direct_prompt.format_messages(
                question=question,
                chat_history=langchain_history,
                summary=self.summary_text,
            )
            response = self.response_llm.invoke(messages)
            answer = response.content
            context = []

        follow_up_messages = self.follow_up_prompt.format_messages(
            question=question,
            answer=answer,
            summary=self.summary_text,
        )
        follow_up_response = self.follow_up_llm.invoke(follow_up_messages)
        follow_up_questions = _parse_follow_up_questions(follow_up_response.content)

        return {
            "answer": answer,
            "context": context,
            "follow_ups": follow_up_questions,
            "used_retriever": should_retrieve,
        }


def _parse_follow_up_questions(raw_text: str) -> List[str]:
    """후속 질문 후보 텍스트를 파싱한다.

    Args:
        raw_text (str): LLM이 생성한 후속 질문 텍스트.

    Returns:
        List[str]: 질문 문자열 리스트.
    """

    try:
        parsed = json.loads(raw_text)
        if isinstance(parsed, list):
            return [str(item) for item in parsed if str(item).strip()]
    except json.JSONDecodeError:
        lines = [line.strip(" -") for line in raw_text.splitlines()]
        return [line for line in lines if line]
    return []


def create_portfolio_assistant(assets_dir: Path, json_path: Path) -> PortfolioChatAssistant:
    """포트폴리오 대화를 담당하는 어시스턴트를 생성한다.

    Args:
        assets_dir (Path): 포트폴리오 에셋 디렉터리.
        json_path (Path): 포트폴리오 JSON 파일 경로.

    Returns:
        PortfolioChatAssistant: 대화형 포트폴리오 어시스턴트 인스턴스.
    """

    documents = load_portfolio_documents(assets_dir, json_path)
    vector_store = build_vector_store(documents)
    retrieval_chain = create_portfolio_chain(vector_store)
    summary_text = _serialize_portfolio_summary(json_path)

    response_llm = ChatOpenAI(model="gpt-5-mini", temperature=0.3)
    classifier_llm = ChatOpenAI(model="gpt-5-mini", temperature=0)
    follow_up_llm = ChatOpenAI(model="gpt-5-mini", temperature=0.4)

    classifier_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "너는 채용 담당자가 궁금해하는 질문이 포트폴리오 원문을 검색해야 하는지를 판단하는 분석가다. "
                "검색이 필요하면 RETRIEVE, 요약된 정보만으로 답할 수 있으면 DIRECT 라고만 출력해라.",
            ),
            (
                "human",
                "질문: {question}\n\n포트폴리오 개요:\n{summary}\n",
            ),
        ]
    )

    direct_prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=(
                    "너는 지원자의 포트폴리오를 설명하는 AI 어시스턴트다. "
                    "요약 정보와 대화 맥락을 활용해 정확하고 구체적으로 답변해라."
                )
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            (
                "human",
                "사용자 질문: {question}\n\n포트폴리오 요약:\n{summary}\n\n"
                "맥락이 부족하면 그렇게 명시하고, 포트폴리오와 무관한 질문에는 정중히 답변을 제한해라.",
            ),
        ]
    )

    follow_up_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "너는 채용 담당자가 흥미를 가질 후속 질문을 제안하는 어시스턴트다. "
                "최대 세 개의 질문을 JSON 배열 형태로 출력해라.",
            ),
            (
                "human",
                "기존 질문: {question}\n답변: {answer}\n포트폴리오 요약:\n{summary}\n"
                "채용 담당자가 추가로 물어볼 만한 짧은 질문을 제안해라.",
            ),
        ]
    )

    return PortfolioChatAssistant(
        retrieval_chain=retrieval_chain,
        summary_text=summary_text,
        response_llm=response_llm,
        classifier_llm=classifier_llm,
        follow_up_llm=follow_up_llm,
        classifier_prompt=classifier_prompt,
        direct_prompt=direct_prompt,
        follow_up_prompt=follow_up_prompt,
    )
