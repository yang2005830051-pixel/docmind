import streamlit as st
from pathlib import Path

st.set_page_config(page_title="DocMind", page_icon="📄", layout="wide")


def _check_env_key(name: str) -> bool:
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return False
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{name}="):
            val = line.split("=", 1)[1].strip()
            if val and not val.startswith("your_"):
                return True
    return False


def _any_key_set() -> bool:
    return _check_env_key("OPENAI_API_KEY") or _check_env_key("DEEPSEEK_API_KEY")


def _save_keys(openai_key: str, deepseek_key: str):
    env_path = Path(__file__).parent / ".env"
    lines = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    found = {"OPENAI": False, "DEEPSEEK": False}
    for i, line in enumerate(lines):
        if line.startswith("OPENAI_API_KEY="):
            lines[i] = f"OPENAI_API_KEY={openai_key}"
            found["OPENAI"] = True
        elif line.startswith("DEEPSEEK_API_KEY="):
            lines[i] = f"DEEPSEEK_API_KEY={deepseek_key}"
            found["DEEPSEEK"] = True
    if not found["OPENAI"]:
        lines.append(f"OPENAI_API_KEY={openai_key}")
    if not found["DEEPSEEK"]:
        lines.append(f"DEEPSEEK_API_KEY={deepseek_key}")
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _get_existing_key(name: str) -> str:
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return ""
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{name}="):
            val = line.split("=", 1)[1].strip()
            if val and not val.startswith("your_"):
                return val
    return ""


# ── State ──
if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())
if "keys_configured" not in st.session_state:
    st.session_state.keys_configured = _any_key_set()


# ── Dialog ──
@st.dialog("🔑 配置 API Key", width="small")
def key_config_dialog():
    st.caption("至少填写一个即可使用")

    existing_oa = _get_existing_key("OPENAI_API_KEY")
    existing_ds = _get_existing_key("DEEPSEEK_API_KEY")

    oa_val = st.text_input(
        "OpenAI API Key",
        value=existing_oa,
        type="password",
        placeholder="sk-...（选填）",
    )
    st.caption("用于文档向量化（Embedding）")

    ds_val = st.text_input(
        "DeepSeek API Key",
        value=existing_ds,
        type="password",
        placeholder="sk-...（选填）",
    )
    st.caption("用于 AI 对话（LLM）")

    if st.button("保存", type="primary", use_container_width=True):
        oa = oa_val.strip()
        ds = ds_val.strip()
        if not oa and not ds:
            st.error("请至少填写一个 API Key")
        else:
            _save_keys(oa, ds)
            st.session_state.keys_configured = True
            st.rerun()


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&display=swap');

:root {
    --bg: #FAFAF9;
    --surface: #FFFFFF;
    --surface-hover: #F5F5F4;
    --border: #E7E5E4;
    --border-focus: #A8A29E;
    --text: #1C1917;
    --text-secondary: #78716C;
    --text-muted: #A8A29E;
    --accent: #B45309;
    --accent-light: #FEF3C7;
    --accent-bg: #FFFBEB;
    --green: #16A34A;
    --green-bg: #F0FDF4;
    --red: #DC2626;
    --red-bg: #FEF2F2;
    --blue: #2563EB;
    --blue-bg: #EFF6FF;
    --radius: 10px;
    --radius-sm: 6px;
    --shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
    --shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
}

.stApp {
    font-family: 'DM Sans', -apple-system, sans-serif;
    background: var(--bg) !important;
}

section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}

/* ── Header ── */
.app-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 0 24px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
}

.app-title {
    display: flex;
    align-items: center;
    gap: 10px;
}

.app-title h1 {
    font-family: 'Fraunces', serif;
    font-size: 24px !important;
    font-weight: 600;
    color: var(--text) !important;
    letter-spacing: -0.3px;
    margin: 0 !important;
}

.app-title-icon {
    width: 36px;
    height: 36px;
    border-radius: var(--radius-sm);
    background: var(--accent);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
}

.header-right {
    display: flex;
    align-items: center;
    gap: 10px;
}

.app-badge {
    font-size: 12px;
    font-weight: 500;
    color: var(--accent);
    background: var(--accent-light);
    padding: 4px 10px;
    border-radius: 100px;
}

