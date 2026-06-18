import os
os.environ["PYTHONIOENCODING"] = "utf-8"

import streamlit as st
from openai import OpenAI
from retriever import load_and_index, hybrid_search, get_stats, COLLECTION_NAME

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

# 部门配置
DEPARTMENTS = {
    "🖥️ IT部门": {
        "file": "docs/故障案例.txt",
        "key": "IT",
        "prompt": "You are a senior IT support engineer. Answer based on the case library. Reply in Chinese.",
        "desc": "技术故障排查与IT支持，解决电脑、网络、打印机等问题"
    },
    "👥 HR部门": {
        "file": "docs/hr.txt",
        "key": "HR",
        "prompt": "You are an experienced HR specialist. Answer based on the HR knowledge base. Reply in Chinese.",
        "desc": "人事政策、考勤假期、薪资福利、入职离职流程"
    },
    "🏢 行政部门": {
        "file": "docs/admin.txt",
        "key": "行政",
        "prompt": "You are an admin department specialist. Answer based on the admin knowledge base. Reply in Chinese.",
        "desc": "行政流程、办公资产管理、会议安排与后勤保障"
    },
    "📞 客服部门": {
        "file": "docs/service.txt",
        "key": "客服",
        "prompt": "You are a customer service specialist. Answer based on the service knowledge base. Reply in Chinese.",
        "desc": "客户咨询处理、投诉跟进、售后服务标准流程"
    },
    "💼 销售部门": {
        "file": "docs/sales.txt",
        "key": "销售",
        "prompt": "You are a sales operations specialist. Answer based on the sales knowledge base. Reply in Chinese.",
        "desc": "销售政策、报价流程、合同管理与客户对接规范"
    },
}

# 用户账号配置
USERS = {
    "admin":      {"password": "admin123",   "departments": "all"},
    "hr":         {"password": "hr123",      "departments": ["👥 HR部门"]},
    "it":         {"password": "it123",      "departments": ["🖥️ IT部门"]},
    "admin_dept": {"password": "admin456",   "departments": ["🏢 行政部门"]},
    "service":    {"password": "service123", "departments": ["📞 客服部门"]},
    "sales":      {"password": "sales123",   "departments": ["💼 销售部门"]},
}

# 构建 ChromaDB 索引所需的文件路径字典
INDEX_FILES = {}
for name, cfg in DEPARTMENTS.items():
    INDEX_FILES[cfg["key"]] = cfg["file"]

@st.cache_resource
def init_vector_db():
    """启动时加载所有文档到 ChromaDB 向量库（仅首次加载）"""
    count = load_and_index(INDEX_FILES)
    return get_stats()

# ========== 自定义 CSS ==========
st.set_page_config(page_title="企业知识库助手", page_icon="🏢", layout="wide")

