import hashlib
from typing import List

import chromadb
from chromadb.config import Settings

from config import CHROMA_PERSIST_DIR
from src.chunker import Chunk
from src.logger import get_logger

logger = get_logger("vector_store")


def _make_chunk_id(content: str, index: int) -> str:
    return f"chunk_{index}_{hashlib.md5(content.encode('utf-8')).hexdigest()}"


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

    def add_chunks(self, chunks: List[Chunk]) -> int:
        if not chunks:
            return 0
        logger.info(f"添加 {len(chunks)} 个文档片段到向量库")
        texts = [c.content for c in chunks]
        embeddings = self.embeddings.embed_documents(texts)
        ids = [_make_chunk_id(c.content, i) for i, c in enumerate(chunks)]
        metadatas = [{"source": c.metadata.get("source", ""),
                      "page": c.metadata.get("page", 0),
                      "type": c.chunk_type} for c in chunks]
        self.content_collection.upsert(
            ids=ids, documents=texts,
            embeddings=embeddings, metadatas=metadatas
        )
        return len(chunks)

    def add_summary(self, source: str, summary: str):
        embedding = self.embeddings.embed_query(summary)
        self.summary_collection.upsert(
            ids=[f"summary_{source}"],
            documents=[summary],
            embeddings=[embedding],
            metadatas=[{"source": source}]
        )

    def query_content(self, query: str, k: int = 5) -> List[dict]:
        embedding = self.embeddings.embed_query(query)
        results = self.content_collection.query(
            query_embeddings=[embedding], n_results=k
        )
        items = []
        for i in range(len(results["ids"][0])):
            items.append({
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else 0
            })
        return items

    def query_summary(self, query: str, k: int = 3) -> List[dict]:
        embedding = self.embeddings.embed_query(query)
        results = self.summary_collection.query(
            query_embeddings=[embedding], n_results=k
        )
        items = []
        for i in range(len(results["ids"][0])):
            items.append({
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else 0
            })
        return items

    def query_by_sources(self, query: str, sources: List[str], k: int = 5) -> List[dict]:
        embedding = self.embeddings.embed_query(query)
        results = self.content_collection.query(
            query_embeddings=[embedding],
            n_results=k,
            where={"source": {"$in": sources}}
        )
        items = []
        for i in range(len(results["ids"][0])):
            items.append({
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else 0
            })
        return items
