from typing import List, Dict

from src.vector_store import VectorStore
from src.reranker import Reranker
from src.logger import get_logger
from config import RERANKER_TOP_K, FINAL_TOP_K, SUMMARY_TOP_K

logger = get_logger("retriever")


class Retriever:
    def __init__(self):
        self.vector_store = VectorStore()
        self.reranker = Reranker()

    def retrieve(self, query: str, top_k: int = FINAL_TOP_K) -> List[Dict]:
        logger.info(f"检索查询: {query[:50]}...")

        # 第一层：摘要检索，定位相关文档
        summaries = self.vector_store.query_summary(query, k=SUMMARY_TOP_K)
        sources = [s["metadata"].get("source", "") for s in summaries if s.get("metadata")]
        logger.info(f"定位到相关文档: {sources}")

        # 第二层：内容检索（优先在相关文档中检索，否则全局检索）
        if sources:
            candidates = self.vector_store.query_by_sources(query, sources, k=RERANKER_TOP_K)
        else:
            candidates = self.vector_store.query_content(query, k=RERANKER_TOP_K)

        # 第三层：重排序
        reranked = self.reranker.rerank(query, candidates, top_k=top_k)
        logger.info(f"返回 {len(reranked)} 个结果")
        return reranked
