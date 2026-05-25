from typing import List, Dict


class Reranker:
    def __init__(self):
        self._model = None
        self._available = None

    @property
    def model(self):
        if self._available is False:
            return None
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                from config import RERANKER_MODEL
                self._model = CrossEncoder(RERANKER_MODEL)
                self._available = True
            except Exception as e:
                print(f"Reranker 模型加载失败，将跳过重排序: {e}")
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
