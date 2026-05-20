"""
服务层包
"""
from .jd_service import jd_service, JDService
from .resume_service import resume_service, ResumeService
from .optimization_service import optimization_service, OptimizationService
from .interview_service import interview_service, InterviewService

__all__ = [
    "jd_service",
    "JDService",
    "resume_service",
    "ResumeService",
    "optimization_service",
    "OptimizationService",
    "interview_service",
    "InterviewService",
]
