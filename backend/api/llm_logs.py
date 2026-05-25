"""
LLM 使用日志 API 路由
"""
import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from models.database import get_db
from models.llm_usage_log import LLMUsageLog

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/llm-logs", tags=["LLM 日志"])


@router.get("")
def list_llm_logs(
    feature: Optional[str] = Query(None, description="功能筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    llm_model: Optional[str] = Query(None, description="模型筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """获取 LLM 调用日志列表"""
    query = db.query(LLMUsageLog)

    if feature:
        query = query.filter(LLMUsageLog.feature == feature)
    if status:
        query = query.filter(LLMUsageLog.status == status)
    if llm_model:
        query = query.filter(LLMUsageLog.llm_model.contains(llm_model))

    total = query.count()
    items = query.order_by(desc(LLMUsageLog.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "items": [_to_dict(log) for log in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{log_id}")
def get_llm_log(log_id: str, db: Session = Depends(get_db)):
    """获取单条日志详情"""
    log = db.query(LLMUsageLog).filter(LLMUsageLog.id == log_id).first()
    if not log:
        return {"error": "日志不存在"}
    return _to_dict(log, detail=True)


@router.get("/stats/summary")
def get_llm_stats(db: Session = Depends(get_db)):
    """获取 LLM 使用统计"""
    from sqlalchemy import func

    # 总调用次数
    total = db.query(func.count(LLMUsageLog.id)).scalar()

    # 成功/失败
    success_count = db.query(func.count(LLMUsageLog.id)).filter(
        LLMUsageLog.status == "success"
    ).scalar()
    failed_count = db.query(func.count(LLMUsageLog.id)).filter(
        LLMUsageLog.status == "failed"
    ).scalar()

    # 总 token
    total_tokens = db.query(func.sum(LLMUsageLog.total_tokens)).scalar() or 0

    # 平均耗时
    avg_duration = db.query(func.avg(LLMUsageLog.duration_ms)).filter(
        LLMUsageLog.status == "success"
    ).scalar()

    # 按功能统计
    feature_stats = db.query(
        LLMUsageLog.feature,
        func.count(LLMUsageLog.id),
        func.sum(LLMUsageLog.total_tokens),
    ).group_by(LLMUsageLog.feature).all()

    # 按模型统计
    model_stats = db.query(
        LLMUsageLog.llm_model,
        func.count(LLMUsageLog.id),
        func.sum(LLMUsageLog.total_tokens),
    ).group_by(LLMUsageLog.llm_model).all()

    return {
        "total_calls": total,
        "success_count": success_count,
        "failed_count": failed_count,
        "success_rate": round(success_count / total * 100, 1) if total > 0 else 0,
        "total_tokens": total_tokens,
        "avg_duration_ms": round(avg_duration) if avg_duration else 0,
        "by_feature": [
            {"feature": f[0], "calls": f[1], "tokens": f[2] or 0}
            for f in feature_stats
        ],
        "by_model": [
            {"model": m[0], "calls": m[1], "tokens": m[2] or 0}
            for m in model_stats
        ],
    }


def _to_dict(log: LLMUsageLog, detail: bool = False) -> dict:
    """转换为字典"""
    result = {
        "id": log.id,
        "feature": log.feature,
        "related_id": log.related_id,
        "related_type": log.related_type,
        "llm_provider": log.llm_provider,
        "llm_model": log.llm_model,
        "input_tokens": log.input_tokens,
        "output_tokens": log.output_tokens,
        "total_tokens": log.total_tokens,
        "duration_ms": log.duration_ms,
        "status": log.status,
        "error_message": log.error_message,
        "retry_count": log.retry_count,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }
    if detail:
        result["system_prompt"] = log.system_prompt
        result["user_prompt"] = log.user_prompt
        result["raw_response"] = log.raw_response
        result["parsed_result"] = log.parsed_result
    return result
