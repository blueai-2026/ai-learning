# 第三步：网络故障排查助手
# 结合你的运维经验，这是一个真实有用的AI工具

from openai import OpenAI

API_KEY = "sk-3ad1591e9d034704bbe4aa0407fa3edc"  # 替换这里

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

# 系统提示：让AI扮演网络运维专家
# 这是"Prompt工程"的核心——通过系统提示控制AI的行为
SYSTEM_PROMPT = """你是一位资深桌面运维工程师，有10年企业IT支持经验。
当用户描述电脑问题时，你需要：
1. 判断可能的故障原因（从最常见到最少见排列）
2. 给出具体的排查步骤（包含实际操作或命令）
3. 给出预防建议

回答简洁实用，直接给步骤。默认Windows环境，用户说Linux再切换。"""

history = []
import datetime
log_file = f"故障记录_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

print("=== 网络故障排查助手 ===")
print("描述你遇到的网络问题，我来帮你排查")
print("输入 quit 退出\n")

while True:
    user_input = input("故障描述：").strip()

    if user_input.lower() == "quit":
        print("再见！")
        break

    if not user_input:
        continue

    history.append({
        "role": "user",
        "content": user_input
    })

    print("\n正在分析...\n")

    # system prompt 作为第一条消息传入
    response = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=2048,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history
    )

    reply = response.choices[0].message.content

    history.append({
        "role": "assistant",
        "content": reply
    })
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"问题：{user_input}\n\n排查建议：\n{reply}\n\n{'='*50}\n\n")

    print(f"排查建议：\n{reply}\n")
    print("-" * 50 + "\n")
