"""
优化任务模型
"""
from sqlalchemy import String, JSON, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, TimestampMixin
import uuid


class Optimization(Base, TimestampMixin):
    """简历优化任务"""
    __tablename__ = "optimizations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    jd_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("job_descriptions.id"), comment="JD ID"
    )
    resume_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("resumes.id"), comment="简历 ID"
    )
    llm_provider: Mapped[str] = mapped_column(
        String(50), default="xiaomi-coding", comment="使用的 LLM Provider"
    )
    llm_model: Mapped[str] = mapped_column(
        String(100), default="mimo-v2.5-pro", comment="使用的模型"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending",
        comment="状态: pending/processing/completed/failed"
    )

    # 优化结果
    optimization_result: Mapped[dict | None] = mapped_column(JSON, comment="优化结果")
    match_score: Mapped[float | None] = mapped_column(Float, comment="匹配度评分")
    keyword_coverage: Mapped[dict | None] = mapped_column(JSON, comment="关键词覆盖情况")
    suggestions: Mapped[list | None] = mapped_column(JSON, comment="优化建议")
    ats_tips: Mapped[list | None] = mapped_column(JSON, comment="ATS优化建议")
    optimized_docx_path: Mapped[str | None] = mapped_column(
        String(500), comment="优化后的DOCX路径"
    )

    # 错误信息
    error_message: Mapped[str | None] = mapped_column(String(1000), comment="错误信息")

    # 关系
    jd: Mapped["JobDescription"] = relationship(back_populates="optimizations")
    resume: Mapped["Resume"] = relationship(back_populates="optimizations")
    interview_guide: Mapped["InterviewGuide | None"] = relationship(
        back_populates="optimization", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Optimization(id={self.id}, status={self.status})>"
