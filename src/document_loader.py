import os
from pathlib import Path
from typing import List

from PyPDF2 import PdfReader

from src.chunker import HybridChunker, Chunk
from src.logger import get_logger
from config import KNOWLEDGE_BASE_DIR

logger = get_logger("document_loader")

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class DocumentLoader:
    def __init__(self):
        self.chunker = HybridChunker()
        self.kb_dir = Path(KNOWLEDGE_BASE_DIR)
        self.kb_dir.mkdir(parents=True, exist_ok=True)

    def load_pdf(self, file_path: str) -> List[Chunk]:
        logger.info(f"加载PDF: {file_path}")
        reader = PdfReader(file_path)
        source = Path(file_path).name
        all_chunks = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                chunks = self.chunker.chunk(text, source=source, page=i + 1)
                all_chunks.extend(chunks)
        return all_chunks

    def load_text(self, file_path: str) -> List[Chunk]:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        source = Path(file_path).name
        return self.chunker.chunk(text, source=source, page=1)

    def load_file(self, file_path: str) -> List[Chunk]:
        ext = Path(file_path).suffix.lower()
        if ext == '.pdf':
            return self.load_pdf(file_path)
        elif ext in ('.txt', '.md'):
            return self.load_text(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {ext}")

    def save_uploaded_file(self, file_content: bytes, file_name: str) -> str:
        safe_name = Path(file_name).name
        if not safe_name or safe_name.startswith('.'):
            raise ValueError(f"无效的文件名: {file_name}")
        if len(file_content) > MAX_FILE_SIZE:
            raise ValueError(f"文件过大，最大支持 {MAX_FILE_SIZE // (1024*1024)}MB")
        save_path = self.kb_dir / safe_name
        logger.info(f"保存文件: {safe_name} ({len(file_content)} bytes)")
        with open(save_path, 'wb') as f:
            f.write(file_content)
        return str(save_path)

    def get_all_files(self) -> List[str]:
        files = []
        for ext in ('*.pdf', '*.txt', '*.md'):
            files.extend([str(f) for f in self.kb_dir.glob(ext)])
        return files

    def generate_summary(self, chunks: List[Chunk]) -> str:
        text_chunks = [c.content for c in chunks if c.chunk_type == "text"][:10]
        combined = "\n".join(text_chunks)
        if len(combined) > 2000:
            combined = combined[:2000]
        return combined
