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
    parsed_content: Optional[dict] = None
    skills: Optional[list[str]] = None
    experience_years: Optional[int] = None
    education: Optional[dict] = None
    work_experience: Optional[list[dict]] = None
    projects: Optional[list[dict]] = None
    profile: Optional[dict] = None
    recommended_positions: Optional[list[dict]] = None
    job_preference: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeepAnalyzeResponse(BaseModel):
    """深度解析响应"""
    profile: dict
    recommended_positions: list[dict]
    search_keywords: list[str]


class ProfileUpdateRequest(BaseModel):
    """求职画像更新请求"""
    profile: Optional[dict] = None
    recommended_positions: Optional[list[dict]] = None
    job_preference: Optional[dict] = None


class SearchMatchRequest(BaseModel):
    """搜索匹配请求"""
    resume_id: str
    selected_positions: list[str]
    city: str = "上海"
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    limit_per_keyword: int = 20


class ResumeListResponse(BaseModel):
    """简历列表响应"""
    items: list[ResumeResponse]
    total: int
    page: int
    page_size: int
