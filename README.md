# 🏢 企业智能知识库助手

基于 **RAG + ChromaDB 向量检索 + LangChain Agent** 的企业级多部门智能问答系统。

> 从零学习 AI 应用开发的完整过程记录，6 个迭代版本展示从 API 调用到生产级应用的演进路径。

## ✨ 核心功能

- **语义向量检索**：ChromaDB 向量数据库替代传统关键词匹配，检索准确率大幅提升
- **多部门知识库**：覆盖 IT、HR、行政、客服、销售 5 个部门，支持部门切换
- **LangChain Agent**：自动判断用户查询意图，智能路由到对应部门知识库
- **权限控制**：6 种用户角色，不同角色可访问不同部门知识库
- **Docker 容器化**：一键部署到 Linux 服务器，开箱即用
- **美观 UI**：蓝白配色的 Streamlit 网页界面，聊天气泡式交互

## 🧱 技术架构

```
用户浏览器 (Streamlit UI)
        │
        ▼
┌──────────────────┐
│   应用层          │
│  enterprise_app  │  ← 多部门 + 登录权限
│  rag_app         │  ← 单部门知识库
│  agent           │  ← LangChain Agent 自动路由
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│   检索层          │
│   retriever.py   │  ← ChromaDB 向量语义检索
│   hybrid_search  │  ← 混合检索（语义 + 关键词兜底）
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│   模型层          │
│   DeepSeek API   │  ← 大语言模型（Chat + Embedding）
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│   存储层          │
│   ChromaDB       │  ← 向量数据库（持久化）
│   docs/*.txt      │  ← 原始文档
└──────────────────┘
```

## 📂 文件说明

| 文件 | 说明 | 演进阶段 |
|------|------|----------|
| `hello_deepseek.py` | API 连通性测试 | 第 1 步：验证环境 |
| `chat_deepseek.py` | 多轮对话 | 第 2 步：对话管理 |
| `network_helper_deepseek.py` | 故障排查助手 | 第 3 步：Prompt 工程 |
| `rag.py` | RAG 命令行版 | 第 4 步：知识库接入 |
| `rag_app.py` | RAG 网页版（Streamlit） | 第 5 步：可视化 |
| `agent.py` | LangChain Agent | 第 6 步：工具调用 |
| `agent_app.py` | 多部门 Agent 网页版 | 第 7 步：多知识库 |
| `enterprise_app.py` | **企业完整版** ⭐ | 第 8 步：生产级 |
| `retriever.py` | **向量检索模块** v2 | ChromaDB 语义检索 |
| `docs/` | 5 个部门知识库文档 | 业务数据 |
| `新员工入职材料清单.txt` | 入职流程参考 | 行政文档 |
| `打印机无法打印解决方案.txt` | 故障案例 | IT 文档 |

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/blueai-2026/ai-learning.git
cd ai-learning
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

```bash
# Linux/Mac
export DEEPSEEK_API_KEY="your-api-key"

# Windows PowerShell
$env:DEEPSEEK_API_KEY="your-api-key"
```

> 去 [platform.deepseek.com](https://platform.deepseek.com) 注册并获取 API Key

### 4. 运行

```bash
# 企业完整版（推荐）
streamlit run enterprise_app.py

# 或单部门版本
streamlit run rag_app.py
```

然后浏览器打开 `http://localhost:8501`

### 5. Docker 部署

```bash
docker build -t enterprise-kb .
docker run -p 8501:8501 -e DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY enterprise-kb
```

## 🧪 检索方式对比

本系统在迭代中经历了检索策略的演进：

| 版本 | 检索方式 | 原理 | 效果 |
|------|----------|------|------|
| v1 | 关键词匹配 `kw in chunk` | 字符串包含判断 | 基础可用，但"没法上网"匹配不到"无法连接网络" |
| v2 | ChromaDB 向量检索 | 语义相似度计算 | "电脑连不上" ↔ "网络无法连接" 自动关联 |

## 👥 内置测试账号

| 账号 | 密码 | 可访问部门 |
|------|------|-----------|
| admin | admin123 | 全部 |
| it | it123 | IT 部门 |
| hr | hr123 | HR 部门 |
| admin_dept | admin456 | 行政部门 |
| service | service123 | 客服部门 |
| sales | sales123 | 销售部门 |

## 🎯 学习要点

这个项目展示了 AI 应用工程师的核心能力：

- **LLM API 调用**：OpenAI 兼容接口，DeepSeek / OpenAI / 通义千问 可互换
- **Prompt 工程**：System Prompt 设计、上下文注入、角色控制
- **RAG 系统**：文档加载 → 切片 → 向量化 → 检索 → 增强生成，全链路掌握
- **向量数据库**：ChromaDB 的嵌入、存储、语义查询
- **Agent 开发**：LangChain Tool Calling，工具定义、意图路由、结果保存
- **工程化**：Streamlit UI、Docker 部署、环境变量管理、权限控制

## 📋 技术栈

`Python 3.11` `Streamlit` `DeepSeek API` `LangChain` `ChromaDB` `Docker` `OpenAI SDK`

---

> 这是我从 IT 运维转 AI 应用工程师的实战学习项目。如果对你有帮助，欢迎 Star ⭐
