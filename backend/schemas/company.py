"""
公司相关 Schema
"""
from pydantic import BaseModel, Field
from datetime import datetime


class CompanyCreate(BaseModel):
    """创建公司"""
    name: str = Field(..., min_length=1, max_length=200, description="公司名称")
    industry: str | None = Field(None, max_length=100, description="行业")
    size: str | None = Field(None, max_length=50, description="公司规模")
    website: str | None = Field(None, max_length=500, description="公司官网")
    notes: str | None = Field(None, max_length=1000, description="备注")


class CompanyUpdate(BaseModel):
    """更新公司"""
    name: str | None = Field(None, min_length=1, max_length=200)
    industry: str | None = Field(None, max_length=100)
    size: str | None = Field(None, max_length=50)
    website: str | None = Field(None, max_length=500)
    notes: str | None = Field(None, max_length=1000)


class CompanyResponse(BaseModel):
    """公司响应"""
    id: str
    name: str
    industry: str | None = None
    size: str | None = None
    website: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    jd_count: int = 0

    class Config:
        from_attributes = True


class CompanyListResponse(BaseModel):
    """公司列表响应"""
    items: list[CompanyResponse]
    total: int
    page: int
    page_size: int
