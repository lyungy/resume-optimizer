"""
简历版本模型
"""
from sqlalchemy import String, JSON, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, TimestampMixin
import uuid


class ResumeVersion(Base, TimestampMixin):
    """简历版本快照"""
    __tablename__ = "resume_versions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    resume_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("resumes.id"), comment="简历 ID"
    )
    version_no: Mapped[int] = mapped_column(Integer, comment="版本号")
    label: Mapped[str | None] = mapped_column(String(100), comment="版本标签（如：智能解析、职业画像）")

    # 快照数据
    skills: Mapped[list | None] = mapped_column(JSON, comment="技能标签快照")
    experience_years: Mapped[int | None] = mapped_column(Integer, comment="工作年限快照")
    education: Mapped[dict | None] = mapped_column(JSON, comment="教育经历快照")
    work_experience: Mapped[list | None] = mapped_column(JSON, comment="工作经历快照")
    projects: Mapped[list | None] = mapped_column(JSON, comment="项目经历快照")
    profile: Mapped[dict | None] = mapped_column(JSON, comment="求职画像快照")
    recommended_positions: Mapped[list | None] = mapped_column(JSON, comment="推荐岗位快照")
    parsed_content: Mapped[dict | None] = mapped_column(JSON, comment="解析内容快照")

    # 关系
    resume: Mapped["Resume"] = relationship(back_populates="versions")

    def __repr__(self):
        return f"<ResumeVersion(id={self.id}, resume_id={self.resume_id}, v{self.version_no})>"
