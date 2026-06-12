# 第二步：多轮对话
# 可以连续和DeepSeek对话，输入 quit 退出

from openai import OpenAI

API_KEY = "key"  # 替换这里

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

# 存储对话历史（这是实现多轮对话的关键）
history = []

print("=== 和DeepSeek对话 ===")
print("输入 quit 退出\n")

while True:
    user_input = input("你：").strip()

    if user_input.lower() == "quit":
        print("再见！")
        break

    if not user_input:
        continue

    # 把用户消息加入历史
    history.append({
        "role": "user",
        "content": user_input
    })

    # 发送整个对话历史（这样它才能记住上下文）
    response = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=1024,
        messages=history
    )

    reply = response.choices[0].message.content

    # 把回复也加入历史
    history.append({
        "role": "assistant",
        "content": reply
    })

    print(f"\nDeepSeek：{reply}\n")
