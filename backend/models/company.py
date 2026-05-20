"""
公司模型
"""
from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, TimestampMixin
import uuid


class Company(Base, TimestampMixin):
    """公司信息"""
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), comment="公司名称")
    industry: Mapped[str | None] = mapped_column(String(100), comment="行业")
    size: Mapped[str | None] = mapped_column(String(50), comment="公司规模")
    culture_keywords: Mapped[dict | None] = mapped_column(JSON, comment="文化关键词")
    website: Mapped[str | None] = mapped_column(String(500), comment="公司官网")
    notes: Mapped[str | None] = mapped_column(String(1000), comment="备注")

    # 关系
    jds: Mapped[list["JobDescription"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Company(id={self.id}, name={self.name})>"
