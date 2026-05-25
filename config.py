import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "chroma_db"))
KNOWLEDGE_BASE_DIR = os.getenv("KNOWLEDGE_BASE_DIR", str(BASE_DIR / "knowledge_base"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64
RERANKER_MODEL = "BAAI/bge-reranker-base"
RERANKER_TOP_K = 10
FINAL_TOP_K = 3
LLM_MODEL = "deepseek-chat"
LLM_TEMPERATURE = 0.1
LLM_MAX_TOKENS = 2048
MEMORY_WINDOW_SIZE = 10


def validate_config():
    pass
