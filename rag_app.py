import os
import streamlit as st
from openai import OpenAI
from retriever import load_and_index, hybrid_search, get_stats, COLLECTION_NAME

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

SYSTEM_PROMPT = """你是一位资深桌面运维工程师，有10年企业IT支持经验。
当用户描述电脑问题时，你需要：
1. 判断可能的故障原因（从最常见到最少见排列）
2. 给出具体的排查步骤（包含实际操作或命令）
3. 给出预防建议
回答简洁实用，直接给步骤。默认Windows环境。"""

# 加载 IT 知识库并建立向量索引
DOCS = {
    "IT": "docs/故障案例.txt",
    "HR": "docs/hr.txt",
    "行政": "docs/admin.txt",
    "客服": "docs/service.txt",
    "销售": "docs/sales.txt",
}

@st.cache_resource
def init_knowledge_base():
    """启动时加载所有文档到 ChromaDB 向量库"""
    count = load_and_index(DOCS)
    return get_stats()

# 页面设置
st.set_page_config(page_title="IT运维知识库 v2", page_icon="🖥️")
st.title("🖥️ IT运维知识库助手 v2")
st.caption("基于向量语义检索的智能问答系统 · ChromaDB + RAG")

# 侧边栏：知识库状态
with st.sidebar:
    st.header("📊 知识库状态")
    try:
        stats = init_knowledge_base()
        st.success(f"✅ 向量库就绪 · {stats['total_chunks']} 个片段")
        st.caption("各部门文档数：")
        for dept, count in stats["by_department"].items():
            st.caption(f"  {dept}：{count}")
    except Exception as e:
        st.warning(f"⚠️ 向量库加载失败：{e}")

    st.divider()
    st.caption("🔍 检索方式：语义向量 + 关键词混合")

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
        with st.spinner("🔍 语义检索中..."):
            # 向量语义检索
            results = hybrid_search(prompt, top_n=3, department="IT")
            context = "\n\n".join([r["content"] for r in results])

            # 显示检索来源（增加可信度）
            if results:
                with st.expander(f"📎 检索到 {len(results)} 条相关知识 (相似度: {results[0]['score']:.2f})"):
                    for r in results:
                        st.caption(f"[{r['department']}] 相关性 {r['score']:.2f}")
                        st.text(r["content"][:200] + "...")

            # 构建消息
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
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
