"""FastAPI 端点测试。"""

import pytest
from unittest.mock import patch, MagicMock

# 使用 httpx TestClient 测试 FastAPI
try:
    from httpx import AsyncClient, ASGITransport
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

pytestmark = pytest.mark.skipif(not HAS_HTTPX, reason="httpx 未安装")


@pytest.fixture
def client():
    """创建测试客户端。"""
    from server import app
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.anyio
async def test_health(client):
    """健康检查端点。"""
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "session_id" in data


@pytest.mark.anyio
async def test_index(client):
    """首页应返回 HTML。"""
    resp = await client.get("/")
    assert resp.status_code == 200
    assert "DocMind" in resp.text


@pytest.mark.anyio
async def test_files_list(client):
    """文件列表端点。"""
    resp = await client.get("/api/files")
    assert resp.status_code == 200
    assert "files" in resp.json()


@pytest.mark.anyio
async def test_keys_status(client):
    """Key 状态端点。"""
    resp = await client.get("/api/keys/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "configured" in data
    assert "openai_set" in data
    assert "deepseek_set" in data


@pytest.mark.anyio
async def test_save_keys_empty(client):
    """空 key 应返回 400。"""
    resp = await client.post("/api/keys", json={"openai_key": "", "deepseek_key": ""})
    assert resp.status_code == 400


@pytest.mark.anyio
async def test_chat_empty_message(client):
    """空消息应返回 400。"""
    resp = await client.post("/api/chat", json={"message": ""})
    assert resp.status_code == 400


@pytest.mark.anyio
async def test_clear(client):
    """清空对话端点。"""
    resp = await client.post("/api/clear")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.anyio
async def test_config(client):
    """配置端点。"""
    resp = await client.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "embedding_model" in data
    assert "chunk_size" in data
    assert "llm_model" in data


@pytest.mark.anyio
async def test_stats(client):
    """统计端点。"""
    resp = await client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "chunk_count" in data
    assert "document_count" in data


@pytest.mark.anyio
async def test_delete_file_not_found(client):
    """删除不存在的文件应返回 404。"""
    resp = await client.delete("/api/files/nonexistent.txt")
    assert resp.status_code == 404
