"""
公司相关 Schema
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CompanyCreate(BaseModel):
    """创建公司"""
    name: str = Field(..., min_length=1, max_length=200, description="公司名称")
    industry: Optional[str] = Field(None, max_length=100, description="行业")
    size: Optional[str] = Field(None, max_length=50, description="公司规模")
    website: Optional[str] = Field(None, max_length=500, description="公司官网")
    notes: Optional[str] = Field(None, max_length=1000, description="备注")


class CompanyUpdate(BaseModel):
    """更新公司"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    industry: Optional[str] = Field(None, max_length=100)
    size: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=1000)


class CompanyResponse(BaseModel):
    """公司响应"""
    id: str
    name: str
    industry: Optional[str] = None
    size: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None
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
