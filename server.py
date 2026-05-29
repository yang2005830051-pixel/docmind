"""DocMind API Server — serves the HTML frontend and provides REST endpoints."""

import os
import uuid
import traceback
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.document_loader import DocumentLoader
from src.rag_chain import RAGChain
from src.logger import get_logger

logger = get_logger("server")

# 限流配置
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(title="DocMind API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS 限制为本地开发
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB

doc_loader = DocumentLoader()

# Session 管理（单用户模式）
_session_id = str(uuid.uuid4())
_rag_chain = RAGChain(session_id=_session_id)
_messages: list[dict] = []


# ── 全局错误处理 ──

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请稍后重试"}
    )


# ── 健康检查 ──

@app.get("/health")
async def health():
    from config import validate_config
    warnings = validate_config()
    return {
        "status": "ok",
        "session_id": _session_id,
        "messages": len(_messages),
        "warnings": warnings,
    }


# ── 前端 ──

@app.get("/")
async def index():
    return FileResponse(BASE_DIR / "index.html")


# ── 文件管理 ──

@app.get("/api/files")
async def list_files():
    files = doc_loader.get_all_files()
    return {"files": [Path(f).name for f in files]}


@app.delete("/api/files/{filename}")
async def delete_file(filename: str):
    """删除指定文件及其向量数据。"""
    # 安全检查：防止路径遍历
    if ".." in "/" or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="无效的文件名")

    file_path = BASE_DIR / "knowledge_base" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    # 删除物理文件
    try:
        file_path.unlink()
    except Exception as e:
        logger.error(f"删除文件失败: {e}")
        raise HTTPException(status_code=500, detail="删除文件失败")

    # 删除向量数据
    try:
        from src.vector_store import VectorStore
        vs = VectorStore()
        vs.delete_by_source(filename)
    except Exception as e:
        logger.warning(f"删除向量数据失败: {e}")

    logger.info(f"已删除文件: {filename}")
    return {"status": "ok", "deleted": filename}


@app.post("/api/upload")
@limiter.limit("10/minute")  # 上传接口严格限流
async def upload_files(request: Request, files: list[UploadFile] = File(...)):
    from src.vector_store import VectorStore

    if not files:
        raise HTTPException(status_code=400, detail="未选择文件")

    try:
        vector_store = VectorStore()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    processed = []
    errors = []
    for file in files:
        try:
            content = await file.read()
            if len(content) > MAX_UPLOAD_SIZE:
                errors.append(f"{file.name}: 文件过大（限 50MB）")
                continue
            file_path = doc_loader.save_uploaded_file(content, file.filename)
            chunks = doc_loader.load_file(file_path)
            vector_store.add_chunks(chunks)
            summary = doc_loader.generate_summary(chunks)
            vector_store.add_summary(file.filename, summary)
            processed.append(file.filename)
        except Exception as e:
            logger.error(f"处理文件 {file.filename} 失败: {e}")
            errors.append(f"{file.filename}: {str(e)}")

    result = {"processed": processed, "count": len(processed)}
    if errors:
        result["errors"] = errors
    return result


# ── 聊天 ──

class ChatRequest(BaseModel):
    message: str


