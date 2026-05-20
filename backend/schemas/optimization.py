"""
优化任务相关 Schema
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class OptimizationCreate(BaseModel):
    """创建优化任务"""
    jd_id: str = Field(..., description="JD ID")
    resume_id: str = Field(..., description="简历 ID")
    llm_provider: Optional[str] = Field(None, description="LLM Provider（默认 xiaomi-coding）")
    llm_model: Optional[str] = Field(None, description="LLM 模型（使用 Provider 默认）")


class KeywordCoverage(BaseModel):
    """关键词覆盖情况"""
    matched: list[str] = []
    missing: list[str] = []
    coverage_rate: float = 0.0


class OptimizedExperience(BaseModel):
    """优化后的工作经历"""
    company: str = ""
    title: str = ""
    period: Optional[str] = None
    highlights: list[str] = []


class OptimizedProject(BaseModel):
    """优化后的项目经历"""
    name: str = ""
    role: Optional[str] = None
    highlights: list[str] = []


class OptimizedSections(BaseModel):
    """优化后的内容"""
    summary: Optional[str] = None
    skills: list[str] = []
    experience: list[OptimizedExperience] = []
    projects: list[OptimizedProject] = []


class OptimizationResult(BaseModel):
    """优化结果"""
    match_score: float = 0.0
    keyword_coverage: KeywordCoverage = KeywordCoverage()
    optimized_sections: OptimizedSections = OptimizedSections()
    suggestions: list[str] = []
    ats_tips: list[str] = []
    interview_highlights: list[str] = []


class OptimizationResponse(BaseModel):
    """优化任务响应"""
    id: str
    jd_id: str
    resume_id: str
    llm_provider: str
    llm_model: str
    status: str
    match_score: Optional[float] = None
    keyword_coverage: Optional[dict] = None
    optimization_result: Optional[dict] = None
    suggestions: Optional[list[str]] = None
    ats_tips: Optional[list[str]] = None
    optimized_docx_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # 关联数据
    jd_title: Optional[str] = None
    company_name: Optional[str] = None
    resume_name: Optional[str] = None
    has_interview_guide: bool = False

    class Config:
        from_attributes = True


class OptimizationListResponse(BaseModel):
    """优化任务列表响应"""
    items: list[OptimizationResponse]
    total: int
    page: int
    page_size: int
