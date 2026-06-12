import os
os.environ["PYTHONIOENCODING"] = "utf-8"

import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate

API_KEY = "key"  # 替换这里

llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=API_KEY,
    base_url="https://api.deepseek.com",
)

# 加载所有部门知识库
DOCS = {
    "IT":   "docs/故障案例.txt",
    "HR":   "docs/hr.txt",
    "行政": "docs/admin.txt",
    "客服": "docs/service.txt",
    "销售": "docs/sales.txt",
}

def load_all_docs():
    all_chunks = {}
    for dept, path in DOCS.items():
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            all_chunks[dept] = [c.strip() for c in content.split("\n\n") if c.strip()]
        except:
            all_chunks[dept] = []
    return all_chunks

def find_relevant(query, chunks, top_n=2):
    keywords = query.replace("，", " ").replace("。", " ").split()
    scored = [(sum(1 for kw in keywords if kw in c), c) for c in chunks]
    scored.sort(reverse=True)
    return [c for _, c in scored[:top_n]]

all_chunks = load_all_docs()

# 定义工具
@tool
def search_all_departments(query: str) -> str:
    """搜索所有部门的知识库，返回最相关的内容"""
    results = []
    for dept, chunks in all_chunks.items():
        relevant = find_relevant(query, chunks)
        if relevant and any(relevant):
            results.append(f"【{dept}部门】\n" + "\n".join(relevant))
    return "\n\n".join(results) if results else "未找到相关信息"

@tool
def search_department(query: str, department: str) -> str:
    """搜索指定部门的知识库，department可以是IT/HR/行政/客服/销售"""
    chunks = all_chunks.get(department, [])
    if not chunks:
        return f"{department}部门知识库未找到"
    relevant = find_relevant(query, chunks)
    return "\n\n".join(relevant) if relevant else "未找到相关信息"

@tool
def save_solution(content: str, filename: str) -> str:
    """把解决方案保存到文件"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return f"已保存到 {filename}"

# 创建Agent
tools = [search_all_departments, search_department, save_solution]

prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个企业内部智能助手，可以查询各部门知识库。
你有以下工具：
- search_all_departments：搜索所有部门
- search_department：搜索指定部门
- save_solution：保存解决方案到文件

根据用户问题判断应该查哪个部门，用中文回答，回答要简洁实用。"""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

# 页面设置
st.set_page_config(page_title="企业智能助手", page_icon="🤖", layout="wide")
st.title("🤖 企业智能助手")
st.caption("基于Agent技术，自动查询各部门知识库")

# 初始化对话历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 侧边栏
st.sidebar.title("使用说明")
st.sidebar.info("""
**可以问我：**
- IT故障处理
- HR入职离职流程
- 行政申请流程
- 客服处理规范
- 销售合同流程

**Agent能力：**
- 自动判断查哪个部门
- 跨部门综合查询
- 保存解决方案到文件
""")

# 显示历史对话
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 输入框
if prompt_input := st.chat_input("问我任何关于公司流程的问题..."):
    st.session_state.messages.append({"role": "user", "content": prompt_input})
    with st.chat_message("user"):
        st.write(prompt_input)

    with st.chat_message("assistant"):
        with st.spinner("Agent思考中..."):
            result = agent_executor.invoke({"input": prompt_input})
            reply = result["output"]
            st.write(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})