import os
import tempfile
from unittest.mock import patch

from src.memory import ConversationMemory


def _make_mem(session_id="test_session"):
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, 'test.db')
    patcher = patch('src.memory.DB_PATH', db_path)
    patcher.start()
    mem = ConversationMemory(session_id=session_id)
    return mem, patcher, tmpdir


def test_memory_add_messages():
    mem, patcher, tmpdir = _make_mem()
    try:
        mem.add_user_message("你好")
        mem.add_ai_message("你好！")
        assert len(mem.messages) == 2
        assert mem.messages[0]["role"] == "user"
        assert mem.messages[1]["role"] == "assistant"
    finally:
        mem.db.close()
        patcher.stop()


def test_memory_context_string():
    mem, patcher, tmpdir = _make_mem("ctx")
    try:
        mem.add_user_message("问题")
        mem.add_ai_message("回答")
        ctx = mem.get_context_string()
        assert "用户: 问题" in ctx
        assert "助手: 回答" in ctx
    finally:
        mem.db.close()
        patcher.stop()


def test_memory_persistence():
    mem1, patcher, tmpdir = _make_mem("persist")
    try:
        mem1.add_user_message("hello")
        mem1.add_ai_message("world")
        mem1.db.close()
        mem2 = ConversationMemory(session_id="persist")
        assert len(mem2.messages) == 2
        mem2.db.close()
    finally:
        patcher.stop()


def test_memory_clear():
    mem, patcher, tmpdir = _make_mem("clear")
    try:
        mem.add_user_message("test")
        mem.clear()
        assert len(mem.messages) == 0
    finally:
        mem.db.close()
        patcher.stop()


def test_memory_trim():
    mem, patcher, tmpdir = _make_mem("trim")
    try:
        mem.window_size = 2
        for i in range(10):
            mem.add_user_message(f"msg {i}")
            mem.add_ai_message(f"reply {i}")
        assert len(mem.messages) <= 4
    finally:
        mem.db.close()
        patcher.stop()
