from src.chunker import HybridChunker


def test_chunk_text_basic():
    chunker = HybridChunker(chunk_size=100)
    text = "这是第一个段落的内容，需要足够长才能通过最小长度过滤。\n\n这是第二个段落的内容，同样需要足够的长度来通过过滤。"
    chunks = chunker.chunk(text, source="test.txt", page=1)
    assert len(chunks) >= 1
    assert all(c.chunk_type == "text" for c in chunks)
    assert all(c.metadata["source"] == "test.txt" for c in chunks)


def test_chunk_code_block():
    chunker = HybridChunker()
    text = "以下是代码示例，展示一个简单的函数定义：\n```python\nprint('hello world')\n```\n代码部分结束了。"
    chunks = chunker.chunk(text, source="test.md", page=1)
    code_chunks = [c for c in chunks if c.chunk_type == "code"]
    assert len(code_chunks) >= 1
    assert "print('hello world')" in code_chunks[0].content


def test_chunk_table():
    chunker = HybridChunker()
    text = "| 列1名称 | 列2名称 |\n|---------|----------|\n| 数据A | 数据B |\n| 数据C | 数据D |"
    chunks = chunker.chunk(text, source="test.md", page=1)
    table_chunks = [c for c in chunks if c.chunk_type == "table"]
    assert len(table_chunks) >= 1


def test_chunk_empty_text():
    chunker = HybridChunker()
    chunks = chunker.chunk("", source="test.txt", page=1)
    assert chunks == []


def test_chunk_preserves_metadata():
    chunker = HybridChunker()
    text = "这是一个足够长的测试文本内容，用于验证元数据是否正确保留在分块结果中。"
    chunks = chunker.chunk(text, source="doc.pdf", page=5)
    assert len(chunks) >= 1
    assert chunks[0].metadata["source"] == "doc.pdf"
    assert chunks[0].metadata["page"] == 5
