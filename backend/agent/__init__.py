"""
Agent 引擎模块

提供轻量级的 Agent 推理能力，支持：
- 循环推理（Reason → Act → Evaluate）
- 工具调用（知识库检索、数学计算等）
- 与现有 llm_service.py 无缝集成

核心组件：
- state: Agent 状态管理
- tools: 工具注册系统
- engine: Agent 推理引擎

使用示例：
```python
from agent import run_agent

# 配置 Agent
config = {
    "agent_id": "agt_xxx",
    "rag_service": rag_service,
    "top_k": 5,
    "threshold": 0.5,
    "qa_items": []
}

# 运行 Agent
answer = await run_agent(
    llm_service=llm,
    user_input="用户问题",
    config=config,
    system_prompt="你是一个客服助手",
    retrieval_results=retrieval_results
)
```
"""

from .state import AgentState, Message, ToolResult
from .tools import (
    Tool,
    register_tool,
    TOOL_REGISTRY,
    set_agent_config,
    get_agent_config,
    list_tools,
    get_tool_schema,
    get_tool,
    execute_tool,
)
from .engine import AgentEngine, run_agent

__all__ = [
    # 状态管理
    "AgentState",
    "Message",
    "ToolResult",
    # 工具
    "Tool",
    "register_tool",
    "TOOL_REGISTRY",
    "set_agent_config",
    "get_agent_config",
    "list_tools",
    "get_tool_schema",
    "get_tool",
    "execute_tool",
    # 引擎
    "AgentEngine",
    "run_agent",
]
