"""
API 路由包
"""
from .company import router as company_router
from .jd import router as jd_router
from .resume import router as resume_router
from .optimization import router as optimization_router
from .interview import router as interview_router
from .llm import router as llm_router
from .stats import router as stats_router

__all__ = [
    "company_router",
    "jd_router",
    "resume_router",
    "optimization_router",
    "interview_router",
    "llm_router",
    "stats_router",
]
