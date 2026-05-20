"""
面试攻略模型
"""
from sqlalchemy import String, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, TimestampMixin
import uuid


class InterviewGuide(Base, TimestampMixin):
    """面试攻略"""
    __tablename__ = "interview_guides"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    optimization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("optimizations.id"), comment="优化任务 ID"
    )

    # 面试攻略内容
    knowledge_points: Mapped[list | None] = mapped_column(JSON, comment="知识点清单")
    high_frequency_questions: Mapped[list | None] = mapped_column(JSON, comment="高频面试题")
    answer_templates: Mapped[list | None] = mapped_column(JSON, comment="答题模板")
    preparation_strategy: Mapped[dict | None] = mapped_column(JSON, comment="准备策略")
    company_research: Mapped[dict | None] = mapped_column(JSON, comment="公司调研建议")

    # 导出文件
    export_docx_path: Mapped[str | None] = mapped_column(
        String(500), comment="导出的攻略文档路径"
    )

    # 关系
    optimization: Mapped["Optimization"] = relationship(back_populates="interview_guide")

    def __repr__(self):
        return f"<InterviewGuide(id={self.id})>"
