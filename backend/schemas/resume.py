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
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResumeListResponse(BaseModel):
    """简历列表响应"""
    items: list[ResumeResponse]
    total: int
    page: int
    page_size: int
