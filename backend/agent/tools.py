"""
Agent 工具注册系统

提供统一的工具注册机制，支持 OpenAI function calling 格式。
每个工具包含：
- name: 工具名称
- description: 工具描述（LLM 据此决定是否调用）
- schema: OpenAI function calling 参数 schema
- func: 实际执行函数（async）
"""

import json
import logging
import math
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable, Optional

logger = logging.getLogger(__name__)


@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    func: Callable[..., Awaitable[Any]]
    schema: dict

    def to_openai_schema(self) -> dict:
        """转换为 OpenAI function calling 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.schema
            }
        }


# 全局工具注册表
TOOL_REGISTRY: dict[str, Tool] = {}

# Agent 配置存储（由 engine 设置）
_agent_config: dict = {}


def set_agent_config(config: dict) -> None:
    """设置 Agent 配置（embedding、rag_service 等）"""
    global _agent_config
    _agent_config = config


def get_agent_config() -> dict:
    """获取 Agent 配置"""
    return _agent_config


# ============ 工具注册装饰器 ============


def register_tool(
    name: str,
    description: str,
    param_schema: dict
) -> Callable:
    """
    工具注册装饰器

    Args:
        name: 工具名称（必须唯一）
        description: 工具描述（LLM 据此决定是否调用）
        param_schema: JSON Schema 格式的参数定义

    Example:
        @register_tool(
            name="search",
            description="搜索知识库",
            param_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索query"}
                },
                "required": ["query"]
            }
        )
        async def search(query: str) -> dict:
            ...
    """
    def decorator(func: Callable) -> Callable:
        TOOL_REGISTRY[name] = Tool(
            name=name,
            description=description,
            func=func,
            schema=param_schema
        )
        return func
    return decorator


# ============ 内置工具 ============


@register_tool(
    name="search_knowledge_base",
    description="搜索知识库，返回与问题相关的文档内容。如果没有相关信息，返回空结果时请如实说明。",
    param_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索 query，使用与原问题相关的关键词"
            }
        },
        "required": ["query"]
    }
)
async def search_knowledge_base(query: str) -> dict:
    """
    搜索知识库

    复用现有的 rag_qdrant.py RAG 检索能力
    """
    config = get_agent_config()
    rag_service = config.get("rag_service")
    agent_id = config.get("agent_id")
    top_k = config.get("top_k", 5)
    threshold = config.get("threshold", 0.5)
    qa_items = config.get("qa_items", [])

    if not rag_service or not agent_id:
        return {"success": False, "error": "知识库未配置", "results": []}

    try:
        results = await rag_service.retrieve_async(
            agent_id=agent_id,
            query=query,
            top_k=top_k,
            threshold=threshold,
            qa_items=qa_items
        )

        # 格式化结果供 LLM 使用
        formatted = []
        for i, r in enumerate(results, 1):
            if r["type"] == "url":
                formatted.append(
                    f"[Source {i}] {r['metadata'].get('title', '文档')}\n"
                    f"URL: {r['metadata'].get('url', '')}\n"
                    f"内容: {r['content'][:300]}..."
                )
            elif r["type"] == "qa":
                formatted.append(
                    f"[Source {i}] Q: {r['metadata'].get('question', '')}\n"
                    f"A: {r['content']}"
                )

        return {
            "success": True,
            "count": len(results),
            "results": formatted,
            "raw_results": results
        }
    except Exception as e:
        logger.warning(f"知识库搜索失败: {e}")
        return {"success": False, "error": str(e), "results": []}


@register_tool(
    name="calculate",
    description="执行数学计算。当用户询问需要计算的问题时使用，如价格计算、百分比、统计等。",
    param_schema={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "数学表达式，如 '2+3*4' 或 '100 * 0.8'"
            }
        },
        "required": ["expression"]
    }
)
async def calculate(expression: str) -> dict:
    """
    安全数学计算

    只允许基本的数学运算，防止代码注入
    """
    try:
        # 清理表达式，只保留数字、运算符和小数点
        cleaned = re.sub(r'[^0-9+\-*/().% ]', '', expression)

        # 安全评估（只用数学运算）
        allowed_names = {
            "__builtins__": {},
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "math": math,
        }

        result = eval(cleaned, allowed_names, {})

        # 格式化结果
        if isinstance(result, float) and result.is_integer():
            result = int(result)

        return {
            "success": True,
            "expression": expression,
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "expression": expression,
            "error": f"计算错误: {str(e)}"
        }


@register_tool(
    name="get_date",
    description="获取当前日期信息。当用户询问今天是几号、星期几、日期计算等问题时使用。",
    param_schema={
        "type": "object",
        "properties": {
            "format": {
                "type": "string",
                "description": "日期格式，如 '%Y-%m-%d'、'%Y年%m月%d日' 等",
                "default": "%Y-%m-%d"
            }
        },
        "required": []
    }
)
async def get_date(format: str = "%Y-%m-%d") -> dict:
    """获取当前日期"""
    from datetime import datetime
    now = datetime.now()
    return {
        "success": True,
        "date": now.strftime(format),
        "weekday": now.strftime("%A"),
        "weekday_cn": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()]
    }


# ============ 工具管理函数 ============


def list_tools() -> list[str]:
    """列出所有已注册的工具名称"""
    return list(TOOL_REGISTRY.keys())


def get_tool_schema() -> list[dict]:
    """获取所有工具的 OpenAI schema"""
    return [tool.to_openai_schema() for tool in TOOL_REGISTRY.values()]


def get_tool(name: str) -> Optional[Tool]:
    """根据名称获取工具"""
    return TOOL_REGISTRY.get(name)


async def execute_tool(name: str, args: dict) -> Any:
    """
    执行工具

    Args:
        name: 工具名称
        args: 工具参数

    Returns:
        工具执行结果（JSON 序列化后的字符串）
    """
    tool = TOOL_REGISTRY.get(name)
    if not tool:
        return json.dumps({"success": False, "error": f"未知工具: {name}"})

    try:
        result = await tool.func(**args)
        return json.dumps(result, ensure_ascii=False)
    except TypeError as e:
        # 参数不匹配
        logger.warning(f"工具 {name} 参数错误: {e}")
        return json.dumps({
            "success": False,
            "error": f"参数错误: {str(e)}",
            "expected_params": list(TOOL_REGISTRY[name].schema.get("properties", {}).keys())
        })
    except Exception as e:
        logger.error(f"工具 {name} 执行失败: {e}")
        return json.dumps({"success": False, "error": str(e)})
