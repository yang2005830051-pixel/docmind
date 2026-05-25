from src.chunker import HybridChunker


def test_chunk_text_basic():
    chunker = HybridChunker(chunk_size=100)
    text = "这是第一段落。\n\n这是第二段落。"
    chunks = chunker.chunk(text, source="test.txt", page=1)
    assert len(chunks) >= 1
    assert all(c.chunk_type == "text" for c in chunks)
    assert all(c.metadata["source"] == "test.txt" for c in chunks)


def test_chunk_code_block():
    chunker = HybridChunker()
    text = "以下是代码：\n```python\nprint('hello')\n```\n结束"
    chunks = chunker.chunk(text, source="test.md", page=1)
    code_chunks = [c for c in chunks if c.chunk_type == "code"]
    assert len(code_chunks) >= 1
    assert "print('hello')" in code_chunks[0].content


def test_chunk_table():
    chunker = HybridChunker()
    text = "| 列1 | 列2 |\n|-----|-----|\n| A | B |\n| C | D |"
    chunks = chunker.chunk(text, source="test.md", page=1)
    table_chunks = [c for c in chunks if c.chunk_type == "table"]
    assert len(table_chunks) >= 1


def test_chunk_empty_text():
    chunker = HybridChunker()
    chunks = chunker.chunk("", source="test.txt", page=1)
    assert chunks == []


def test_chunk_preserves_metadata():
    chunker = HybridChunker()
    text = "测试内容"
    chunks = chunker.chunk(text, source="doc.pdf", page=5)
    assert chunks[0].metadata["source"] == "doc.pdf"
    assert chunks[0].metadata["page"] == 5
