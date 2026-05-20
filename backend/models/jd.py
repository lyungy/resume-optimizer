"""
职位描述(JD)模型
"""
from sqlalchemy import String, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, TimestampMixin
import uuid


class JobDescription(Base, TimestampMixin):
    """职位描述"""
    __tablename__ = "job_descriptions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id"), comment="公司ID"
    )
    title: Mapped[str] = mapped_column(String(200), comment="职位名称")
    raw_text: Mapped[str] = mapped_column(Text, comment="原始JD文本")
    source_url: Mapped[str | None] = mapped_column(String(500), comment="来源链接")

    # 解析后的结构化数据
    parsed_requirements: Mapped[dict | None] = mapped_column(JSON, comment="解析后的结构化要求")
    hard_skills: Mapped[list | None] = mapped_column(JSON, comment="硬性技能要求")
    soft_skills: Mapped[list | None] = mapped_column(JSON, comment="软性技能要求")
    hidden_requirements: Mapped[list | None] = mapped_column(JSON, comment="隐性需求推断")
    experience_years: Mapped[str | None] = mapped_column(String(50), comment="工作年限要求")
    difficulty_level: Mapped[str | None] = mapped_column(
        String(20), comment="难度级别: junior/mid/senior"
    )
    senior_friendly: Mapped[bool | None] = mapped_column(comment="是否对大龄友好")
    senior_friendly_signals: Mapped[list | None] = mapped_column(JSON, comment="大龄友好信号")
    concern_signals: Mapped[list | None] = mapped_column(JSON, comment="潜在风险信号")
    key_keywords: Mapped[list | None] = mapped_column(JSON, comment="ATS关键词")

    # 解析状态
    is_parsed: Mapped[bool] = mapped_column(default=False, comment="是否已解析")

    # 关系
    company: Mapped["Company"] = relationship(back_populates="jds")
    optimizations: Mapped[list["Optimization"]] = relationship(
        back_populates="jd", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<JobDescription(id={self.id}, title={self.title})>"
