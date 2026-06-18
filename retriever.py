"""
向量语义检索模块
自动检测 ChromaDB 是否可用：
  - 可用 → 向量语义检索
  - 不可用（如 Streamlit Cloud 环境冲突）→ 降级为纯 Python 关键词+相关性匹配
"""
import os
import re
import math

# ─── 尝试导入 ChromaDB ───
CHROMA_AVAILABLE = False
try:
    import chromadb
    CHROMA_AVAILABLE = True
except Exception:
    pass

# ─── 配置 ───
COLLECTION_NAME = "enterprise_docs"

# ─── 纯 Python 降级检索器（不依赖任何第三方库） ───
class FallbackRetriever:
    """基于 TF-IDF + 余弦相似度的轻量检索，零依赖"""

    def __init__(self):
        self.documents: list[str] = []
        self.metadatas: list[dict] = []

    def add(self, documents, ids=None, metadatas=None):
        self.documents = list(documents)
        self.metadatas = list(metadatas) if metadatas else [{} for _ in documents]

    def get(self):
        return {"documents": self.documents, "metadatas": self.metadatas, "ids": list(range(len(self.documents)))}

    def _tokenize(self, text: str) -> list[str]:
        """中文分词：按标点和空格切分 + 2-gram"""
        # 去掉标点，按空格/标点分
        cleaned = re.sub(r'[，。；：！？、""''（）【】\s]+', ' ', text)
        tokens = [t for t in cleaned.split() if len(t) >= 1]
        # 加 2-gram 增强匹配
        bigrams = []
        for i in range(len(tokens) - 1):
            bigrams.append(tokens[i] + tokens[i+1])
        return tokens + bigrams

    def _tfidf_vector(self, text: str, doc_freq: dict, num_docs: int) -> dict:
        """计算文本的 TF-IDF 向量"""
        tokens = self._tokenize(text)
        tf = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1

        # TF * IDF
        vec = {}
        for t, freq in tf.items():
            tf_val = 1 + math.log(freq)  # sublinear TF
            df = doc_freq.get(t, 1)
            idf = math.log((num_docs + 1) / (df + 1)) + 1
            vec[t] = tf_val * idf
        return vec

    def _cosine(self, v1: dict, v2: dict) -> float:
        """两个稀疏向量的余弦相似度"""
        dot = sum(v1.get(k, 0) * v2.get(k, 0) for k in set(v1) | set(v2))
        norm1 = math.sqrt(sum(v**2 for v in v1.values()))
        norm2 = math.sqrt(sum(v**2 for v in v2.values()))
        if norm1 == 0 or norm2 == 0:
            return 0
        return dot / (norm1 * norm2)

    def query(self, query_texts: list[str], n_results: int = 3,
              where: dict = None) -> dict:
        """执行检索"""
        query = query_texts[0]
        num_docs = len(self.documents)

        # 构建文档的词频统计
        doc_freq = {}
        doc_vectors = []
        for doc in self.documents:
            vec = {}
            seen = set()
            for t in self._tokenize(doc):
                if t not in seen:
                    doc_freq[t] = doc_freq.get(t, 0) + 1
                    seen.add(t)
                vec[t] = vec.get(t, 0) + 1
            doc_vectors.append(vec)

        # 查询向量
        q_vec = self._tfidf_vector(query, doc_freq, num_docs)

        # 计算每个文档的余弦相似度
        scores = []
        for i, d_vec in enumerate(doc_vectors):
            # 部门过滤
            if where and self.metadatas[i].get("department") != where.get("department"):
                continue
            sim = self._cosine(q_vec, d_vec)
            scores.append((sim, i))

        scores.sort(reverse=True, key=lambda x: x[0])

        top = scores[:n_results]
        return {
            "documents": [[self.documents[i] for _, i in top]],
            "metadatas": [[self.metadatas[i] for _, i in top]],
            "distances": [[round(1 - s, 4) for s, _ in top]],
            "ids": [[str(i) for _, i in top]],
        }


# ─── 统一接口 ───
if CHROMA_AVAILABLE:
    _chroma_client = chromadb.PersistentClient(path="./chroma_db")
    _collection = _chroma_client.get_or_create_collection(name=COLLECTION_NAME)
else:
    _collection = FallbackRetriever()
    print("[retriever] ChromaDB 不可用，使用内置 TF-IDF 检索器")


def load_and_index(file_paths: dict[str, str], force_rebuild: bool = False):
    """加载文档并建立索引"""
    existing = _collection.get()

    if CHROMA_AVAILABLE:
        if existing["ids"] and not force_rebuild:
            return len(existing["ids"])
        if existing["ids"]:
            _collection.delete(ids=existing["ids"])
    else:
        if existing["documents"] and not force_rebuild:
            return len(existing["documents"])

    all_docs = []
    all_ids = []
    all_metadatas = []

    for dept, path in file_paths.items():
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            continue

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

    _collection.add(documents=all_docs, ids=all_ids, metadatas=all_metadatas)
    return len(all_docs)


def search(query: str, top_n: int = 3, department: str = None) -> list[dict]:
    """语义检索（ChromaDB 或 TF-IDF 降级）"""
    where_filter = None
    if department:
        where_filter = {"department": department}

    results = _collection.query(
        query_texts=[query],
        n_results=top_n,
        where=where_filter,
    )

    docs = []
    if results.get("documents") and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results.get("metadatas") else {}
            distance = results["distances"][0][i] if results.get("distances") else 0
            score = max(0, 1 - distance / 2)
            docs.append({
                "content": doc,
                "department": meta.get("department", ""),
                "source": meta.get("source", ""),
                "score": round(score, 4),
            })
    return docs


def hybrid_search(query: str, top_n: int = 3, department: str = None) -> list[dict]:
    """混合检索：语义搜索 + 关键词兜底"""
    results = search(query, top_n, department)
    if len(results) >= top_n:
        return results[:top_n]

    # 关键词兜底
    all_data = _collection.get()
    all_docs = all_data.get("documents", [])
    all_meta = all_data.get("metadatas", [])
    keywords = set(re.sub(r'[，。；：！？\s]+', ' ', query).split())

    kw_results = []
    for i, doc in enumerate(all_docs):
        if any(r["content"] == doc for r in results):
            continue
        if department and all_meta[i].get("department") != department:
            continue
        score = sum(1 for kw in keywords if kw in doc)
        if score > 0:
            kw_results.append({
                "content": doc,
                "department": all_meta[i].get("department", ""),
                "source": all_meta[i].get("source", ""),
                "score": min(score / max(len(keywords), 1), 0.5),
            })

    kw_results.sort(key=lambda x: x["score"], reverse=True)
    results += kw_results
    return results[:top_n]


def get_stats() -> dict:
    """返回索引统计信息"""
    existing = _collection.get()
    dept_counts = {}
    if existing.get("metadatas"):
        for meta in existing["metadatas"]:
            dept = meta.get("department", "unknown")
            dept_counts[dept] = dept_counts.get(dept, 0) + 1

    total = len(existing.get("ids", existing.get("documents", [])))
    return {
        "total_chunks": total,
        "by_department": dept_counts,
        "engine": "ChromaDB" if CHROMA_AVAILABLE else "TF-IDF",
    }
