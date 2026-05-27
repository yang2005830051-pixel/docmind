import re
from dataclasses import dataclass, field
from typing import List

from config import CHUNK_SIZE, CHUNK_OVERLAP, MIN_CHUNK_LENGTH


@dataclass
class Chunk:
    content: str
    chunk_type: str
    metadata: dict = field(default_factory=dict)


class HybridChunker:
    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str, source: str = "", page: int = 0) -> List[Chunk]:
        segments = self._split_by_type(text)
        chunks = []
        for seg_type, content in segments:
            if seg_type == "code":
                chunks.extend(self._chunk_code(content, source, page))
            elif seg_type == "table":
                chunks.extend(self._chunk_table(content, source, page))
            else:
                chunks.extend(self._chunk_text(content, source, page))
        # 过滤过短的 chunk
        return [c for c in chunks if len(c.content.strip()) >= MIN_CHUNK_LENGTH]

    def _split_by_type(self, text: str) -> List[tuple]:
        segments = []
        pattern = re.compile(
            r'(```[\s\S]*?```)'           # code blocks
            r'|(\|[^\n]+\|(?:\n\|[^\n]+\|)*)'  # markdown tables
            r'|((?:\+[-+]+\+|\|[-: ]+\|)(?:\n[^\n]*)*)',  # ascii tables
            re.MULTILINE
        )
        last_end = 0
        for match in pattern.finditer(text):
            start = match.start()
            if start > last_end:
                segments.append(("text", text[last_end:start]))
            if match.group(1):
                segments.append(("code", match.group(1)))
            elif match.group(2):
                segments.append(("table", match.group(2)))
            elif match.group(3):
                segments.append(("table", match.group(3)))
            last_end = match.end()
        if last_end < len(text):
            segments.append(("text", text[last_end:]))
        return segments

    def _chunk_code(self, code: str, source: str, page: int) -> List[Chunk]:
        chunks = []
        blocks = re.split(r'(```[\s\S]*?```)', code)
        for block in blocks:
            if block.startswith('```') and block.endswith('```'):
                chunks.append(Chunk(
                    content=block,
                    chunk_type="code",
                    metadata={"source": source, "page": page}
                ))
            elif block.strip():
                chunks.extend(self._chunk_text(block, source, page))
        return chunks if chunks else [Chunk(
            content=code, chunk_type="code",
            metadata={"source": source, "page": page}
        )]

    def _chunk_table(self, table: str, source: str, page: int) -> List[Chunk]:
        lines = table.strip().split('\n')
        chunks = []
        current_table = []
        for line in lines:
            if re.match(r'^[\s|+\-=:]+$', line.strip()):
                if current_table:
                    chunks.append(Chunk(
                        content='\n'.join(current_table),
                        chunk_type="table",
                        metadata={"source": source, "page": page}
                    ))
                    current_table = []
            else:
                current_table.append(line)
        if current_table:
            chunks.append(Chunk(
                content='\n'.join(current_table),
                chunk_type="table",
                metadata={"source": source, "page": page}
            ))
        return chunks if chunks else [Chunk(
            content=table, chunk_type="table",
            metadata={"source": source, "page": page}
        )]

    def _chunk_text(self, text: str, source: str, page: int) -> List[Chunk]:
        if not text.strip():
            return []
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(current) + len(para) + 2 <= self.chunk_size:
                current = f"{current}\n\n{para}" if current else para
            else:
                if current:
                    chunks.append(current)
                    # 重叠窗口：保留末尾 chunk_overlap 字符作为下一段的开头
                    if self.chunk_overlap > 0 and len(current) > self.chunk_overlap:
                        current = current[-self.chunk_overlap:]
                    else:
                        current = ""
                if len(para) > self.chunk_size:
                    sub_chunks = self._split_long_paragraph(para)
                    chunks.extend(sub_chunks)
                    current = ""
                else:
                    current = para
                    continue
        if current.strip():
            chunks.append(current)
        return [Chunk(
            content=c, chunk_type="text",
            metadata={"source": source, "page": page}
        ) for c in chunks]

    def _split_long_paragraph(self, text: str) -> List[str]:
        chunks = []
        sentences = re.split(r'(?<=[。！？.!?])\s*', text)
        current = ""
        for sent in sentences:
            if len(current) + len(sent) + 1 <= self.chunk_size:
                current = f"{current} {sent}" if current else sent
            else:
                if current:
                    chunks.append(current)
                # 超长句子强制按 chunk_size 切割
                if len(sent) > self.chunk_size:
                    for i in range(0, len(sent), self.chunk_size):
                        chunks.append(sent[i:i + self.chunk_size])
                    current = ""
                else:
                    current = sent
        if current.strip():
            chunks.append(current)
        return chunks
