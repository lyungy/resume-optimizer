"""
JD 相关 Schema
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class JDCreate(BaseModel):
    """创建 JD"""
    company_id: str = Field(..., description="公司 ID")
    title: str = Field(..., min_length=1, max_length=200, description="职位名称")
    raw_text: str = Field(..., min_length=10, description="JD 原始文本")
    source_url: str | None = Field(None, max_length=500, description="来源链接")


class JDUpdate(BaseModel):
    """更新 JD"""
    title: str | None = Field(None, min_length=1, max_length=200)
    raw_text: str | None = Field(None, min_length=10)
    source_url: str | None = Field(None, max_length=500)


class JDParseResult(BaseModel):
    """JD 解析结果"""
    hard_skills: list[str] = []
    soft_skills: list[str] = []
    experience_years: str | None = None
    hidden_requirements: list[str] = []
    company_culture: str | None = None
    key_keywords: list[str] = []
    difficulty_level: str | None = None
    senior_friendly: bool | None = None
    senior_friendly_signals: list[str] = []
    concern_signals: list[str] = []


class JDResponse(BaseModel):
    """JD 响应"""
    id: str
    company_id: str
    company_name: str | None = None
    title: str
    raw_text: str
    source_url: str | None = None
    is_parsed: bool = False
    parsed_requirements: dict | None = None
    hard_skills: Optional[list[str]] = None
    soft_skills: Optional[list[str]] = None
    hidden_requirements: Optional[list[str]] = None
    experience_years: str | None = None
    difficulty_level: str | None = None
    senior_friendly: bool | None = None
    senior_friendly_signals: Optional[list[str]] = None
    concern_signals: Optional[list[str]] = None
    key_keywords: Optional[list[str]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JDListResponse(BaseModel):
    """JD 列表响应"""
    items: list[JDResponse]
    total: int
    page: int
    page_size: int


class JDBatchImportItem(BaseModel):
    """批量导入 JD 单项"""
    title: str = Field(..., min_length=1, max_length=200, description="职位名称")
    company_name: str = Field(..., min_length=1, max_length=200, description="公司名称")
    raw_text: str = Field(..., min_length=10, description="JD 原始文本")
    source_url: str | None = Field(None, max_length=500, description="来源链接")
    industry: str | None = Field(None, max_length=100, description="行业")


class JDBatchImportRequest(BaseModel):
    """批量导入 JD 请求"""
    items: list[JDBatchImportItem] = Field(..., min_length=1, description="JD 列表")


class JDBatchImportResponse(BaseModel):
    """批量导入 JD 响应"""
    total: int
    success: int
    failed: int
    errors: list[str] = []
    imported_ids: list[str] = []
