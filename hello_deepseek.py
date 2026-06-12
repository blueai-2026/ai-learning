# 第一步：验证API能跑通
# 运行前把下面的 YOUR_API_KEY 替换成你的真实key
# 去 https://platform.deepseek.com 获取key

import os
from openai import OpenAI

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-chat",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "用一句话介绍你自己"}
    ]
)

print("DeepSeek说：", response.choices[0].message.content)
print("\n✅ API连接成功！")
