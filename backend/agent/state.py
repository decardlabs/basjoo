"""Agent 状态管理模块"""

from dataclasses import dataclass, field
from typing import Literal, Optional, List, Any


@dataclass
class Message:
    """对话消息"""
    role: Literal["user", "assistant", "tool"]
    content: str
    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None


@dataclass
class ToolResult:
    """工具执行结果"""
    tool_name: str
    result: Any
    success: bool = True
    error: Optional[str] = None


@dataclass
class AgentState:
    """
    Agent 运行状态

    Attributes:
        messages: 对话历史
        context: 中间结果，供工具使用
        step_count: 当前循环轮次
        max_steps: 最大循环轮次
        final_answer: 最终答案（循环结束后）
        retrieval_results: RAG 检索结果（可选）
        system_prompt: 系统提示词
    """
    messages: List[Message] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    step_count: int = 0
    max_steps: int = 5
    final_answer: Optional[str] = None
    retrieval_results: List[dict] = field(default_factory=list)
    system_prompt: str = "You are a helpful AI assistant."

    def is_halted(self) -> bool:
        """检查是否应该停止循环"""
        return self.step_count >= self.max_steps

    def add_user_message(self, content: str) -> None:
        """添加用户消息"""
        self.messages.append(Message(role="user", content=content))

    def add_assistant_message(self, content: str) -> None:
        """添加助手消息"""
        self.messages.append(Message(role="assistant", content=content))

    def add_tool_result(self, tool_name: str, content: str) -> None:
        """添加工具结果"""
        self.messages.append(Message(role="tool", content=content, tool_name=tool_name))

    def get_recent_messages(self, n: int = 10) -> List[Message]:
        """获取最近 n 条消息"""
        return self.messages[-n:] if self.messages else []

    def to_dict_list(self) -> List[dict]:
        """转换为 API 格式"""
        return [
            {"role": m.role, "content": m.content}
            for m in self.messages
        ]