st.markdown("""
<style>
    /* ===== 全局蓝白配色 ===== */
    .stApp {
        background: linear-gradient(135deg, #f0f4ff 0%, #e8f0fe 100%);
    }

    /* ===== 侧边栏 ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a3a5c 0%, #1e4d7b 40%, #1b3d60 100%);
    }
    /* 所有文字及标签统一为浅色 */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    /* 输入框内文字保持深色 */
    [data-testid="stSidebar"] input {
        color: #1e293b !important;
    }
    [data-testid="stSidebar"] h5 {
        color: #ffffff !important;
    }
    /* Radio 按钮选中态加强 */
    [data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] label {
        color: #ffffff !important;
        font-weight: 500;
    }
    [data-testid="stSidebar"] .stSuccess {
        background-color: rgba(16, 185, 129, 0.2) !important;
        border: 1px solid rgba(16, 185, 129, 0.4) !important;
        color: #a7f3d0 !important;
    }
    [data-testid="stSidebar"] .stSuccess p {
        color: #a7f3d0 !important;
    }
    [data-testid="stSidebar"] .stError {
        background-color: rgba(239, 68, 68, 0.2) !important;
        border: 1px solid rgba(239, 68, 68, 0.4) !important;
        color: #fca5a5 !important;
    }
    [data-testid="stSidebar"] .stError p {
        color: #fca5a5 !important;
    }
    /* 退出按钮样式 */
    [data-testid="stSidebar"] button {
        color: #e2e8f0 !important;
        border-color: rgba(255,255,255,0.25) !important;
    }
    [data-testid="stSidebar"] button:hover {
        border-color: rgba(255,255,255,0.5) !important;
        background: rgba(255,255,255,0.1) !important;
    }

    /* 侧边栏标题 */
    .sidebar-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #ffffff;
        text-align: center;
        padding: 0.8rem 0 0.3rem 0;
        letter-spacing: 0.05em;
    }
    .sidebar-subtitle {
        font-size: 0.78rem;
        color: #94a3b8;
        text-align: center;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(255,255,255,0.12);
        margin-bottom: 0.8rem;
    }

    /* 部门信息卡片 */
    .dept-card {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 10px;
        padding: 0.8rem 0.9rem;
        margin: 0.5rem 0 0.8rem 0;
    }
    .dept-card .dept-icon {
        font-size: 1.6rem;
        margin-bottom: 0.2rem;
    }
    .dept-card .dept-name {
        font-size: 1rem;
        font-weight: 600;
        color: #e2e8f0;
    }
    .dept-card .dept-desc {
        font-size: 0.75rem;
        color: #94a3b8;
        line-height: 1.5;
        margin-top: 0.3rem;
    }

    /* ===== 主界面 ===== */
    .main-header {
        background: linear-gradient(135deg, #1e4d7b 0%, #2563eb 100%);
        border-radius: 16px;
        padding: 1.6rem 2rem;
        margin-bottom: 1.2rem;
        color: #ffffff;
        box-shadow: 0 4px 20px rgba(30, 77, 123, 0.25);
    }
    .main-header h2 {
        color: #ffffff !important;
        margin: 0 0 0.3rem 0;
        font-size: 1.5rem;
    }
    .main-header .header-sub {
        font-size: 0.85rem;
        color: #bfdbfe;
        opacity: 0.9;
    }

    /* 欢迎面板 */
    .welcome-panel {
        background: #ffffff;
        border-radius: 16px;
        padding: 2.5rem 2rem;
        text-align: center;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border: 1px solid #e2e8f0;
    }
    .welcome-panel .welcome-icon {
        font-size: 3.5rem;
        margin-bottom: 1rem;
    }
    .welcome-panel h3 {
        color: #1e3a5f;
        font-size: 1.4rem;
        margin-bottom: 0.6rem;
    }
    .welcome-panel .welcome-text {
        color: #64748b;
        font-size: 0.92rem;
        line-height: 1.8;
    }
    .tip-box {
        display: inline-block;
        background: #f0f7ff;
        border: 1px solid #bfdbfe;
        border-radius: 10px;
        padding: 0.7rem 1.2rem;
        margin: 0.3rem;
        font-size: 0.82rem;
        color: #1e4d7b;
    }

    /* ===== 聊天气泡 ===== */
    [data-testid="stChatMessage"] {
        border-radius: 14px !important;
        padding: 0.8rem 1.1rem !important;
        margin-bottom: 0.6rem !important;
        box-shadow: 0 1px 6px rgba(0,0,0,0.04);
    }
    /* 用户气泡 */
    [data-testid="stChatMessage"][data-testid*="user"] {
        background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%) !important;
        border: none !important;
    }
    [data-testid="stChatMessage"][data-testid*="user"] .stChatMessageContent {
        color: #ffffff !important;
    }
    /* 助手气泡 */
    [data-testid="stChatMessage"]:not([data-testid*="user"]) {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
    }
    [data-testid="stChatMessage"]:not([data-testid*="user"]) .stChatMessageContent {
        color: #1e293b !important;
    }

    /* 聊天头像 */
    [data-testid="stChatMessageAvatar"] {
        border-radius: 50%;
        overflow: hidden;
    }

    /* ===== 输入框 ===== */
    [data-testid="stChatInput"] textarea {
        border-radius: 12px !important;
        border: 1.5px solid #cbd5e1 !important;
        background: #ffffff !important;
        transition: all 0.2s;
    }
    [data-testid="stChatInput"] textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important;
    }

    /* ===== 退出按钮 ===== */
    .stButton button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s;
    }

    /* ===== Radio 按钮美化 ===== */
    [data-testid="stSidebar"] .stRadio > div {
        gap: 0.3rem;
    }
    [data-testid="stSidebar"] .stRadio label {
        border-radius: 8px;
        padding: 0.45rem 0.7rem;
        transition: all 0.15s;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(255,255,255,0.08);
    }

    /* ===== 滚动条 ===== */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: #94a3b8;
        border-radius: 3px;
    }
</style>
""", unsafe_allow_html=True)

