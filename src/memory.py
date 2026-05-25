import sqlite3
import uuid
from pathlib import Path
from typing import List, Dict

from config import BASE_DIR, MEMORY_WINDOW_SIZE

DB_PATH = BASE_DIR / "conversations.db"


class ConversationMemory:
    def __init__(self, session_id: str = None, window_size: int = MEMORY_WINDOW_SIZE):
        self.session_id = session_id or str(uuid.uuid4())
        self.window_size = window_size
        self.messages: List[Dict[str, str]] = []
        self._db = None
        self._load()

    @property
    def db(self):
        if self._db is None:
            self._db = sqlite3.connect(str(DB_PATH), check_same_thread=False)
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
        cursor = self.db.execute(
            "SELECT role, content FROM conversations WHERE session_id = ? ORDER BY timestamp",
            (self.session_id,)
        )
        self.messages = [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]
        self._trim()

    def add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})
        self.db.execute(
            "INSERT INTO conversations (session_id, role, content) VALUES (?, ?, ?)",
            (self.session_id, "user", content)
        )
        self.db.commit()
        self._trim()

    def add_ai_message(self, content: str):
        self.messages.append({"role": "assistant", "content": content})
        self.db.execute(
            "INSERT INTO conversations (session_id, role, content) VALUES (?, ?, ?)",
            (self.session_id, "assistant", content)
        )
        self.db.commit()
        self._trim()

    def get_history(self) -> List[Dict[str, str]]:
        return self.messages.copy()

    def get_context_string(self) -> str:
        if not self.messages:
            return ""
        lines = []
        for msg in self.messages:
            prefix = "用户" if msg["role"] == "user" else "助手"
            lines.append(f"{prefix}: {msg['content']}")
        return "\n".join(lines)

    def clear(self):
        self.db.execute(
            "DELETE FROM conversations WHERE session_id = ?",
            (self.session_id,)
        )
        self.db.commit()
        self.messages.clear()

    def _trim(self):
        if len(self.messages) > self.window_size * 2:
            self.messages = self.messages[-self.window_size * 2:]
