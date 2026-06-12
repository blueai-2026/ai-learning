import os
os.environ["PYTHONIOENCODING"] = "utf-8"

from openai import OpenAI

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

# 读取文档
print("正在加载知识库...")
with open("docs/故障案例.txt", "r", encoding="utf-8") as f:
    content = f.read()

# 按空行切割成段落
chunks = [c.strip() for c in content.split("\n\n") if c.strip()]
print(f"已加载 {len(chunks)} 个知识片段\n")

def find_relevant(question, chunks, top_n=2):
    """简单关键词匹配找相关段落"""
    scored = []
    keywords = question.replace("，", " ").replace("。", " ").split()
    for chunk in chunks:
        score = sum(1 for kw in keywords if kw in chunk)
        scored.append((score, chunk))
    scored.sort(reverse=True)
    return [c for _, c in scored[:top_n]]

print("=== IT知识库问答 ===")
print("输入 quit 退出\n")

while True:
    question = input("你的问题：").strip()
    if question.lower() == "quit":
        break
    if not question:
        continue

    # 找相关内容
    relevant = find_relevant(question, chunks)
    context = "\n\n".join(relevant)

    prompt = f"""根据以下IT故障案例库回答问题。

案例库内容：
{context}

问题：{question}

请根据案例库内容回答，如果案例库中没有相关信息，请说明。"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    print(f"\n回答：{response.choices[0].message.content}\n")
    print("-" * 50 + "\n")