"""
数据模型包
"""
from models.base import Base, TimestampMixin
from models.company import Company
from models.jd import JobDescription
from models.resume import Resume
from models.optimization import Optimization
from models.interview import InterviewGuide

__all__ = [
    "Base",
    "TimestampMixin",
    "Company",
    "JobDescription",
    "Resume",
    "Optimization",
    "InterviewGuide",
]