/* ── Key button ── */
.key-open-btn button {
    width: 36px !important;
    height: 36px !important;
    padding: 0 !important;
    border-radius: var(--radius-sm) !important;
    font-size: 16px !important;
    line-height: 1 !important;
    min-height: 36px !important;
    border: 1px solid var(--border) !important;
    background: var(--surface) !important;
    color: var(--text-muted) !important;
    box-shadow: var(--shadow-sm) !important;
}

.key-open-btn button:hover {
    background: var(--surface-hover) !important;
    border-color: var(--border-focus) !important;
    color: var(--text) !important;
}

.key-open-btn.ok button {
    border-color: var(--green) !important;
    color: var(--green) !important;
    background: var(--green-bg) !important;
}

/* ── Stats ── */
.stats-bar {
    display: flex;
    gap: 8px;
    margin-bottom: 24px;
    flex-wrap: wrap;
}

.stat-item {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 100px;
    font-size: 13px;
    color: var(--text-secondary);
    box-shadow: var(--shadow-sm);
}

.stat-item strong { color: var(--text); font-weight: 600; }

/* ── Sidebar ── */
.side-section { margin-bottom: 20px; }

.side-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-muted);
    margin-bottom: 10px;
    padding-left: 2px;
}

.file-entry {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    border-radius: var(--radius-sm);
    margin-bottom: 2px;
    transition: background 0.15s;
}

.file-entry:hover { background: var(--surface-hover); }

.file-tag {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.5px;
    padding: 3px 7px;
    border-radius: 4px;
    text-transform: uppercase;
    flex-shrink: 0;
}

.file-tag.pdf { background: var(--red-bg); color: var(--red); }
.file-tag.txt { background: var(--green-bg); color: var(--green); }
.file-tag.md  { background: var(--blue-bg); color: var(--blue); }

.file-label {
    font-size: 13px;
    color: var(--text);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.empty-files {
    text-align: center;
    padding: 20px;
    color: var(--text-muted);
    font-size: 13px;
    border: 1px dashed var(--border);
    border-radius: var(--radius);
    background: var(--surface);
}

/* ── Chat ── */
.chat-area { max-width: 720px; margin: 0 auto; }
.msg-row { margin-bottom: 16px; }

.msg-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 6px;
    padding-left: 2px;
}

.msg-label.user { color: var(--accent); }
.msg-label.ai { color: var(--text-muted); }

.msg-body {
    padding: 14px 18px;
    border-radius: var(--radius);
    font-size: 14px;
    line-height: 1.65;
    color: var(--text);
}

.msg-body.user {
    background: var(--accent-bg);
    border: 1px solid #FDE68A;
}

.msg-body.ai {
    background: var(--surface);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-sm);
}

/* ── Empty ── */
.empty-state { text-align: center; padding: 64px 20px; }
.empty-state-icon { font-size: 40px; margin-bottom: 16px; opacity: 0.3; }
.empty-state h3 {
    font-family: 'Fraunces', serif;
    font-size: 20px;
    font-weight: 600;
    color: var(--text) !important;
    margin-bottom: 6px !important;
}
.empty-state p { font-size: 14px; color: var(--text-secondary); }

/* ── Buttons ── */
.stButton > button {
    font-family: 'DM Sans', sans-serif !important;
    border-radius: var(--radius-sm) !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    border: 1px solid var(--border) !important;
    background: var(--surface) !important;
    color: var(--text) !important;
    box-shadow: var(--shadow-sm) !important;
    transition: all 0.15s !important;
}

.stButton > button:hover {
    background: var(--surface-hover) !important;
    border-color: var(--border-focus) !important;
}

.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
    background: var(--accent) !important;
    color: white !important;
    border: none !important;
}

.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {
    background: #92400E !important;
}

/* ── Chat Input ── */
div[data-testid="stChatInput"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    box-shadow: var(--shadow) !important;
    padding: 2px !important;
}

div[data-testid="stChatInput"]:focus-within {
    border-color: var(--accent) !important;
    box-shadow: var(--shadow), 0 0 0 3px var(--accent-light) !important;
}

div[data-testid="stChatInput"] textarea {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
}

.stFileUploader section {
    border-radius: var(--radius) !important;
    border: 1px solid var(--border) !important;
}

