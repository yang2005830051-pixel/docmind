from typing import TypedDict, List, Dict

from langgraph.graph import StateGraph, END

from src.memory import ConversationMemory
from src.logger import get_logger

logger = get_logger("rag_chain")

SYSTEM_PROMPT = """你是一个技术文档问答助手。根据提供的文档内容回答问题。

规则：
1. 仅基于提供的文档内容回答，不要编造信息
2. 如果文档中没有相关信息，诚实告知用户
3. 引用来源时使用 [1] [2] 等编号
4. 回答要准确、简洁、专业
5. 如果用户追问，结合对话历史理解上下文"""


class RAGState(TypedDict):
    query: str
    context: str
    history: str
    documents: List[Dict]
    answer: str


class RAGChain:
    def __init__(self, session_id: str = None):
        self._retriever = None
        self._llm = None
        self._stream_llm = None
        self._graph = None
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

    @property
    def graph(self):
        if self._graph is None:
            self._graph = self._build_graph()
        return self._graph

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(RAGState)
        workflow.add_node("retrieve", self._retrieve_node)
        workflow.add_node("generate", self._generate_node)
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)
        return workflow.compile()

    def _retrieve_node(self, state: RAGState) -> dict:
        docs = self.retriever.retrieve(state["query"])
        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc["metadata"].get("source", "未知")
            page = doc["metadata"].get("page", "")
            context_parts.append(f"[{i}] 来源: {source} (第{page}页)\n{doc['content']}")
        return {
            "documents": docs,
            "context": "\n\n".join(context_parts)
        }

    def _generate_node(self, state: RAGState) -> dict:
        history_str = state.get("history", "")
        user_msg = state["query"]
        context = state["context"]
        full_prompt = self._build_prompt(user_msg, context, history_str)
        from src.llm import invoke_with_retry
        answer = invoke_with_retry(self.llm, [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": full_prompt}
        ])
        return {"answer": answer}

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

    def _format_context(self, docs: List[Dict]) -> str:
        parts = []
        for i, doc in enumerate(docs, 1):
            source = doc["metadata"].get("source", "未知")
            page = doc["metadata"].get("page", "")
            parts.append(f"[{i}] 来源: {source} (第{page}页)\n{doc['content']}")
        return "\n\n".join(parts)

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
            error_msg = f"抱歉，处理您的问题时出现错误: {e}"
            self.memory.add_ai_message(error_msg)
            yield error_msg

    def clear_memory(self):
        self.memory.clear()
