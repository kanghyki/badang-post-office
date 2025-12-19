"""
RAG 시스템 테스트 스크립트

ChromaDB 초기화 및 검색 기능을 테스트합니다.
"""
import sys
import os
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(__file__))

# 환경 변수 로드 (먼저!)
from dotenv import load_dotenv
load_dotenv()

from app.services.jeju_rag_service import JejuRAGServiceSingleton


def test_rag_initialization():
    """RAG 서비스 초기화 테스트"""
    print("=" * 80)
    print("RAG 서비스 초기화 테스트")
    print("=" * 80)

    try:
        rag_service = JejuRAGServiceSingleton.get_instance()
        print("✅ RAG 서비스 초기화 성공!")
        return rag_service
    except Exception as e:
        print(f"❌ RAG 서비스 초기화 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_rag_search(rag_service):
    """RAG 검색 테스트"""
    print("\n" + "=" * 80)
    print("RAG 검색 테스트")
    print("=" * 80)

    test_queries = [
        "안녕하세요",
        "고맙습니다",
        "날씨가 좋아요",
        "맛있어요",
        "보고 싶어요"
    ]

    for query in test_queries:
        print(f"\n📝 검색 쿼리: '{query}'")
        try:
            results = rag_service.search(query, top_k=3)
            if results:
                print(f"   검색 결과: {len(results)}개")
                for i, result in enumerate(results, 1):
                    print(f"   {i}. {result['standard']} → {result['jeju']} "
                          f"(카테고리: {result['category']}, 유사도: {result['similarity']:.3f})")
            else:
                print("   ⚠️  검색 결과 없음")
        except Exception as e:
            print(f"   ❌ 검색 실패: {str(e)}")


def test_category_filter(rag_service):
    """카테고리 필터 테스트"""
    print("\n" + "=" * 80)
    print("카테고리 필터 테스트")
    print("=" * 80)

    query = "안녕"
    categories = ["인사", "일상", "감정"]

    for category in categories:
        print(f"\n📂 카테고리: '{category}'로 '{query}' 검색")
        try:
            results = rag_service.search(query, top_k=3, category_filter=category)
            if results:
                print(f"   검색 결과: {len(results)}개")
                for i, result in enumerate(results, 1):
                    print(f"   {i}. {result['standard']} → {result['jeju']}")
            else:
                print("   ⚠️  검색 결과 없음")
        except Exception as e:
            print(f"   ❌ 검색 실패: {str(e)}")


def main():
    """메인 테스트 함수"""
    print("\n🚀 RAG 시스템 테스트 시작\n")

    # 1. RAG 초기화
    rag_service = test_rag_initialization()
    if not rag_service:
        print("\n❌ RAG 서비스 초기화 실패로 테스트 중단")
        return

    # 2. RAG 검색 테스트
    test_rag_search(rag_service)

    # 3. 카테고리 필터 테스트
    test_category_filter(rag_service)

    print("\n" + "=" * 80)
    print("✅ 모든 테스트 완료!")
    print("=" * 80)


if __name__ == "__main__":
    main()
