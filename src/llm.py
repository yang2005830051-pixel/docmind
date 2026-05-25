import time

from langchain_openai import ChatOpenAI

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS

MAX_RETRIES = 3
RETRY_DELAY = 1


def get_llm(streaming: bool = False) -> ChatOpenAI:
    return ChatOpenAI(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        streaming=streaming,
        request_timeout=30
    )


def invoke_with_retry(llm: ChatOpenAI, messages: list) -> str:
    for attempt in range(MAX_RETRIES):
        try:
            response = llm.invoke(messages)
            return response.content
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(RETRY_DELAY * (attempt + 1))
    return ""
