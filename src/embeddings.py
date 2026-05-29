import time
from langchain_openai import OpenAIEmbeddings

from config import (
    OPENAI_API_KEY, EMBEDDING_MODEL, EMBEDDING_MAX_RETRIES,
    MIMO_API_KEY, MIMO_BASE_URL, SILICONFLOW_EMBEDDING_MODEL,
    get_embedding_provider,
)
from src.logger import get_logger

logger = get_logger("embeddings")


def get_embeddings() -> OpenAIEmbeddings:
    provider = get_embedding_provider()

    if provider == "openai":
        return OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            openai_api_key=OPENAI_API_KEY,
            max_retries=EMBEDDING_MAX_RETRIES,
            request_timeout=30,
        )

    elif provider == "siliconflow":
        return OpenAIEmbeddings(
            model=SILICONFLOW_EMBEDDING_MODEL,
            openai_api_key=MIMO_API_KEY,
            openai_api_base=MIMO_BASE_URL,
            max_retries=EMBEDDING_MAX_RETRIES,
            request_timeout=30,
        )

    else:
        raise ValueError(
            "未配置嵌入 API Key，请设置 OPENAI_API_KEY 或 MIMO_API_KEY"
        )


def embed_documents_safe(texts: list[str], batch_size: int = 50) -> list[list[float]]:
    """带重试的批量嵌入，处理大文档集。自动截断超长文本。"""
    embeddings = get_embeddings()

    # 截断超长文本（约 512 tokens ≈ 1500 字符）
    MAX_CHARS = 1500
    truncated_texts = []
    for text in texts:
        if len(text) > MAX_CHARS:
            truncated_texts.append(text[:MAX_CHARS])
        else:
            truncated_texts.append(text)

    all_vecs = []
    for i in range(0, len(truncated_texts), batch_size):
        batch = truncated_texts[i:i + batch_size]
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
