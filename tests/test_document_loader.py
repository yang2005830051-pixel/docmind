import os
import tempfile
from pathlib import Path

from src.document_loader import DocumentLoader, MAX_FILE_SIZE


def test_save_uploaded_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = DocumentLoader()
        loader.kb_dir = Path(tmpdir)
        content = b"test file content"
        path = loader.save_uploaded_file(content, "test.txt")
        assert os.path.exists(path)
        with open(path, 'rb') as f:
            assert f.read() == content


def test_save_file_sanitizes_name():
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = DocumentLoader()
        loader.kb_dir = Path(tmpdir)
        path = loader.save_uploaded_file(b"content", "../../etc/passwd")
        assert "passwd" in path
        assert ".." not in path


def test_save_file_rejects_empty_name():
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = DocumentLoader()
        loader.kb_dir = Path(tmpdir)
        try:
            loader.save_uploaded_file(b"content", "")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


def test_save_file_rejects_oversized():
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = DocumentLoader()
        loader.kb_dir = Path(tmpdir)
        try:
            loader.save_uploaded_file(b"x" * (MAX_FILE_SIZE + 1), "big.txt")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "过大" in str(e)


def test_load_text_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = DocumentLoader()
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("这是一段足够长的测试内容，用于验证文本文件加载功能是否正常工作。\n\n这是第二段内容，同样需要足够的长度来通过最小长度过滤。")
        chunks = loader.load_file(test_file)
        assert len(chunks) >= 1
        assert any("测试内容" in c.content for c in chunks)


def test_get_all_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = DocumentLoader()
        loader.kb_dir = Path(tmpdir)
        for name in ["a.pdf", "b.txt", "c.md", "d.py"]:
            with open(os.path.join(tmpdir, name), 'w') as f:
                f.write("content")
        files = loader.get_all_files()
        assert len(files) == 3
        assert not any(f.endswith('.py') for f in files)
