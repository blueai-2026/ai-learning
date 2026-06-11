import os
os.environ["PYTHONIOENCODING"] = "utf-8"

import streamlit as st
from openai import OpenAI

API_KEY = "key"  # 替换这里

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

SYSTEM_PROMPT = """You are a senior desktop IT support engineer with 10 years of enterprise experience.
Answer the user's question based on the provided case library.
If the case library has relevant information, use it as the primary reference.
If not, answer based on your own knowledge.
Reply in Chinese. Be concise and practical."""

def find_relevant(question, chunks, top_n=2):
    keywords = question.replace("，", " ").replace("。", " ").split()
    scored = []
    for chunk in chunks:
        score = sum(1 for kw in keywords if kw in chunk)
        scored.append((score, chunk))
    scored.sort(reverse=True)
    return [c for _, c in scored[:top_n]]

def load_docs():
    try:
        with open("docs/故障案例.txt", "r", encoding="utf-8") as f:
            content = f.read()
        chunks = [c.strip() for c in content.split("\n\n") if c.strip()]
        return chunks
    except:
        return []

# 页面设置
st.set_page_config(page_title="IT运维知识库", page_icon="🖥️")
st.title("🖥️ IT运维知识库助手")
st.caption("基于内部故障案例库的智能问答系统")

# 加载知识库
chunks = load_docs()
if chunks:
    st.sidebar.success(f"✅ 知识库已加载 {len(chunks)} 个案例")
else:
    st.sidebar.warning("⚠️ 知识库未找到")

# 初始化对话历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史对话
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 输入框
if prompt := st.chat_input("描述你的IT问题..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("查询知识库中..."):
            # 从知识库找相关内容
            context = ""
            if chunks:
                relevant = find_relevant(prompt, chunks)
                context = "\n\n".join(relevant)

            # 构建带知识库的消息
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            if context:
                messages.append({
                    "role": "system",
                    "content": f"以下是内部故障案例库中的相关内容，优先参考：\n\n{context}"
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