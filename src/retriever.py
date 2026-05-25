from typing import List, Dict

from src.vector_store import VectorStore
from src.reranker import Reranker
from src.logger import get_logger
from config import RERANKER_TOP_K, FINAL_TOP_K

logger = get_logger("retriever")


class Retriever:
    def __init__(self):
        self.vector_store = VectorStore()
        self.reranker = Reranker()

    def retrieve(self, query: str, top_k: int = FINAL_TOP_K) -> List[Dict]:
        logger.info(f"检索查询: {query[:50]}...")
        summaries = self.vector_store.query_summary(query, k=3)
        sources = [s["metadata"].get("source", "") for s in summaries if s.get("metadata")]
        logger.info(f"定位到相关文档: {sources}")
        if sources:
            candidates = self.vector_store.query_by_sources(query, sources, k=RERANKER_TOP_K)
        else:
            candidates = self.vector_store.query_content(query, k=RERANKER_TOP_K)
        if not candidates:
            candidates = self.vector_store.query_content(query, k=RERANKER_TOP_K)
        reranked = self.reranker.rerank(query, candidates, top_k=top_k)
        logger.info(f"返回 {len(reranked)} 个结果")
        return reranked
