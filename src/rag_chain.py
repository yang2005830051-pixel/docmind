from typing import List, Dict

from src.memory import ConversationMemory
from src.logger import get_logger
from config import SYSTEM_PROMPT

logger = get_logger("rag_chain")


class RAGChain:
    def __init__(self, session_id: str = None):
        self._retriever = None
        self._llm = None
        self._stream_llm = None
        self.memory = ConversationMemory(session_id=session_id)

    @property
    def retriever(self):
        if self._retriever is None:
            from src.retriever import Retriever
            self._retriever = Retriever()
        return self._retriever

    @property
    def llm(self):
        if self._llm is None:
            from src.llm import get_llm
            self._llm = get_llm()
        return self._llm

    @property
    def stream_llm(self):
        if self._stream_llm is None:
            from src.llm import get_llm
            self._stream_llm = get_llm(streaming=True)
        return self._stream_llm

    def _format_context(self, docs: List[Dict]) -> str:
        parts = []
        for i, doc in enumerate(docs, 1):
            source = doc["metadata"].get("source", "未知")
            page = doc["metadata"].get("page", "")
            parts.append(f"[{i}] 来源: {source} (第{page}页)\n{doc['content']}")
        return "\n\n".join(parts)

    def _build_prompt(self, question: str, context: str, history: str = "") -> str:
        if history:
            return f"""对话历史:
{history}

参考文档:
{context}

当前问题: {question}

请根据对话历史和参考文档回答问题。"""
        return f"""参考文档:
{context}

当前问题: {question}

请根据参考文档回答问题。"""

    def query_stream(self, question: str):
        self.memory.add_user_message(question)
        history = self.memory.get_context_string()
        try:
            logger.info(f"收到查询: {question[:50]}...")
            docs = self.retriever.retrieve(question)
            logger.info(f"检索到 {len(docs)} 个相关文档片段")
            context = self._format_context(docs)
            full_prompt = self._build_prompt(question, context, history)
            full_answer = ""
            for chunk in self.stream_llm.stream([
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": full_prompt}
            ]):
                if chunk.content:
                    full_answer += chunk.content
                    yield chunk.content
            self.memory.add_ai_message(full_answer)
        except Exception as e:
            logger.error(f"查询处理失败: {e}", exc_info=True)
            error_msg = "抱歉，处理您的问题时出现错误，请稍后重试。"
            self.memory.add_ai_message(error_msg)
            yield error_msg

    def clear_memory(self):
        self.memory.clear()
