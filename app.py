import streamlit as st
from openai import OpenAI
import os
os.environ["PYTHONIOENCODING"] = "utf-8"

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

SYSTEM_PROMPT = """你是一位资深桌面运维工程师，有10年企业IT支持经验。
当用户描述电脑问题时，你需要：
1. 判断可能的故障原因（从最常见到最少见排列）
2. 给出具体的排查步骤（包含实际操作或命令）
3. 给出预防建议
回答简洁实用，直接给步骤。默认Windows环境。"""

st.title("🖥️ 桌面运维助手")
st.caption("描述你遇到的电脑问题，AI帮你排查")

# 初始化对话历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史对话
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 输入框
if prompt := st.chat_input("描述故障现象..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("分析中..."):
            response = client.chat.completions.create(
                model="deepseek-chat",
                max_tokens=2048,
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages
            )
            reply = response.choices[0].message.content
            st.write(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})