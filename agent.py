import os
os.environ["PYTHONIOENCODING"] = "utf-8"

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from openai import OpenAI

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

# 初始化LLM
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=API_KEY,
    base_url="https://api.deepseek.com",
)

# 加载知识库
with open("docs/故障案例.txt", "r", encoding="utf-8") as f:
    content = f.read()
chunks = [c.strip() for c in content.split("\n\n") if c.strip()]

def find_relevant(question, chunks, top_n=2):
    keywords = question.replace("，", " ").replace("。", " ").split()
    scored = [(sum(1 for kw in keywords if kw in c), c) for c in chunks]
    scored.sort(reverse=True)
    return [c for _, c in scored[:top_n]]

# 定义工具
@tool
def search_knowledge_base(query: str) -> str:
    """从IT故障知识库中搜索相关解决方案"""
    relevant = find_relevant(query, chunks)
    if relevant:
        return "\n\n".join(relevant)
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