"""向量存储模块测试。"""

import hashlib
from unittest.mock import MagicMock, patch, PropertyMock
import pytest

from src.vector_store import _make_chunk_id


# ── ID 生成测试 ──

def test_make_chunk_id_deterministic():
    """相同输入应产生相同 ID。"""
    id1 = _make_chunk_id("test.txt", "hello", 0)
    id2 = _make_chunk_id("test.txt", "hello", 0)
    assert id1 == id2


def test_make_chunk_id_different_content():
    """不同内容应产生不同 ID。"""
    id1 = _make_chunk_id("test.txt", "hello", 0)
    id2 = _make_chunk_id("test.txt", "world", 0)
    assert id1 != id2


def test_make_chunk_id_different_source():
    """不同来源应产生不同 ID（即使内容相同）。"""
    id1 = _make_chunk_id("a.txt", "hello", 0)
    id2 = _make_chunk_id("b.txt", "hello", 0)
    assert id1 != id2


def test_make_chunk_id_different_index():
    """不同序号应产生不同 ID。"""
    id1 = _make_chunk_id("test.txt", "hello", 0)
    id2 = _make_chunk_id("test.txt", "hello", 1)
    assert id1 != id2


def test_make_chunk_id_format():
    """ID 格式应以 chunk_ 开头。"""
    chunk_id = _make_chunk_id("test.txt", "hello", 5)
    assert chunk_id.startswith("chunk_")
    assert len(chunk_id) == len("chunk_") + 32  # md5 hex is 32 chars


# ── VectorStore 类测试 ──

def test_add_chunks_empty():
    """空 chunk 列表应该返回 0。"""
    from src.vector_store import VectorStore

    vs = VectorStore.__new__(VectorStore)
    result = vs.add_chunks([])
    assert result == 0


def test_delete_by_source():
    """测试按来源删除。"""
    from src.vector_store import VectorStore

    vs = VectorStore.__new__(VectorStore)
    vs._content_collection = MagicMock()
    vs._summary_collection = MagicMock()

    vs.delete_by_source("test.txt")
    vs._content_collection.delete.assert_called_once_with(where={"source": "test.txt"})
    vs._summary_collection.delete.assert_called_once_with(ids=["summary_test.txt"])


def test_delete_all():
    """测试清空所有。"""
    from src.vector_store import VectorStore

    mock_client = MagicMock()
    vs = VectorStore.__new__(VectorStore)
    vs._client = mock_client
    vs._content_collection = MagicMock()
    vs._summary_collection = MagicMock()

    vs.delete_all()
    mock_client.delete_collection.assert_any_call("document_content")
    mock_client.delete_collection.assert_any_call("document_summary")
    assert vs._content_collection is None
    assert vs._summary_collection is None


def test_get_stats():
    """测试统计信息。"""
    from src.vector_store import VectorStore

    vs = VectorStore.__new__(VectorStore)
    vs._content_collection = MagicMock()
    vs._summary_collection = MagicMock()
    vs._content_collection.count.return_value = 42
    vs._summary_collection.count.return_value = 5
    vs._content_collection.get.return_value = {
        "metadatas": [
            {"source": "a.txt"},
            {"source": "b.txt"},
            {"source": "a.txt"},
        ]
    }

    stats = vs.get_stats()
    assert stats["chunk_count"] == 42
    assert stats["summary_count"] == 5
    assert stats["document_count"] == 2
    assert "a.txt" in stats["sources"]
    assert "b.txt" in stats["sources"]
