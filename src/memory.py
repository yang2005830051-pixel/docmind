import sqlite3
import threading
import uuid
from pathlib import Path
from typing import List, Dict

from config import MEMORY_WINDOW_SIZE, MEMORY_MAX_TOKENS, DB_PATH


class ConversationMemory:
    def __init__(self, session_id: str = None, window_size: int = MEMORY_WINDOW_SIZE):
        self.session_id = session_id or str(uuid.uuid4())
        self.window_size = window_size
        self.messages: List[Dict[str, str]] = []
        self._lock = threading.Lock()
        self._db = None
        self._load()

    @property
    def db(self):
        if self._db is None:
            self._db = sqlite3.connect(DB_PATH, check_same_thread=False)
            self._db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self._db.commit()
        return self._db

    def _load(self):
        with self._lock:
            cursor = self.db.execute(
                "SELECT role, content FROM conversations WHERE session_id = ? ORDER BY timestamp",
                (self.session_id,)
            )
            self.messages = [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]
            self._trim()

    def add_user_message(self, content: str):
        with self._lock:
            self.messages.append({"role": "user", "content": content})
            self.db.execute(
                "INSERT INTO conversations (session_id, role, content) VALUES (?, ?, ?)",
                (self.session_id, "user", content)
            )
            self.db.commit()
            self._trim()

    def add_ai_message(self, content: str):
        with self._lock:
            self.messages.append({"role": "assistant", "content": content})
            self.db.execute(
                "INSERT INTO conversations (session_id, role, content) VALUES (?, ?, ?)",
                (self.session_id, "assistant", content)
            )
            self.db.commit()
            self._trim()

    def get_history(self) -> List[Dict[str, str]]:
        with self._lock:
            return self.messages.copy()

    def get_context_string(self) -> str:
        with self._lock:
            if not self.messages:
                return ""
            lines = []
            total_tokens = 0
            # 从最新消息向前拼接，直到超过 token 限制
            for msg in reversed(self.messages):
                prefix = "用户" if msg["role"] == "user" else "助手"
                line = f"{prefix}: {msg['content']}"
                # 粗略估计 token 数（中文约 1.5 字/token，英文约 4 字符/token）
                est_tokens = max(len(msg['content']) // 2, 1)
                if total_tokens + est_tokens > MEMORY_MAX_TOKENS:
                    break
                lines.insert(0, line)
                total_tokens += est_tokens
            return "\n".join(lines)

    def clear(self):
        with self._lock:
            self.db.execute(
                "DELETE FROM conversations WHERE session_id = ?",
                (self.session_id,)
            )
            self.db.commit()
            self.messages.clear()

    def _trim(self):
        """在内存和数据库中同时截断超出窗口的消息。"""
        max_msgs = self.window_size * 2
        if len(self.messages) > max_msgs:
            # 从数据库中删除旧记录
            excess = len(self.messages) - max_msgs
            old_msgs = self.messages[:excess]
            for msg in old_msgs:
                self.db.execute(
                    "DELETE FROM conversations WHERE session_id = ? AND role = ? AND content = ? AND timestamp = (SELECT MIN(timestamp) FROM conversations WHERE session_id = ? AND role = ? AND content = ?)",
                    (self.session_id, msg["role"], msg["content"], self.session_id, msg["role"], msg["content"])
                )
            self.db.commit()
            self.messages = self.messages[-max_msgs:]
