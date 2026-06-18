"""
MCP (Model Context Protocol) 工具连接器
给你的 Agent 提供标准化的外部工具接入能力

对应 JD 常见要求：「熟悉 MCP 协议」「有 MCP Server 开发经验」
"""
import json
from typing import Any, Callable


class MCPServer:
    """简易 MCP Server：注册工具 → 暴露 JSON-RPC 接口"""

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self._tools: dict[str, dict] = {}

    def register_tool(
        self,
        name: str,
        handler: Callable,
        description: str,
        parameters: dict[str, dict] = None,
    ):
        """注册一个工具"""
        self._tools[name] = {
            "handler": handler,
            "definition": {
                "name": name,
                "description": description,
                "inputSchema": {
                    "type": "object",
                    "properties": parameters or {},
                    "required": list(parameters.keys()) if parameters else [],
                },
            },
        }
        return self

    def list_tools(self) -> list[dict]:
        """返回所有已注册工具的定义（MCP tools/list）"""
        return [t["definition"] for t in self._tools.values()]

    def call_tool(self, name: str, arguments: dict) -> dict:
        """调用工具（MCP tools/call）"""
        if name not in self._tools:
            return {"error": f"工具 {name} 不存在"}
        try:
            result = self._tools[name]["handler"](**arguments)
            return {"content": [{"type": "text", "text": str(result)}]}
        except Exception as e:
            return {"error": str(e)}

    def handle_request(self, method: str, params: dict = None) -> dict:
        """处理 MCP JSON-RPC 请求"""
        params = params or {}
        if method == "tools/list":
            return {"tools": self.list_tools()}
        elif method == "tools/call":
            return self.call_tool(params.get("name", ""), params.get("arguments", {}))
        else:
            return {"error": f"未知方法: {method}"}


# ─── 示例：创建知识库 MCP Server ───
def create_kb_mcp_server():
    """创建知识库的 MCP Server，可被外部 Agent 连接"""
    from retriever import hybrid_search

    server = MCPServer(name="knowledge-base", version="1.0.0")

    server.register_tool(
        name="search_knowledge",
        handler=lambda query, department="IT": json.dumps(
            [{"content": r["content"][:200], "score": r["score"]}
             for r in hybrid_search(query, department=department)],
            ensure_ascii=False,
        ),
        description="从企业知识库中语义搜索相关内容",
        parameters={
            "query": {"type": "string", "description": "搜索查询"},
            "department": {"type": "string", "description": "部门: IT/HR/行政/客服/销售"},
        },
    )

    server.register_tool(
        name="get_departments",
        handler=lambda: json.dumps(["IT", "HR", "行政", "客服", "销售"]),
        description="获取所有可用的部门列表",
    )

    return server


# ─── 测试 ───
if __name__ == "__main__":
    server = create_kb_mcp_server()

    # 模拟 MCP 客户端调用
    print("=== MCP tools/list ===")
    print(json.dumps(server.handle_request("tools/list"), indent=2, ensure_ascii=False))

    print("\n=== MCP tools/call ===")
    result = server.handle_request("tools/call", {
        "name": "search_knowledge",
        "arguments": {"query": "打印机故障", "department": "IT"},
    })
    print(json.dumps(result, indent=2, ensure_ascii=False))
