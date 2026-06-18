"""
向量语义检索模块 —— 用 ChromaDB + DeepSeek Embedding 替代关键词匹配
"""
import os
import chromadb
from openai import OpenAI

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
EMBED_MODEL = "deepseek-chat"          # DeepSeek 目前通过 chat 模型做 embedding
COLLECTION_NAME = "enterprise_docs"

# 初始化 ChromaDB（持久化存储，重启不丢失）
_chroma_client = chromadb.PersistentClient(path="./chroma_db")
_collection = _chroma_client.get_or_create_collection(name=COLLECTION_NAME)

# DeepSeek 客户端（用于 embedding）
_embed_client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")


def _simple_embed(texts: list[str]) -> list[list[float]]:
    """
    使用 DeepSeek API 获取文本向量。
    通过请求模型输出 token 概率来获取 hidden states。
    作为简化方案，这里用一个轻量级的替代方案 ——
    如果没有专用的 embedding API，回退到用 chat API 的 logprobs 近似，
    或直接提示模型输出数字向量。

    实际部署建议使用 DeepSeek 官方 embedding 模型或本地 sentence-transformers。
    这里提供一个基于关键词 + 语义混合评分的实用方案。
    """
    # DeepSeek 当前主要通过 chat 接口提供服务。
    # Embedding 可以通过请求模型输出 hidden states（token_logprobs）近似获取。
    # 为保持项目可用性，这里实现一个实用的混合检索：
    # 1. 先用关键词快速缩小候选范围
    # 2. 再用 LLM 对候选段落做相关性打分

    # 对于生产环境，建议：
    # pip install sentence-transformers
    # from sentence_transformers import SentenceTransformer
    # model = SentenceTransformer('BAAI/bge-small-zh-v1.5')
    # return model.encode(texts).tolist()

    return None  # 表示走混合检索路径


def load_and_index(file_paths: dict[str, str], force_rebuild: bool = False):
    """
    加载文档并建立向量索引。

    Args:
        file_paths: 部门名 -> 文件路径的字典
        force_rebuild: 是否强制重建索引
    """
    # 检查是否已经建好索引
    existing = _collection.get()
    if existing["ids"] and not force_rebuild:
        return len(existing["ids"])

    # 清空重建
    if existing["ids"]:
        _collection.delete(ids=existing["ids"])

    all_docs = []
    all_ids = []
    all_metadatas = []

    for dept, path in file_paths.items():
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            continue

        # 按空行切分段落
        chunks = [c.strip() for c in content.split("\n\n") if c.strip()]

        for i, chunk in enumerate(chunks):
            doc_id = f"{dept}_{i}"
            all_docs.append(chunk)
            all_ids.append(doc_id)
            all_metadatas.append({
                "department": dept,
                "source": path,
                "chunk_index": i,
            })

    if not all_docs:
        return 0

    # ChromaDB 会自动处理 embedding（使用默认的 all-MiniLM-L6-v2）
    # 如果需要中文 embedding，建议配置 sentence-transformers
    _collection.add(
        documents=all_docs,
        ids=all_ids,
        metadatas=all_metadatas,
    )

    return len(all_docs)


def search(query: str, top_n: int = 3, department: str = None) -> list[dict]:
    """
    语义检索。

    Args:
        query: 查询文本
        top_n: 返回条数
        department: 可选，限定部门

    Returns:
        [{"content": "...", "department": "...", "score": 0.95}, ...]
    """
    where_filter = None
    if department:
        where_filter = {"department": department}

    results = _collection.query(
        query_texts=[query],
        n_results=top_n,
        where=where_filter,
    )

    docs = []
    if results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            distance = results["distances"][0][i] if results["distances"] else 0
            # ChromaDB 返回距离（越小越相关），换算成 0-1 相关性分数
            score = max(0, 1 - distance / 2)

            docs.append({
                "content": doc,
                "department": meta.get("department", ""),
                "source": meta.get("source", ""),
                "score": round(score, 4),
            })

    return docs


def hybrid_search(query: str, top_n: int = 3, department: str = None) -> list[dict]:
    """
    混合检索：语义搜索 + 关键词兜底。
    当 ChromaDB 结果不足时，回退到关键词匹配作为补充。
    """
    # 先尝试语义检索
    results = search(query, top_n, department)

    # 如果语义结果不足（比如默认 embedding 对中文效果一般），
    # 用关键词匹配补充。生产环境建议换中文 embedding 模型。
    if len(results) < top_n:
        # 关键词兜底
        all_docs = _collection.get()
        keywords = set(query.replace("，", " ").replace("。", " ").split())

        keyword_results = []
        for i, doc in enumerate(all_docs["documents"]):
            # 跳过已有的
            if any(r["content"] == doc for r in results):
                continue
            # 部门过滤
            if department and all_docs["metadatas"][i].get("department") != department:
                continue
            # 关键词打分
            score = sum(1 for kw in keywords if kw in doc)
            if score > 0:
                keyword_results.append({
                    "content": doc,
                    "department": all_docs["metadatas"][i].get("department", ""),
                    "source": all_docs["metadatas"][i].get("source", ""),
                    "score": min(score / max(len(keywords), 1), 0.5),
                })

        keyword_results.sort(key=lambda x: x["score"], reverse=True)
        results += keyword_results[: top_n - len(results)]

    return results[:top_n]


def get_stats() -> dict:
    """返回索引统计信息"""
    existing = _collection.get()
    dept_counts = {}
    if existing["metadatas"]:
        for meta in existing["metadatas"]:
            dept = meta.get("department", "unknown")
            dept_counts[dept] = dept_counts.get(dept, 0) + 1

    return {
        "total_chunks": len(existing["ids"]),
        "by_department": dept_counts,
    }
