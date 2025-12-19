"""
제주어 RAG 검색 서비스

ChromaDB를 사용한 벡터 기반 제주어 사전 검색
"""
import json
import os
import threading
from typing import List, Dict, Optional
import logging

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import settings

logger = logging.getLogger(__name__)


class JejuRAGService:
    """제주어 사전 기반 RAG 검색 서비스 (ChromaDB)"""

    def __init__(self):
        """OpenAI Embeddings 및 ChromaDB 초기화"""
        logger.info("JejuRAGService 초기화 시작...")
        self.embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key
        )
        self.vector_store = None
        self._initialize()
        logger.info("JejuRAGService 초기화 완료")

    def _initialize(self):
        """벡터 스토어 로드 또는 생성"""
        # ChromaDB는 persist_directory가 있으면 자동으로 로드
        chroma_path = os.path.join(os.getcwd(), settings.jeju_chroma_path)

        if os.path.exists(chroma_path):
            logger.info(f"기존 ChromaDB 로드 중... ({chroma_path})")
            try:
                self.vector_store = Chroma(
                    collection_name="jeju_dictionary",
                    embedding_function=self.embeddings,
                    persist_directory=chroma_path
                )
                logger.info("ChromaDB 로드 완료")
            except Exception as e:
                logger.warning(f"ChromaDB 로드 실패, 새로 생성합니다: {str(e)}")
                self._build_vector_store()
        else:
            logger.info("ChromaDB가 없습니다. 새로 생성합니다...")
            self._build_vector_store()

    def _load_dictionary(self) -> List[Dict]:
        """JSON 파일에서 사전 로드"""
        dict_path = os.path.join(os.getcwd(), settings.jeju_dictionary_path)
        logger.info(f"제주어 사전 로드 중... ({dict_path})")

        with open(dict_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"제주어 사전 로드 완료: {len(data['entries'])}개 항목")
        return data['entries']

    def _build_vector_store(self):
        """ChromaDB 컬렉션 생성"""
        logger.info("ChromaDB 벡터 스토어 생성 중...")
        entries = self._load_dictionary()
        documents = []

        for entry in entries:
            # 문서 내용 구성 (검색에 사용될 텍스트)
            text = f"표준어: {entry['standard']}\n제주어: {entry['jeju']}\n"
            if 'context' in entry and entry['context']:
                text += f"문맥: {entry['context']}\n"
            if 'category' in entry:
                text += f"카테고리: {entry['category']}\n"
            if 'pos' in entry:
                text += f"품사: {entry['pos']}\n"

            # 메타데이터는 별도로 저장 (ChromaDB 장점 활용)
            metadata = {
                "id": entry['id'],
                "standard": entry['standard'],
                "jeju": entry['jeju'],
                "category": entry.get('category', ''),
                "pos": entry.get('pos', ''),
                "frequency": entry.get('frequency', '')
            }

            documents.append(Document(page_content=text, metadata=metadata))

        # ChromaDB 생성 및 저장
        chroma_path = os.path.join(os.getcwd(), settings.jeju_chroma_path)
        os.makedirs(chroma_path, exist_ok=True)

        self.vector_store = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            collection_name="jeju_dictionary",
            persist_directory=chroma_path
        )

        logger.info(f"ChromaDB 생성 완료: {len(documents)}개 항목, 저장 경로: {chroma_path}")

    def search(
        self,
        query: str,
        top_k: int = 5,
        category_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        유사도 검색

        Args:
            query: 검색 쿼리 (표준어 문장)
            top_k: 반환할 결과 수
            category_filter: 카테고리 필터 (예: "인사", "감정")

        Returns:
            검색된 제주어 표현 리스트
        """
        if not self.vector_store:
            logger.error("ChromaDB가 초기화되지 않았습니다.")
            return []

        # 메타데이터 필터 (ChromaDB 장점!)
        filter_dict = None
        if category_filter:
            filter_dict = {"category": category_filter}
            logger.debug(f"카테고리 필터 적용: {category_filter}")

        try:
            # 검색 수행
            results = self.vector_store.similarity_search_with_score(
                query,
                k=top_k,
                filter=filter_dict
            )

            # 결과 포맷팅
            formatted_results = []
            for doc, score in results:
                # 유사도 임계값 필터링 (선택적)
                # ChromaDB는 L2 distance 사용 (낮을수록 유사)
                # 일반적으로 0~2 범위, 0.5 이하면 매우 유사
                if score > settings.rag_similarity_threshold:
                    continue

                formatted_results.append({
                    "standard": doc.metadata['standard'],
                    "jeju": doc.metadata['jeju'],
                    "category": doc.metadata.get('category', ''),
                    "similarity": 1 - min(score, 1.0)  # 0-1 범위로 변환 (1에 가까울수록 유사)
                })

            logger.info(f"RAG 검색 완료: '{query}' → {formatted_results}")
            return formatted_results

        except Exception as e:
            logger.error(f"검색 중 오류 발생: {str(e)}")
            return []

    def rebuild_index(self):
        """사전 업데이트 시 재구축"""
        logger.info("ChromaDB 재구축 시작...")

        # 기존 컬렉션 삭제
        if self.vector_store:
            try:
                self.vector_store.delete_collection()
                logger.info("기존 ChromaDB 컬렉션 삭제 완료")
            except Exception as e:
                logger.warning(f"컬렉션 삭제 실패 (무시): {str(e)}")

        # 새로 구축
        self._build_vector_store()
        logger.info("ChromaDB 재구축 완료")


class JejuRAGServiceSingleton:
    """싱글톤 관리 (thread-safe)"""
    _instance: Optional[JejuRAGService] = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> JejuRAGService:
        """
        싱글톤 인스턴스 반환

        Double-check locking 패턴을 사용하여 thread-safe하게 인스턴스를 생성합니다.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = JejuRAGService()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """인스턴스 초기화 (테스트용)"""
        with cls._lock:
            cls._instance = None
