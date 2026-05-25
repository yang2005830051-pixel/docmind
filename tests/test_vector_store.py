import hashlib
from src.vector_store import _make_chunk_id


def test_make_chunk_id_deterministic():
    content = "test content"
    id1 = _make_chunk_id(content, 0)
    id2 = _make_chunk_id(content, 0)
    assert id1 == id2


def test_make_chunk_id_different_content():
    id1 = _make_chunk_id("content A", 0)
    id2 = _make_chunk_id("content B", 0)
    assert id1 != id2


def test_make_chunk_id_different_index():
    id1 = _make_chunk_id("same content", 0)
    id2 = _make_chunk_id("same content", 1)
    assert id1 != id2


def test_make_chunk_id_format():
    content = "hello"
    chunk_id = _make_chunk_id(content, 5)
    assert chunk_id.startswith("chunk_5_")
    assert len(chunk_id) == len("chunk_5_") + 32  # md5 hex is 32 chars
