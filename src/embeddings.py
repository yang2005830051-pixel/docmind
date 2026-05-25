from langchain_openai import OpenAIEmbeddings

from config import OPENAI_API_KEY, EMBEDDING_MODEL


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY
    )
