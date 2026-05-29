import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

BASE_DIR = Path(__file__).parent

# ── 路径配置 ──
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "chroma_db"))
KNOWLEDGE_BASE_DIR = os.getenv("KNOWLEDGE_BASE_DIR", str(BASE_DIR / "knowledge_base"))

# ── API 密钥 ──
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
MIMO_API_KEY = os.getenv("MIMO_API_KEY", "")
MIMO_BASE_URL = os.getenv("MIMO_BASE_URL", "https://api.siliconflow.cn/v1")

# ── 嵌入模型 ──
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "auto")  # auto / openai / siliconflow
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
SILICONFLOW_EMBEDDING_MODEL = os.getenv("SILICONFLOW_EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5")

# ── 分块参数 ──
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "64"))
MIN_CHUNK_LENGTH = int(os.getenv("MIN_CHUNK_LENGTH", "20"))

# ── 检索参数 ──
SUMMARY_TOP_K = int(os.getenv("SUMMARY_TOP_K", "3"))
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-base")
RERANKER_TOP_K = int(os.getenv("RERANKER_TOP_K", "10"))
FINAL_TOP_K = int(os.getenv("FINAL_TOP_K", "3"))

# ── LLM 参数 ──
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto")  # auto / deepseek / mimo / openai
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))
LLM_REQUEST_TIMEOUT = int(os.getenv("LLM_REQUEST_TIMEOUT", "30"))

# MiMo 模型（通过 SiliconFlow 调用）
MIMO_MODEL = os.getenv("MIMO_MODEL", "MiMo-7B-RL")

# ── 重试参数 ──
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))
LLM_RETRY_BASE_DELAY = float(os.getenv("LLM_RETRY_BASE_DELAY", "1.0"))
EMBEDDING_MAX_RETRIES = int(os.getenv("EMBEDDING_MAX_RETRIES", "3"))

# ── 对话记忆 ──
MEMORY_WINDOW_SIZE = int(os.getenv("MEMORY_WINDOW_SIZE", "10"))
MEMORY_MAX_TOKENS = int(os.getenv("MEMORY_MAX_TOKENS", "2000"))
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "conversations.db"))

# ── System Prompt ──
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", """你是一个技术文档问答助手。根据提供的文档内容回答问题。

规则：
1. 仅基于提供的文档内容回答，不要编造信息
2. 如果文档中没有相关信息，诚实告知用户
3. 引用来源时使用 [1] [2] 等编号
4. 回答要准确、简洁、专业
5. 如果用户追问，结合对话历史理解上下文""")


def get_embedding_provider() -> str:
    """自动检测可用的嵌入提供商。"""
    if EMBEDDING_PROVIDER != "auto":
        return EMBEDDING_PROVIDER
    if OPENAI_API_KEY:
        return "openai"
    if MIMO_API_KEY:
        return "siliconflow"
    return "none"


def get_available_llm_provider() -> str:
    """自动检测可用的 LLM 提供商。"""
    if LLM_PROVIDER != "auto":
        return LLM_PROVIDER
    if DEEPSEEK_API_KEY:
        return "deepseek"
    if MIMO_API_KEY:
        return "mimo"
    if OPENAI_API_KEY:
        return "openai"
    return "none"


def validate_config() -> list[str]:
    """验证配置，返回警告信息列表。"""
    warnings = []
    has_any_key = OPENAI_API_KEY or DEEPSEEK_API_KEY or MIMO_API_KEY
    if not has_any_key:
        warnings.append("未配置任何 API Key，请设置 OPENAI_API_KEY、DEEPSEEK_API_KEY 或 MIMO_API_KEY")
    if CHUNK_SIZE < 64:
        warnings.append(f"CHUNK_SIZE={CHUNK_SIZE} 过小，建议至少 128")
    if CHUNK_OVERLAP >= CHUNK_SIZE:
        warnings.append(f"CHUNK_OVERLAP({CHUNK_OVERLAP}) 不应大于等于 CHUNK_SIZE({CHUNK_SIZE})")
    if FINAL_TOP_K > RERANKER_TOP_K:
        warnings.append(f"FINAL_TOP_K({FINAL_TOP_K}) 不应大于 RERANKER_TOP_K({RERANKER_TOP_K})")
    if LLM_TEMPERATURE < 0 or LLM_TEMPERATURE > 2:
        warnings.append(f"LLM_TEMPERATURE={LLM_TEMPERATURE} 超出合理范围 [0, 2]")
    return warnings