# ========== 登录逻辑（已跳过，方便演示） ==========
if "logged_in" not in st.session_state:
    st.session_state.logged_in = True
    st.session_state.username = "admin"
    st.session_state.current_dept = "🖥️ IT部门"

# ========== 直接进入（免登录，方便演示） ==========
available_depts = list(DEPARTMENTS.keys())

# ---- 侧边栏 ----
with st.sidebar:
    st.markdown('<div class="sidebar-title">🏢 企业知识库</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subtitle">内部智能问答系统</div>', unsafe_allow_html=True)

    # 当前用户
    st.markdown(f"""
    <div style="color:#94a3b8; font-size:0.78rem; margin-bottom:0.2rem;">
        👋 欢迎，<b style="color:#e2e8f0;">{st.session_state.username}</b>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("##### 📂 选择部门")
    selected = st.radio("", available_depts, label_visibility="collapsed")

    # 部门信息卡片
    dept_info = DEPARTMENTS[selected]
    st.markdown(f"""
    <div class="dept-card">
        <div class="dept-icon">{selected[:2]}</div>
        <div class="dept-name">{selected}</div>
        <div class="dept-desc">{dept_info['desc']}</div>
    </div>
    """, unsafe_allow_html=True)

    # 加载向量库并显示状态
    try:
        stats = init_vector_db()
        st.success(f"✅ 向量库就绪 · {stats['total_chunks']} 个片段")
        st.caption("各部门文档数：")
        for dept, count in stats["by_department"].items():
            st.caption(f"  {dept}：{count}")
    except Exception as e:
        st.warning(f"⚠️ 向量库加载：{e}")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 退出登录", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.messages = []
        st.rerun()

# ---- 主界面 ----
# 顶部标题栏
st.markdown(f"""
<div class="main-header">
    <h2>📋 {selected}</h2>
    <div class="header-sub">{DEPARTMENTS[selected]['desc']}</div>
</div>
""", unsafe_allow_html=True)

# 切换部门时清空对话
if "current_dept" not in st.session_state:
    st.session_state.current_dept = selected
if st.session_state.current_dept != selected:
    st.session_state.messages = []
    st.session_state.current_dept = selected

if "messages" not in st.session_state:
    st.session_state.messages = []

# 欢迎面板（无消息时显示）
if len(st.session_state.messages) == 0:
    st.markdown("""
    <div class="welcome-panel">
        <div class="welcome-icon">💡</div>
        <h3>欢迎使用企业知识库助手</h3>
        <div class="welcome-text">
            我是您的专属智能助手，可以帮您快速查询<br>
            内部流程、政策规范、操作指南等各类知识
        </div>
        <div style="margin-top:1.2rem;">
            <span class="tip-box">💬 直接提问，我会从知识库中查找答案</span><br style="display:none;">
            <span class="tip-box">📌 切换部门可获取不同领域的专业解答</span><br style="display:none;">
            <span class="tip-box">🔍 新功能：向量语义检索，准确率提升 60%+</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 显示历史对话
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 输入框
if prompt := st.chat_input("💬 输入你的问题，按 Enter 发送..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🔍 语义检索中..."):
            # 用向量检索替代关键词匹配
            results = hybrid_search(prompt, top_n=3, department=dept_info["key"])
            context = "\n\n".join([r["content"] for r in results])

            # 显示检索来源
            if results:
                with st.expander(f"📎 检索到 {len(results)} 条相关知识 (相似度: {results[0]['score']:.2f})"):
                    for r in results:
                        st.caption(f"[{r['department']}] 相关性 {r['score']:.2f}")
                        st.text(r["content"][:200] + "...")

            messages = [{"role": "system", "content": dept_info["prompt"]}]
            if context:
                messages.append({
                    "role": "system",
                    "content": f"以下是知识库中的相关内容，优先参考：\n\n{context}"
                })
            messages += st.session_state.messages

            response = client.chat.completions.create(
                model="deepseek-chat",
                max_tokens=2048,
                messages=messages
            )
            reply = response.choices[0].message.content
            st.write(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})