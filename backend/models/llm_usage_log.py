"""
LLM 调用日志模型
"""
from sqlalchemy import String, Text, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base, TimestampMixin
import uuid


class LLMUsageLog(Base, TimestampMixin):
    """LLM 调用日志"""
    __tablename__ = "llm_usage_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # 功能标识
    feature: Mapped[str] = mapped_column(
        String(50), comment="功能：智能解析/职业画像/JD解析/简历优化/面试攻略"
    )
    related_id: Mapped[str | None] = mapped_column(String(36), comment="关联业务 ID")
    related_type: Mapped[str | None] = mapped_column(
        String(30), comment="关联类型：resume/jd/optimization/interview"
    )

    # LLM 信息
    llm_provider: Mapped[str] = mapped_column(String(50), comment="LLM 提供商")
    llm_model: Mapped[str] = mapped_column(String(100), comment="模型名称")

    # Prompt 内容
    system_prompt: Mapped[str | None] = mapped_column(Text, comment="完整 system prompt")
    user_prompt: Mapped[str | None] = mapped_column(Text, comment="完整 user prompt")

    # 返回结果
    raw_response: Mapped[str | None] = mapped_column(Text, comment="LLM 原始返回")
    parsed_result: Mapped[dict | None] = mapped_column(JSON, comment="解析后的结构化结果")

    # Token 用量
    input_tokens: Mapped[int | None] = mapped_column(Integer, comment="输入 token 数")
    output_tokens: Mapped[int | None] = mapped_column(Integer, comment="输出 token 数")
    total_tokens: Mapped[int | None] = mapped_column(Integer, comment="总 token 数")

    # 调用信息
    duration_ms: Mapped[int | None] = mapped_column(Integer, comment="调用耗时（毫秒）")
    status: Mapped[str] = mapped_column(
        String(20), default="success", comment="状态：success/failed/timeout"
    )
    error_message: Mapped[str | None] = mapped_column(Text, comment="失败原因")
    retry_count: Mapped[int] = mapped_column(Integer, default=0, comment="重试次数")

    def __repr__(self):
        return f"<LLMUsageLog(id={self.id}, feature={self.feature}, status={self.status})>"
