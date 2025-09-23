"""포트폴리오 챗봇 생성을 담당하는 도우미 모듈."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, List, Sequence

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.schema import AIMessage, BaseMessage, Document, HumanMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


def load_portfolio_documents(pdf_path: Path) -> List[Document]:
    """포트폴리오 PDF 문서를 로드하여 청크 단위의 문서 리스트를 생성한다.

    Args:
        pdf_path (Path): 임베딩할 포트폴리오 PDF의 경로.

    Returns:
        List[Document]: 텍스트 청크 단위로 분할된 문서 객체 리스트.
    """
    loader = PyPDFLoader(str(pdf_path))
    documents = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    return splitter.split_documents(documents)


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
    query_llm = ChatOpenAI(model="gpt-5-mini", temperature=0.3)
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
