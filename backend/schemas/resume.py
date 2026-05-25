"""
简历相关 Schema
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ResumeResponse(BaseModel):
    """简历响应"""
    id: str
    name: str
    original_file_path: str
    is_parsed: bool = False
    parsed_content: dict | None = None
    skills: Optional[list[str]] = None
    experience_years: int | None = None
    education: dict | None = None
    work_experience: Optional[list[dict]] = None
    projects: Optional[list[dict]] = None
    profile: dict | None = None
    recommended_positions: Optional[list[dict]] = None
    job_preference: dict | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeepAnalyzeResponse(BaseModel):
    """职业画像响应"""
    profile: dict
    recommended_positions: list[dict]
    search_keywords: list[str]


class ProfileUpdateRequest(BaseModel):
    """求职画像更新请求"""
    profile: dict | None = None
    recommended_positions: Optional[list[dict]] = None
    job_preference: dict | None = None


class SearchMatchRequest(BaseModel):
    """搜索匹配请求"""
    resume_id: str
    selected_positions: list[str]
    city: str = "上海"
    salary_min: int | None = None
    salary_max: int | None = None
    limit_per_keyword: int = 30


class ResumeListResponse(BaseModel):
    """简历列表响应"""
    items: list[ResumeResponse]
    total: int
    page: int
    page_size: int
