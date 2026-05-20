"""
简历模型
"""
from sqlalchemy import String, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, TimestampMixin
import uuid


class Resume(Base, TimestampMixin):
    """简历"""
    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), comment="简历名称")
    original_file_path: Mapped[str] = mapped_column(String(500), comment="原始文件路径")

    # 解析后的结构化数据
    parsed_content: Mapped[dict | None] = mapped_column(JSON, comment="解析后的内容结构")
    skills: Mapped[list | None] = mapped_column(JSON, comment="技能标签")
    experience_years: Mapped[int | None] = mapped_column(Integer, comment="工作年限")
    education: Mapped[dict | None] = mapped_column(JSON, comment="教育经历")
    work_experience: Mapped[list | None] = mapped_column(JSON, comment="工作经历")
    projects: Mapped[list | None] = mapped_column(JSON, comment="项目经历")

    # 解析状态
    is_parsed: Mapped[bool] = mapped_column(default=False, comment="是否已解析")

    # 关系
    optimizations: Mapped[list["Optimization"]] = relationship(
        back_populates="resume", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Resume(id={self.id}, name={self.name})>"
