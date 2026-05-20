"""
面试攻略 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from pathlib import Path
from models.database import get_db
from schemas import InterviewGuideCreate, InterviewGuideResponse, InterviewGuideListResponse
from services import interview_service

router = APIRouter(prefix="/interview", tags=["面试攻略"])


@router.post("", response_model=InterviewGuideResponse)
def create_interview_guide(
    data: InterviewGuideCreate,
    db: Session = Depends(get_db),
):
    """创建面试攻略"""
    try:
        guide = interview_service.create(db, data)
        return interview_service.to_response(guide)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=InterviewGuideListResponse)
def list_interview_guides(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """获取面试攻略列表"""
    items, total = interview_service.list(
        db,
        page=page,
        page_size=page_size,
    )

    return InterviewGuideListResponse(
        items=[interview_service.to_response(g) for g in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{guide_id}", response_model=InterviewGuideResponse)
def get_interview_guide(guide_id: str, db: Session = Depends(get_db)):
    """获取面试攻略详情"""
    guide = interview_service.get(db, guide_id)
    if not guide:
        raise HTTPException(status_code=404, detail="攻略不存在")

    return interview_service.to_response(guide)


@router.post("/{guide_id}/generate", response_model=InterviewGuideResponse)
def generate_interview_guide(
    guide_id: str,
    llm_provider: Optional[str] = Query(None, description="LLM Provider"),
    llm_model: Optional[str] = Query(None, description="LLM 模型"),
    db: Session = Depends(get_db),
):
    """生成面试攻略内容"""
    try:
        guide = interview_service.generate(db, guide_id, llm_provider, llm_model)
        return interview_service.to_response(guide)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.get("/{guide_id}/download")
def download_interview_guide(guide_id: str, db: Session = Depends(get_db)):
    """下载面试攻略"""
    guide = interview_service.get(db, guide_id)
    if not guide:
        raise HTTPException(status_code=404, detail="攻略不存在")

    if not guide.export_docx_path:
        raise HTTPException(status_code=400, detail="攻略文档不存在，请先生成")

    file_path = Path(guide.export_docx_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=str(file_path),
        filename=f"面试攻略_{guide.id[:8]}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/by-optimization/{optimization_id}", response_model=InterviewGuideResponse)
def get_guide_by_optimization(
    optimization_id: str,
    db: Session = Depends(get_db),
):
    """根据优化任务获取攻略"""
    guide = interview_service.get_by_optimization(db, optimization_id)
    if not guide:
        raise HTTPException(status_code=404, detail="攻略不存在")

    return interview_service.to_response(guide)
