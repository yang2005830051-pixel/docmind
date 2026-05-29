import os
from typing import List, Dict

from src.logger import get_logger

logger = get_logger("reranker")

# 配置 HuggingFace 镜像源（国内访问）
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")


class Reranker:
    def __init__(self):
        self._model = None
        self._available = None

    @property
    def model(self):
        if self._available is False:
            return None
        if self._model is None:
            from config import RERANKER_MODEL
            if not RERANKER_MODEL:
                self._available = False
                return None
            try:
                from sentence_transformers import CrossEncoder
                logger.info(f"加载 Reranker 模型: {RERANKER_MODEL}")
                self._model = CrossEncoder(RERANKER_MODEL)
                self._available = True
            except Exception as e:
                logger.warning(f"Reranker 模型加载失败，将跳过重排序: {e}")
                self._available = False
                return None
        return self._model

    def rerank(self, query: str, documents: List[Dict], top_k: int = 3) -> List[Dict]:
        if not documents:
            return []
        if self.model is None:
            return documents[:top_k]
        pairs = [(query, doc["content"]) for doc in documents]
        scores = self.model.predict(pairs)
        for i, doc in enumerate(documents):
            doc["rerank_score"] = float(scores[i])
        reranked = sorted(documents, key=lambda x: x["rerank_score"], reverse=True)
        return reranked[:top_k]