@app.post("/api/chat")
@limiter.limit("20/minute")  # 聊天接口更严格限流
async def chat(request: Request, req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    try:
        response_parts = []
        for chunk in _rag_chain.query_stream(req.message):
            response_parts.append(chunk)
        response = "".join(response_parts)

        _messages.append({"role": "user", "content": req.message})
        _messages.append({"role": "assistant", "content": response})

        return {"response": response, "sources": []}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"聊天失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="处理请求时出错，请稍后重试")


@app.post("/api/clear")
async def clear_chat():
    _rag_chain.clear_memory()
    _messages.clear()
    return {"status": "ok"}


@app.get("/api/export")
@limiter.limit("30/minute")
async def export_chat(request: Request):
    """导出对话历史为 Markdown 格式。"""
    if not _messages:
        raise HTTPException(status_code=400, detail="没有对话记录可导出")

    # 生成 Markdown 内容
    md_lines = ["# DocMind 对话记录\n"]
    md_lines.append(f"导出时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    md_lines.append("---\n")

    for i, msg in enumerate(_messages, 1):
        role = "用户" if msg["role"] == "user" else "助手"
        md_lines.append(f"## {role} [{i}]\n")
        md_lines.append(f"{msg['content']}\n")
        md_lines.append("---\n")

    content = "\n".join(md_lines)

    # 返回文件下载
    from fastapi.responses import Response
    return Response(
        content=content.encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=docmind_chat_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        }
    )


# ── Key 管理 ──

def _check_env_key(name: str) -> bool:
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return False
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{name}="):
            val = line.split("=", 1)[1].strip()
            if val and not val.startswith("your_"):
                return True
    return False


def _save_keys(openai_key: str = "", deepseek_key: str = "", mimo_key: str = ""):
    env_path = BASE_DIR / ".env"
    lines = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    keys_map = {
        "OPENAI_API_KEY": openai_key,
        "DEEPSEEK_API_KEY": deepseek_key,
        "MIMO_API_KEY": mimo_key,
    }
    found = {k: False for k in keys_map}
    for i, line in enumerate(lines):
        for key_name in keys_map:
            if line.startswith(f"{key_name}="):
                if keys_map[key_name]:
                    lines[i] = f"{key_name}={keys_map[key_name]}"
                found[key_name] = True
                break
    for key_name, val in keys_map.items():
        if not found[key_name] and val:
            lines.append(f"{key_name}={val}")
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class KeyRequest(BaseModel):
    openai_key: str = ""
    deepseek_key: str = ""
    mimo_key: str = ""


@app.get("/api/keys/status")
async def keys_status():
    return {
        "configured": _check_env_key("OPENAI_API_KEY") or _check_env_key("DEEPSEEK_API_KEY") or _check_env_key("MIMO_API_KEY"),
        "openai_set": _check_env_key("OPENAI_API_KEY"),
        "deepseek_set": _check_env_key("DEEPSEEK_API_KEY"),
        "mimo_set": _check_env_key("MIMO_API_KEY"),
    }


@app.post("/api/keys")
async def save_keys(req: KeyRequest):
    if not req.openai_key and not req.deepseek_key and not req.mimo_key:
        raise HTTPException(status_code=400, detail="请至少填写一个 API Key")
    _save_keys(req.openai_key, req.deepseek_key, req.mimo_key)
    # 重新加载环境变量
    if req.openai_key:
        os.environ["OPENAI_API_KEY"] = req.openai_key
    if req.deepseek_key:
        os.environ["DEEPSEEK_API_KEY"] = req.deepseek_key
    if req.mimo_key:
        os.environ["MIMO_API_KEY"] = req.mimo_key
    return {"status": "ok"}


# ── 配置管理 ──

@app.get("/api/config")
async def get_config():
    from config import (
        EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, RERANKER_MODEL,
        RERANKER_TOP_K, FINAL_TOP_K, LLM_MODEL, LLM_TEMPERATURE,
        LLM_MAX_TOKENS, MEMORY_WINDOW_SIZE, validate_config,
        get_available_llm_provider, MIMO_MODEL,
    )
    return {
        "embedding_model": EMBEDDING_MODEL,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "reranker_model": RERANKER_MODEL,
        "reranker_top_k": RERANKER_TOP_K,
        "final_top_k": FINAL_TOP_K,
        "llm_provider": get_available_llm_provider(),
        "llm_model": LLM_MODEL,
        "mimo_model": MIMO_MODEL,
        "llm_temperature": LLM_TEMPERATURE,
        "llm_max_tokens": LLM_MAX_TOKENS,
        "memory_window_size": MEMORY_WINDOW_SIZE,
        "warnings": validate_config(),
    }


# ── 向量库统计 ──

@app.get("/api/stats")
async def get_stats():
    try:
        from src.vector_store import VectorStore
        vs = VectorStore()
        return vs.get_stats()
    except Exception as e:
        logger.warning(f"获取统计失败: {e}")
        return {"chunk_count": 0, "document_count": 0, "summary_count": 0, "sources": []}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8501)
