"""
Prompt 模板包
"""
from .jd_parser import get_jd_parse_prompt, JD_PARSE_SYSTEM
from .resume_parser import get_resume_parse_prompt, RESUME_PARSE_SYSTEM
from .resume_optimizer import get_resume_optimize_prompt, RESUME_OPTIMIZE_SYSTEM
from .interview_guide import get_interview_guide_prompt, INTERVIEW_GUIDE_SYSTEM

__all__ = [
    "get_jd_parse_prompt",
    "JD_PARSE_SYSTEM",
    "get_resume_parse_prompt",
    "RESUME_PARSE_SYSTEM",
    "get_resume_optimize_prompt",
    "RESUME_OPTIMIZE_SYSTEM",
    "get_interview_guide_prompt",
    "INTERVIEW_GUIDE_SYSTEM",
]
