import os
os.environ["PYTHONIOENCODING"] = "utf-8"

import streamlit as st
from openai import OpenAI

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

# 部门配置
DEPARTMENTS = {
    "🖥️ IT部门": {
        "file": "docs/故障案例.txt",
        "prompt": "You are a senior IT support engineer. Answer based on the case library. Reply in Chinese.",
        "desc": "技术故障排查与IT支持，解决电脑、网络、打印机等问题"
    },
    "👥 HR部门": {
        "file": "docs/hr.txt",
        "prompt": "You are an experienced HR specialist. Answer based on the HR knowledge base. Reply in Chinese.",
        "desc": "人事政策、考勤假期、薪资福利、入职离职流程"
    },
    "🏢 行政部门": {
        "file": "docs/admin.txt",
        "prompt": "You are an admin department specialist. Answer based on the admin knowledge base. Reply in Chinese.",
        "desc": "行政流程、办公资产管理、会议安排与后勤保障"
    },
    "📞 客服部门": {
        "file": "docs/service.txt",
        "prompt": "You are a customer service specialist. Answer based on the service knowledge base. Reply in Chinese.",
        "desc": "客户咨询处理、投诉跟进、售后服务标准流程"
    },
    "💼 销售部门": {
        "file": "docs/sales.txt",
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

def load_docs(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return [c.strip() for c in content.split("\n\n") if c.strip()]
    except:
        return []

def find_relevant(question, chunks, top_n=2):
    keywords = question.replace("，", " ").replace("。", " ").split()
    scored = []
    for chunk in chunks:
        score = sum(1 for kw in keywords if kw in chunk)
        scored.append((score, chunk))
    scored.sort(reverse=True)
    return [c for _, c in scored[:top_n]]

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
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stRadio label {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] .stSuccess {
        background-color: rgba(16, 185, 129, 0.2) !important;
        border: 1px solid rgba(16, 185, 129, 0.4) !important;
        color: #a7f3d0 !important;
    }
    [data-testid="stSidebar"] .stError {
        background-color: rgba(239, 68, 68, 0.2) !important;
        border: 1px solid rgba(239, 68, 68, 0.4) !important;
        color: #fca5a5 !important;
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

# ========== 登录逻辑 ==========
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.logged_in:
    # 登录页也应用蓝白风格
    st.markdown("""
    <div style="max-width:420px; margin:4rem auto; text-align:center;">
        <div style="font-size:3.5rem; margin-bottom:1rem;">🏢</div>
        <h2 style="color:#1e3a5f; margin-bottom:0.3rem;">企业内部知识库</h2>
        <p style="color:#64748b; margin-bottom:2rem; font-size:0.9rem;">请使用您的账号登录</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.container(border=True):
            username = st.text_input("👤 用户名", placeholder="请输入用户名")
            password = st.text_input("🔒 密码", type="password", placeholder="请输入密码")
            if st.button("登 录", use_container_width=True, type="primary"):
                if username in USERS and USERS[username]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("用户名或密码错误")
    st.stop()

# ========== 已登录 ==========
user = USERS[st.session_state.username]
if user["departments"] == "all":
    available_depts = list(DEPARTMENTS.keys())
else:
    available_depts = user["departments"]

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

    # 加载状态
    chunks = load_docs(dept_info["file"])
    if chunks:
        st.success(f"✅ 已加载 {len(chunks)} 条知识")
    else:
        st.error("❌ 文档未找到")

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
            <span class="tip-box">🔍 尝试问「打印机故障怎么办」「请假流程是什么」</span>
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
        with st.spinner("🔍 正在查询知识库..."):
            context = ""
            if chunks:
                relevant = find_relevant(prompt, chunks)
                context = "\n\n".join(relevant)

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