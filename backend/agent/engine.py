"""
Agent 引擎核心模块

实现 ReAct (Reason + Act) 模式的最小化 Agent：
- 推理节点：LLM 判断是否需要工具调用
- 工具节点：执行注册的外部工具
- 循环控制：防止无限循环

特点：
- 无任何框架依赖
- 完全可控可调试
- 与现有 llm_service.py 无缝集成
"""

import json
import logging
from typing import Optional, List, Dict, Any

from .state import AgentState, Message
from .tools import (
    TOOL_REGISTRY,
    set_agent_config,
    get_tool_schema,
    execute_tool,
    list_tools
)

logger = logging.getLogger(__name__)


class AgentEngine:
    """
    Agent 推理引擎

    支持循环推理和工具调用，核心流程：
    1. 推理（Reason）：让 LLM 判断是直接回答还是调用工具
    2. 执行（Act）：如果需要工具，执行工具并获取结果
    3. 循环：重复直到 LLM 给出最终回答或达到最大轮次

    Attributes:
        max_steps: 最大推理轮次，默认 5
        model: 使用的模型（从 agent 配置获取）
    """

    def __init__(
        self,
        llm_service,
        system_prompt: Optional[str] = None,
        max_steps: int = 5
    ):
        """
        初始化 Agent 引擎

        Args:
            llm_service: LLM 服务实例（BaseLLMService）
            system_prompt: 系统提示词
            max_steps: 最大推理轮次
        """
        self.llm = llm_service
        self.system_prompt = system_prompt or "You are a helpful AI assistant."
        self.max_steps = max_steps

    def configure(self, config: dict) -> None:
        """
        配置 Agent（工具、RAG 服务等）

        Args:
            config: 配置字典，包含：
                - agent_id: Agent ID
                - rag_service: RAG 服务实例
                - top_k: 检索数量
                - threshold: 相似度阈值
                - qa_items: Q&A 列表
        """
        set_agent_config(config)

    async def run(self, user_input: str) -> str:
        """
        运行 Agent

        Args:
            user_input: 用户输入

        Returns:
            Agent 最终回答
        """
        state = AgentState(
            system_prompt=self.system_prompt,
            max_steps=self.max_steps
        )
        state.add_user_message(user_input)

        while not state.is_halted():
            state.step_count += 1
            logger.info(f"Agent 推理轮次: {state.step_count}/{state.max_steps}")

            # 步骤 1：推理（Reason）
            decision = await self._reason(state)

            if decision["type"] == "final":
                # 直接回答
                state.final_answer = decision["content"]
                break

            if decision["type"] == "tool_call":
                # 步骤 2：执行工具（Act）
                tool_name = decision["tool_name"]
                tool_args = decision["tool_args"]

                logger.info(f"执行工具: {tool_name}, 参数: {tool_args}")

                tool_result = await self._act(tool_name, tool_args)

                # 步骤 3：添加工具结果到上下文
                state.add_tool_result(tool_name, tool_result)
                continue

            if decision["type"] == "error":
                # LLM 返回格式错误，尝试直接回答
                state.final_answer = decision.get("content", user_input)
                break

        if state.final_answer is None:
            state.final_answer = "抱歉，我需要更多信息来回答您的问题。"

        return state.final_answer

    async def run_with_context(
        self,
        user_input: str,
        retrieval_results: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        带上下文的 Agent 运行

        Args:
            user_input: 用户输入
            retrieval_results: RAG 检索结果
            conversation_history: 对话历史

        Returns:
            Agent 最终回答
        """
        state = AgentState(
            system_prompt=self.system_prompt,
            max_steps=self.max_steps
        )
        state.retrieval_results = retrieval_results
        state.add_user_message(user_input)

        # 如果有对话历史，转换为 Message 对象
        if conversation_history:
            for msg in conversation_history:
                if msg.get("role") == "assistant":
                    state.add_assistant_message(msg.get("content", ""))
                elif msg.get("role") == "user":
                    state.add_user_message(msg.get("content", ""))

        while not state.is_halted():
            state.step_count += 1
            logger.info(f"Agent 推理轮次: {state.step_count}/{state.max_steps}")

            # 推理
            decision = await self._reason(state)

            if decision["type"] == "final":
                state.final_answer = decision["content"]
                break

            if decision["type"] == "tool_call":
                tool_name = decision["tool_name"]
                tool_args = decision["tool_args"]

                logger.info(f"执行工具: {tool_name}")

                tool_result = await self._act(tool_name, tool_args)
                state.add_tool_result(tool_name, tool_result)
                continue

            if decision["type"] == "error":
                state.final_answer = decision.get("content", user_input)
                break

        return state.final_answer or "抱歉，我无法回答您的问题。"

    async def _reason(self, state: AgentState) -> dict:
        """
        推理节点：让 LLM 判断是直接回答还是调用工具

        Args:
            state: Agent 状态

        Returns:
            决策结果：
            - {"type": "final", "content": "回答内容"}
            - {"type": "tool_call", "tool_name": "工具名", "tool_args": {...}}
            - {"type": "error", "content": "错误信息"}
        """
        # 构建系统提示词
        tools_desc = ", ".join(list_tools()) if TOOL_REGISTRY else "无"

        system = state.system_prompt + f"""

## 工具说明
可用工具：{list_tools()}

**重要规则**：
- 如果用户问题需要查询知识库，必须使用 `search_knowledge_base` 工具
- 如果问题涉及计算，使用 `calculate` 工具
- 只需要调用 1 个工具，不要一次调用多个
- 如果问题可以直接回答，不需要调用工具

## 输出格式
请返回以下 JSON 格式之一：
1. 直接回答：{{"type": "final", "content": "你的回答内容"}}
2. 调用工具：{{"type": "tool_call", "tool_name": "工具名", "tool_args": {{"参数名": "参数值"}}}}
"""

        # 如果有检索结果，添加到系统提示词
        if state.retrieval_results:
            context_parts = []
            for i, r in enumerate(state.retrieval_results[:3], 1):
                if r["type"] == "url":
                    context_parts.append(
                        f"[Source {i}] {r['metadata'].get('title', '文档')}\n"
                        f"URL: {r['metadata'].get('url', '')}\n"
                        f"内容: {r['content'][:300]}..."
                    )
                elif r["type"] == "qa":
                    context_parts.append(
                        f"[Source {i}] Q: {r['metadata'].get('question', '')}\n"
                        f"A: {r['content']}"
                    )

            if context_parts:
                system += f"\n\n## 知识库检索结果\n" + "\n\n".join(context_parts)
                system += "\n\n**请基于以上检索结果回答。如果检索结果与问题无关或不足，请说明。**"

        # 构建消息历史（最近 8 条，防止 token 爆炸）
        history = [{"role": "system", "content": system}]
        recent = state.messages[-8:]
        for msg in recent:
            history.append({"role": msg.role, "content": msg.content})

        # 调用 LLM
        try:
            chunks = []
            async for chunk in self.llm.chat_completion(
                messages=history,
                stream=True,
                temperature=0.7,
                max_tokens=2000
            ):
                chunks.append(chunk)

            response_text = "".join(chunks)

            # 尝试解析 JSON
            return self._parse_llm_response(response_text)

        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            return {
                "type": "error",
                "content": f"抱歉，服务暂时不可用。错误: {str(e)}"
            }

    def _parse_llm_response(self, text: str) -> dict:
        """
        解析 LLM 响应

        支持多种格式：
        1. 纯 JSON
        2. Markdown 代码块包裹的 JSON
        3. 混杂在普通文本中的 JSON
        """
        text = text.strip()

        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试从 Markdown 代码块中提取
        code_block_patterns = [
            r'```(?:json)?\s*(\{.*?\})\s*```',
            r'```(\{.*?\})```',
        ]
        for pattern in code_block_patterns:
            match = _find_json_in_text(text, pattern)
            if match:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    pass

        # 尝试提取任何 {...} 块
        match = _find_json_in_text(text, r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}')
        if match:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                pass

        # 无法解析，返回原始文本作为最终回答
        logger.warning(f"无法解析 LLM 响应格式，返回原始文本")
        return {"type": "final", "content": text}

    async def _act(self, tool_name: str, tool_args: dict) -> str:
        """
        执行工具

        Args:
            tool_name: 工具名称
            tool_args: 工具参数

        Returns:
            工具执行结果（字符串）
        """
        if tool_name not in TOOL_REGISTRY:
            return json.dumps({
                "success": False,
                "error": f"未知工具: {tool_name}"
            })

        result = await execute_tool(tool_name, tool_args)
        return result


def _find_json_in_text(text: str, pattern: str) -> str:
    """从文本中提取匹配模式的 JSON"""
    import re
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1)
    return ""


# ============ 便捷函数 ============


async def run_agent(
    llm_service,
    user_input: str,
    config: dict,
    system_prompt: Optional[str] = None,
    retrieval_results: Optional[List[Dict[str, Any]]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    max_steps: int = 5
) -> str:
    """
    运行 Agent 的便捷函数

    Args:
        llm_service: LLM 服务实例
        user_input: 用户输入
        config: Agent 配置（rag_service、agent_id 等）
        system_prompt: 系统提示词
        retrieval_results: RAG 检索结果
        conversation_history: 对话历史
        max_steps: 最大推理轮次

    Returns:
        Agent 最终回答
    """
    agent = AgentEngine(
        llm_service=llm_service,
        system_prompt=system_prompt,
        max_steps=max_steps
    )
    agent.configure(config)

    if retrieval_results is not None:
        return await agent.run_with_context(
            user_input=user_input,
            retrieval_results=retrieval_results,
            conversation_history=conversation_history
        )
    else:
        return await agent.run(user_input)