.stSpinner > div { border-top-color: var(--accent) !important; }

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

div[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════
#  Auto-show dialog if no keys configured
# ══════════════════════════════════════════
if not st.session_state.keys_configured:
    key_config_dialog()


# ══════════════════════════════════════════
#  Main App
# ══════════════════════════════════════════
from src.document_loader import DocumentLoader
from src.rag_chain import RAGChain

if "rag_chain" not in st.session_state:
    st.session_state.rag_chain = RAGChain(session_id=st.session_state.session_id)
if "messages" not in st.session_state:
    st.session_state.messages = []

rag_chain = st.session_state.rag_chain
doc_loader = DocumentLoader()
files = doc_loader.get_all_files()

# ── Sidebar ──
with st.sidebar:
    st.markdown("""
    <div class="side-section">
        <div class="side-label">上传文档</div>
    </div>
    """, unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "选择文件",
        type=["pdf", "txt", "md"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        help="支持 PDF、TXT、Markdown 格式"
    )
    if uploaded_files:
        if st.button("处理文档", use_container_width=True, type="primary"):
            try:
                from src.vector_store import VectorStore
                vector_store = VectorStore()
                with st.spinner("处理中..."):
                    progress = st.progress(0)
                    for i, file in enumerate(uploaded_files):
                        progress.progress((i) / len(uploaded_files), text=f"{file.name}")
                        file_path = doc_loader.save_uploaded_file(file.getvalue(), file.name)
                        chunks = doc_loader.load_file(file_path)
                        vector_store.add_chunks(chunks)
                        summary = doc_loader.generate_summary(chunks)
                        vector_store.add_summary(file.name, summary)
                    progress.progress(1.0, text="完成")
                    st.success(f"已处理 {len(uploaded_files)} 个文档")
                    st.rerun()
            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"出错: {e}")

    st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="side-section">
        <div class="side-label">知识库</div>
    </div>
    """, unsafe_allow_html=True)

    if files:
        for f in files:
            ext = Path(f).suffix.lower().replace('.', '')
            st.markdown(f"""
            <div class="file-entry">
                <span class="file-tag {ext}">{ext}</span>
                <span class="file-label">{Path(f).name}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-files">暂无文档</div>', unsafe_allow_html=True)

    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

    if st.button("清空对话", use_container_width=True):
        rag_chain.clear_memory()
        st.session_state.messages = []
        st.rerun()

# ── Header with key button ──
is_ok = st.session_state.keys_configured

header_cols = st.columns([8, 1])
with header_cols[0]:
    st.markdown("""
    <div class="app-header" style="border-bottom:none;padding-bottom:0;margin-bottom:0;">
        <div class="app-title">
            <div class="app-title-icon">📄</div>
            <h1>DocMind</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)

with header_cols[1]:
    btn_cls = "key-open-btn ok" if is_ok else "key-open-btn"
    st.markdown(f'<div class="{btn_cls}" style="text-align:right;padding-top:4px;">', unsafe_allow_html=True)
    if st.button("🔑", key="key_reopen", help="配置 API Key"):
        key_config_dialog()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ── Stats ──
doc_count = len(files)
turn_count = len(st.session_state.messages) // 2

st.markdown(f"""
<div class="stats-bar">
    <div class="stat-item"><strong>{doc_count}</strong> 文档</div>
    <div class="stat-item"><strong>{turn_count}</strong> 轮对话</div>
</div>
""", unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">💬</div>
        <h3>开始提问</h3>
        <p>在左侧上传文档，然后在下方输入问题</p>
    </div>
    """, unsafe_allow_html=True)

# ── Chat ──
st.markdown('<div class="chat-area">', unsafe_allow_html=True)

for msg in st.session_state.messages:
    role = msg["role"]
    content = msg["content"]
    label_cls = "user" if role == "user" else "ai"
    label_text = "你" if role == "user" else "助手"
    st.markdown(f"""
    <div class="msg-row">
        <div class="msg-label {label_cls}">{label_text}</div>
        <div class="msg-body {label_cls}">{content}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

if query := st.chat_input("输入技术问题..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    with st.chat_message("assistant"):
        with st.spinner("正在检索并生成回答..."):
            response = st.write_stream(rag_chain.query_stream(query))
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
