import hashlib
import uuid
from typing import List, Optional

import chromadb
from chromadb.config import Settings

from config import CHROMA_PERSIST_DIR
from src.chunker import Chunk
from src.logger import get_logger

logger = get_logger("vector_store")


def _make_chunk_id(source: str, content: str, index: int) -> str:
    """生成全局唯一的 chunk ID，包含来源避免跨文档冲突。"""
    raw = f"{source}:{content}:{index}"
    return f"chunk_{hashlib.md5(raw.encode('utf-8')).hexdigest()}"


class VectorStore:
    def __init__(self):
        self._embeddings = None
        self._client = None
        self._content_collection = None
        self._summary_collection = None

    @property
    def embeddings(self):
        if self._embeddings is None:
            from src.embeddings import get_embeddings
            self._embeddings = get_embeddings()
        return self._embeddings

    @property
    def client(self):
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=CHROMA_PERSIST_DIR,
                settings=Settings(anonymized_telemetry=False)
            )
        return self._client

    @property
    def content_collection(self):
        if self._content_collection is None:
            self._content_collection = self.client.get_or_create_collection(
                name="document_content",
                metadata={"hnsw:space": "cosine"}
            )
        return self._content_collection

    @property
    def summary_collection(self):
        if self._summary_collection is None:
            self._summary_collection = self.client.get_or_create_collection(
                name="document_summary",
                metadata={"hnsw:space": "cosine"}
            )
        return self._summary_collection

    # ── 写入 ──

    def add_chunks(self, chunks: List[Chunk]) -> int:
        if not chunks:
            return 0
        logger.info(f"添加 {len(chunks)} 个文档片段到向量库")
        texts = [c.content for c in chunks]

        # 分批处理 embedding，避免超过 512 tokens 限制
        from src.embeddings import embed_documents_safe
        embeddings = embed_documents_safe(texts, batch_size=50)

        source = chunks[0].metadata.get("source", "") if chunks else ""
        ids = [_make_chunk_id(source, c.content, i) for i, c in enumerate(chunks)]
        metadatas = [{"source": c.metadata.get("source", ""),
                      "page": c.metadata.get("page", 0),
                      "type": c.chunk_type} for c in chunks]
        self.content_collection.upsert(
            ids=ids, documents=texts,
            embeddings=embeddings, metadatas=metadatas
        )
        return len(chunks)

    def add_summary(self, source: str, summary: str):
        # 截断 summary 避免超过 512 tokens 限制
        MAX_CHARS = 1500
        truncated_summary = summary[:MAX_CHARS] if len(summary) > MAX_CHARS else summary

        from src.embeddings import embed_documents_safe
        embeddings = embed_documents_safe([truncated_summary], batch_size=1)
        embedding = embeddings[0] if embeddings else []

        self.summary_collection.upsert(
            ids=[f"summary_{source}"],
            documents=[truncated_summary],
            embeddings=[embedding],
            metadatas=[{"source": source}]
        )

    # ── 查询（统一内部方法） ──

    def _query_collection(self, collection, query: str, k: int = 5,
                          where: Optional[dict] = None) -> List[dict]:
        embedding = self.embeddings.embed_query(query)
        kwargs = {"query_embeddings": [embedding], "n_results": k}
        if where:
            kwargs["where"] = where
        results = collection.query(**kwargs)
        items = []
        for i in range(len(results["ids"][0])):
            items.append({
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else 0
            })
        return items

    def query_content(self, query: str, k: int = 5) -> List[dict]:
        return self._query_collection(self.content_collection, query, k)

    def query_summary(self, query: str, k: int = 3) -> List[dict]:
        return self._query_collection(self.summary_collection, query, k)

    def query_by_sources(self, query: str, sources: List[str], k: int = 5) -> List[dict]:
        return self._query_collection(
            self.content_collection, query, k,
            where={"source": {"$in": sources}}
        )

    # ── 删除 ──

    def delete_by_source(self, source_name: str):
        """删除指定来源的所有 chunk 和摘要。"""
        logger.info(f"删除来源 '{source_name}' 的所有向量数据")
        try:
            self.content_collection.delete(where={"source": source_name})
        except Exception as e:
            logger.warning(f"删除 content 集合中的 '{source_name}' 失败: {e}")
        try:
            self.summary_collection.delete(ids=[f"summary_{source_name}"])
        except Exception as e:
            logger.warning(f"删除 summary 中的 '{source_name}' 失败: {e}")

    def delete_all(self):
        """清空所有向量数据。"""
        logger.info("清空所有向量数据")
        try:
            self.client.delete_collection("document_content")
            self.client.delete_collection("document_summary")
            self._content_collection = None
            self._summary_collection = None
        except Exception as e:
            logger.warning(f"清空向量库失败: {e}")

    # ── 统计 ──

    def get_stats(self) -> dict:
        """返回向量库统计信息。"""
        try:
            content_count = self.content_collection.count()
            summary_count = self.summary_collection.count()
            # 获取所有不重复的 source
            all_meta = self.content_collection.get(include=["metadatas"])
            sources = set()
            for m in all_meta.get("metadatas", []):
                if m and m.get("source"):
                    sources.add(m["source"])
            return {
                "chunk_count": content_count,
                "document_count": len(sources),
                "summary_count": summary_count,
                "sources": sorted(sources),
            }
        except Exception as e:
            logger.warning(f"获取统计信息失败: {e}")
            return {"chunk_count": 0, "document_count": 0, "summary_count": 0, "sources": []}
