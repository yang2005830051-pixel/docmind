import time
import openai
from langchain_openai import ChatOpenAI

from config import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL,
    MIMO_API_KEY, MIMO_BASE_URL, MIMO_MODEL,
    OPENAI_API_KEY,
    LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS,
    LLM_REQUEST_TIMEOUT, LLM_MAX_RETRIES, LLM_RETRY_BASE_DELAY,
    get_available_llm_provider,
)
from src.logger import get_logger

logger = get_logger("llm")

# 可重试的错误码
_RETRYABLE_CODES = {429, 500, 502, 503, 504}


def get_llm(streaming: bool = False) -> ChatOpenAI:
    provider = get_available_llm_provider()
    logger.info(f"使用 LLM 提供商: {provider}")

    if provider == "deepseek":
        return ChatOpenAI(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
            streaming=streaming,
            request_timeout=LLM_REQUEST_TIMEOUT,
        )
    elif provider == "mimo":
        return ChatOpenAI(
            model=MIMO_MODEL,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            api_key=MIMO_API_KEY,
            base_url=MIMO_BASE_URL,
            streaming=streaming,
            request_timeout=LLM_REQUEST_TIMEOUT,
        )
    elif provider == "openai":
        return ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            api_key=OPENAI_API_KEY,
            streaming=streaming,
            request_timeout=LLM_REQUEST_TIMEOUT,
        )
    else:
        raise ValueError("未配置任何 LLM API Key，请在 .env 中设置 DEEPSEEK_API_KEY、MIMO_API_KEY 或 OPENAI_API_KEY")


def _is_retryable(exc: Exception) -> bool:
    """判断异常是否值得重试。"""
    if isinstance(exc, (TimeoutError, ConnectionError, ConnectionResetError)):
        return True
    if isinstance(exc, openai.APIStatusError):
        return exc.status_code in _RETRYABLE_CODES
    if isinstance(exc, openai.APIConnectionError):
        return True
    if isinstance(exc, openai.RateLimitError):
        return True
    return False


def invoke_with_retry(llm: ChatOpenAI, messages: list) -> str:
    for attempt in range(LLM_MAX_RETRIES):
        try:
            response = llm.invoke(messages)
            return response.content
        except Exception as e:
            if not _is_retryable(e):
                logger.error(f"不可重试的错误: {e}")
                raise
            if attempt == LLM_MAX_RETRIES - 1:
                logger.error(f"重试 {LLM_MAX_RETRIES} 次后仍失败: {e}")
                raise
            delay = LLM_RETRY_BASE_DELAY * (attempt + 1)
            logger.warning(f"请求失败，{delay}s 后重试 ({attempt + 1}/{LLM_MAX_RETRIES}): {e}")
            time.sleep(delay)
