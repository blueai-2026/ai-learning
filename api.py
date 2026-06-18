"""
企业知识库 FastAPI 后端服务
为前端提供 RESTful API，支持向量检索 + LLM 问答 + Redis 缓存
"""
import os
import hashlib
import json
import time
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field
from openai import OpenAI

from retriever import load_and_index, hybrid_search, get_stats

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

# ─── Redis 缓存（可选，没有 Redis 则跳过） ───
REDIS_AVAILABLE = False
_redis = None
try:
    import redis
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
    _redis = redis.from_url(REDIS_URL)
    _redis.ping()
    REDIS_AVAILABLE = True
except Exception:
    pass


def cache_get(key: str) -> Optional[str]:
    if REDIS_AVAILABLE and _redis:
        return _redis.get(key)
    return None


def cache_set(key: str, value: str, ttl: int = 3600):
    if REDIS_AVAILABLE and _redis:
        _redis.setex(key, ttl, value)


# ─── 启动时加载向量库 ───
DOCS = {
    "IT": "docs/故障案例.txt",
    "HR": "docs/hr.txt",
    "行政": "docs/admin.txt",
    "客服": "docs/service.txt",
    "销售": "docs/sales.txt",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时初始化向量库"""
    count = load_and_index(DOCS)
    print(f"[启动] 向量库就绪：{count} 个片段")
    yield


app = FastAPI(
    title="企业智能知识库 API",
    description="基于 RAG + ChromaDB 的多部门知识库问答接口",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── 简单认证 ───
security = HTTPBasic()

USERS = {
    "admin": "admin123",
    "it": "it123",
    "hr": "hr123",
}


def verify_user(credentials: HTTPBasicCredentials = Depends(security)):
    pwd = USERS.get(credentials.username)
    if not pwd or pwd != credentials.password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return credentials.username


# ─── 数据模型 ───
class QuestionRequest(BaseModel):
    question: str = Field(..., description="用户问题", min_length=1, max_length=2000)
    department: str = Field(default="IT", description="查询部门: IT/HR/行政/客服/销售")
    top_n: int = Field(default=3, ge=1, le=10, description="返回文档数")


class QuestionResponse(BaseModel):
    answer: str
    sources: list[dict] = []
    cached: bool = False
    response_time_ms: float = 0


class StatsResponse(BaseModel):
    total_chunks: int
    by_department: dict
    redis_available: bool


@app.post("/api/chat", response_model=QuestionResponse, tags=["问答"])
def chat(req: QuestionRequest, username: str = Depends(verify_user)):
    """
    知识库问答接口 —— 语义检索 + LLM 生成

    先查 Redis 缓存，命中则直接返回；未命中则走检索→LLM→缓存流程。
    """
    start = time.time()

    # 1. 缓存检查（相同问题+部门，1小时内复用）
    cache_key = hashlib.md5(f"{req.department}:{req.question}".encode()).hexdigest()
    cached = cache_get(cache_key)
    if cached:
        data = json.loads(cached)
        data["cached"] = True
        data["response_time_ms"] = round((time.time() - start) * 1000, 2)
        return data

    # 2. 向量语义检索
    dept_key = req.department if req.department in DOCS else "IT"
    results = hybrid_search(req.question, top_n=req.top_n, department=dept_key)
    context = "\n\n".join([r["content"] for r in results])

    # 3. LLM 生成
    client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")
    system_prompt = f"你是一个{req.department}部门的智能助手，根据知识库回答问题。用中文简洁回答。"
    messages = [{"role": "system", "content": system_prompt}]
    if context:
        messages.append({
            "role": "system",
            "content": f"知识库相关内容：\n\n{context}"
        })
    messages.append({"role": "user", "content": req.question})

    response = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=2048,
        messages=messages,
    )
    answer = response.choices[0].message.content

    # 4. 构建响应
    sources = [
        {"content": r["content"][:100] + "...", "score": r["score"], "department": r["department"]}
        for r in results
    ]

    elapsed = round((time.time() - start) * 1000, 2)

    data = QuestionResponse(
        answer=answer,
        sources=sources,
        cached=False,
        response_time_ms=elapsed,
    )

    # 5. 写入缓存
    cache_set(cache_key, data.model_dump_json(), ttl=3600)

    return data


@app.get("/api/stats", response_model=StatsResponse, tags=["管理"])
def stats():
    """获取知识库统计信息"""
    s = get_stats()
    return StatsResponse(
        total_chunks=s["total_chunks"],
        by_department=s["by_department"],
        redis_available=REDIS_AVAILABLE,
    )


@app.get("/api/health", tags=["管理"])
def health():
    return {"status": "ok", "version": "2.0.0"}


# ─── 直接启动 ───
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
