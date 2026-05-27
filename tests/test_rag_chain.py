"""RAG 链路测试 — mock 外部依赖，测试核心流程。"""

from unittest.mock import MagicMock, patch
import pytest


def test_format_context():
    """测试上下文格式化。"""
    from src.rag_chain import RAGChain

    chain = RAGChain.__new__(RAGChain)
    docs = [
        {"content": "第一段内容", "metadata": {"source": "a.txt", "page": 1}},
        {"content": "第二段内容", "metadata": {"source": "b.txt", "page": 2}},
    ]
    result = chain._format_context(docs)
    assert "[1]" in result
    assert "[2]" in result
    assert "a.txt" in result
    assert "b.txt" in result


def test_build_prompt_with_history():
    """测试带历史的 prompt 构建。"""
    from src.rag_chain import RAGChain

    chain = RAGChain.__new__(RAGChain)
    prompt = chain._build_prompt("问题", "上下文", "历史记录")
    assert "对话历史" in prompt
    assert "历史记录" in prompt
    assert "问题" in prompt
    assert "上下文" in prompt


def test_build_prompt_without_history():
    """测试无历史的 prompt 构建。"""
    from src.rag_chain import RAGChain

    chain = RAGChain.__new__(RAGChain)
    prompt = chain._build_prompt("问题", "上下文")
    assert "对话历史" not in prompt
    assert "问题" in prompt


@patch("src.rag_chain.ConversationMemory")
def test_clear_memory(mock_memory_cls):
    """测试清空记忆。"""
    from src.rag_chain import RAGChain

    mock_memory = MagicMock()
    mock_memory_cls.return_value = mock_memory
    chain = RAGChain(session_id="test")
    chain.clear_memory()
    mock_memory.clear.assert_called_once()
