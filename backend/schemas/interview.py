"""
面试攻略相关 Schema
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class KnowledgePoint(BaseModel):
    """知识点"""
    category: str = ""
    points: list[str] = []
    priority: str = "medium"
    estimated_prep_hours: int = 0
    study_resources: list[str] = []


class HighFrequencyQuestion(BaseModel):
    """高频面试题"""
    question: str = ""
    category: str = ""
    difficulty: str = "medium"
    answer_template: Optional[str] = None
    key_points: list[str] = []
    common_mistakes: list[str] = []


class DayPlan(BaseModel):
    """每日计划"""
    day: int = 0
    focus: str = ""
    tasks: list[str] = []
    hours: int = 0


class PreparationStrategy(BaseModel):
    """准备策略"""
    total_days: int = 7
    daily_plan: list[DayPlan] = []
    tips: list[str] = []


class CompanyResearch(BaseModel):
    """公司调研"""
    what_to_prepare: list[str] = []
    questions_to_ask: list[str] = []
    red_flags: list[str] = []


class SalaryNegotiation(BaseModel):
    """薪资谈判"""
    market_range: Optional[str] = None
    negotiation_tips: list[str] = []


class InterviewGuideCreate(BaseModel):
    """创建面试攻略"""
    optimization_id: str = Field(..., description="优化任务 ID")
    llm_provider: Optional[str] = Field(None, description="LLM Provider")
    llm_model: Optional[str] = Field(None, description="LLM 模型")


class InterviewGuideResponse(BaseModel):
    """面试攻略响应"""
    id: str
    optimization_id: str
    knowledge_points: Optional[list[dict]] = None
    high_frequency_questions: Optional[list[dict]] = None
    answer_templates: Optional[list[dict]] = None
    preparation_strategy: Optional[dict] = None
    company_research: Optional[dict] = None
    export_docx_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # 关联数据
    jd_title: Optional[str] = None
    company_name: Optional[str] = None

    class Config:
        from_attributes = True


class InterviewGuideListResponse(BaseModel):
    """面试攻略列表响应"""
    items: list[InterviewGuideResponse]
    total: int
    page: int
    page_size: int
