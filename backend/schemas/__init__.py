"""
Schema 包
"""
from .company import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyListResponse
from .jd import (
    JDCreate, JDUpdate, JDParseResult, JDResponse, JDListResponse,
    JDBatchImportItem, JDBatchImportRequest, JDBatchImportResponse,
)
from .resume import ResumeResponse, ResumeListResponse, DeepAnalyzeResponse, ProfileUpdateRequest, SearchMatchRequest
from .optimization import (
    OptimizationCreate,
    OptimizationResult,
    OptimizationResponse,
    OptimizationListResponse,
)
from .interview import (
    InterviewGuideCreate,
    InterviewGuideResponse,
    InterviewGuideListResponse,
)

__all__ = [
    "CompanyCreate",
    "CompanyUpdate",
    "CompanyResponse",
    "CompanyListResponse",
    "JDCreate",
    "JDUpdate",
    "JDParseResult",
    "JDResponse",
    "JDListResponse",
    "JDBatchImportItem",
    "JDBatchImportRequest",
    "JDBatchImportResponse",
    "ResumeResponse",
    "ResumeListResponse",
    "DeepAnalyzeResponse",
    "ProfileUpdateRequest",
    "SearchMatchRequest",
    "OptimizationCreate",
    "OptimizationResult",
    "OptimizationResponse",
    "OptimizationListResponse",
    "InterviewGuideCreate",
    "InterviewGuideResponse",
    "InterviewGuideListResponse",
]
