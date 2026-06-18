import os
os.environ["PYTHONIOENCODING"] = "utf-8"

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from retriever import load_and_index, hybrid_search, get_stats

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

# 初始化LLM
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=API_KEY,
    base_url="https://api.deepseek.com",
)

# 建立向量索引
DOCS = {
    "IT": "docs/故障案例.txt",
    "HR": "docs/hr.txt",
    "行政": "docs/admin.txt",
    "客服": "docs/service.txt",
    "销售": "docs/sales.txt",
}
load_and_index(DOCS)
stats = get_stats()
print(f"向量库就绪：{stats['total_chunks']} 个片段")

# 定义工具
@tool
def search_knowledge_base(query: str) -> str:
    """从IT故障知识库中搜索相关解决方案（使用向量语义检索）"""
    relevant = hybrid_search(query, top_n=2, department="IT")
    if relevant:
        return "\n\n".join([r["content"] for r in relevant])
    return "知识库中没有找到相关信息"

@tool
def save_to_file(content: str, filename: str = "解决方案.txt") -> str:
    """把内容保存到文件"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return f"已保存到 {filename}"

# 创建Agent
tools = [search_knowledge_base, save_to_file]

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个IT运维助手，可以查询知识库和保存文件。用中文回答。"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

print("=== IT运维Agent ===")
print("输入 quit 退出\n")

while True:
    user_input = input("你：").strip()
    if user_input.lower() == "quit":
        break
    if not user_input:
        continue

    result = agent_executor.invoke({"input": user_input})
    print(f"\nAgent：{result['output']}\n")
    print("-" * 50 + "\n")