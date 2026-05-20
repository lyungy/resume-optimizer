"""
统计 API 路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.database import get_db
from models import Company, JobDescription, Resume, Optimization, InterviewGuide

router = APIRouter(prefix="/stats", tags=["统计"])


@router.get("/dashboard")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """获取仪表盘统计"""
    # 各模块总数
    company_count = db.query(func.count(Company.id)).scalar()
    jd_count = db.query(func.count(JobDescription.id)).scalar()
    resume_count = db.query(func.count(Resume.id)).scalar()
    optimization_count = db.query(func.count(Optimization.id)).scalar()
    guide_count = db.query(func.count(InterviewGuide.id)).scalar()

    # 解析状态统计
    parsed_jd_count = db.query(func.count(JobDescription.id)).filter(
        JobDescription.is_parsed == True
    ).scalar()

    # 优化状态统计
    completed_optimization = db.query(func.count(Optimization.id)).filter(
        Optimization.status == "completed"
    ).scalar()
    failed_optimization = db.query(func.count(Optimization.id)).filter(
        Optimization.status == "failed"
    ).scalar()

    # 平均匹配度
    avg_match_score = db.query(func.avg(Optimization.match_score)).filter(
        Optimization.status == "completed"
    ).scalar()

    # 最近的优化任务
    recent_optimizations = db.query(Optimization).order_by(
        Optimization.created_at.desc()
    ).limit(5).all()

    recent_list = []
    for opt in recent_optimizations:
        recent_list.append({
            "id": opt.id,
            "jd_title": opt.jd.title if opt.jd else None,
            "company_name": opt.jd.company.name if opt.jd and opt.jd.company else None,
            "status": opt.status,
            "match_score": opt.match_score,
            "created_at": opt.created_at.isoformat() if opt.created_at else None,
        })

    return {
        "counts": {
            "companies": company_count,
            "jds": jd_count,
            "parsed_jds": parsed_jd_count,
            "resumes": resume_count,
            "optimizations": optimization_count,
            "completed_optimizations": completed_optimization,
            "failed_optimizations": failed_optimization,
            "interview_guides": guide_count,
        },
        "metrics": {
            "avg_match_score": round(avg_match_score, 1) if avg_match_score else 0,
            "optimization_success_rate": round(
                completed_optimization / optimization_count * 100, 1
            ) if optimization_count > 0 else 0,
        },
        "recent_optimizations": recent_list,
    }
