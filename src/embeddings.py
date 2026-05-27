import time
from langchain_openai import OpenAIEmbeddings

from config import OPENAI_API_KEY, EMBEDDING_MODEL, EMBEDDING_MAX_RETRIES
from src.logger import get_logger

logger = get_logger("embeddings")


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY,
        max_retries=EMBEDDING_MAX_RETRIES,
        request_timeout=30,
    )


def embed_documents_safe(texts: list[str], batch_size: int = 100) -> list[list[float]]:
    """带重试的批量嵌入，处理大文档集。"""
    embeddings = get_embeddings()
    all_vecs = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        for attempt in range(EMBEDDING_MAX_RETRIES):
            try:
                vecs = embeddings.embed_documents(batch)
                all_vecs.extend(vecs)
                break
            except Exception as e:
                if attempt == EMBEDDING_MAX_RETRIES - 1:
                    logger.error(f"嵌入失败 (batch {i}): {e}")
                    raise
                delay = 1.0 * (attempt + 1)
                logger.warning(f"嵌入请求失败，{delay}s 后重试: {e}")
                time.sleep(delay)
    return all_vecs
