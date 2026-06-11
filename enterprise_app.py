import os
os.environ["PYTHONIOENCODING"] = "utf-8"

import streamlit as st
from openai import OpenAI

API_KEY = "key"  # 替换这里

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

# 部门配置
DEPARTMENTS = {
    "🖥️ IT部门": {
        "file": "docs/故障案例.txt",
        "prompt": "You are a senior IT support engineer. Answer based on the case library. Reply in Chinese."
    },
    "👥 HR部门": {
        "file": "docs/hr.txt",
        "prompt": "You are an experienced HR specialist. Answer based on the HR knowledge base. Reply in Chinese."
    },
    "🏢 行政部门": {
        "file": "docs/admin.txt",
        "prompt": "You are an admin department specialist. Answer based on the admin knowledge base. Reply in Chinese."
    },
    "📞 客服部门": {
        "file": "docs/service.txt",
        "prompt": "You are a customer service specialist. Answer based on the service knowledge base. Reply in Chinese."
    },
    "💼 销售部门": {
        "file": "docs/sales.txt",
        "prompt": "You are a sales operations specialist. Answer based on the sales knowledge base. Reply in Chinese."
    },
}

# 用户账号配置：用户名、密码、可访问的部门
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

# 页面设置
st.set_page_config(page_title="企业知识库助手", page_icon="🏢", layout="wide")
st.title("🏢 企业内部知识库助手")
st.caption("选择部门，快速获取内部流程和政策解答")
# 登录状态初始化
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# 未登录显示登录页
if not st.session_state.logged_in:
    st.title("🏢 企业内部知识库助手")
    st.subheader("请登录")
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")
    if st.button("登录"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("用户名或密码错误")
    st.stop()

# 已登录，获取该用户可访问的部门
user = USERS[st.session_state.username]
if user["departments"] == "all":
    available_depts = list(DEPARTMENTS.keys())
else:
    available_depts = user["departments"]

# 侧边栏选择部门
st.sidebar.title("选择部门")
col1, col2 = st.columns([6, 1])
with col2:
    if st.button("退出登录"):
        st.session_state.logged_in = False
        st.session_state.messages = []
        st.rerun()

selected = st.sidebar.radio("", available_depts)

# 加载对应部门文档
dept = DEPARTMENTS[selected]
chunks = load_docs(dept["file"])

if chunks:
    st.sidebar.success(f"✅ 已加载 {len(chunks)} 条知识")
else:
    st.sidebar.error("❌ 文档未找到")

# 切换部门时清空对话
if "current_dept" not in st.session_state:
    st.session_state.current_dept = selected
if st.session_state.current_dept != selected:
    st.session_state.messages = []
    st.session_state.current_dept = selected

# 初始化对话历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示当前部门
st.subheader(f"当前部门：{selected}")

# 显示历史对话
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 输入框
if prompt := st.chat_input("输入你的问题..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("查询知识库中..."):
            context = ""
            if chunks:
                relevant = find_relevant(prompt, chunks)
                context = "\n\n".join(relevant)

            messages = [{"role": "system", "content": dept["prompt"]}]
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