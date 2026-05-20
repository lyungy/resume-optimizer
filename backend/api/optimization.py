"""
优化任务 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from pathlib import Path
from models.database import get_db
from schemas import OptimizationCreate, OptimizationResponse, OptimizationListResponse
from services import optimization_service

router = APIRouter(prefix="/optimization", tags=["简历优化"])


@router.post("", response_model=OptimizationResponse)
def create_optimization(
    data: OptimizationCreate,
    db: Session = Depends(get_db),
):
    """创建优化任务"""
    try:
        optimization = optimization_service.create(db, data)
        return optimization_service.to_response(optimization)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=OptimizationListResponse)
def list_optimizations(
    jd_id: Optional[str] = Query(None, description="JD ID"),
    resume_id: Optional[str] = Query(None, description="简历 ID"),
    status: Optional[str] = Query(None, description="状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """获取优化任务列表"""
    items, total = optimization_service.list(
        db,
        jd_id=jd_id,
        resume_id=resume_id,
        status=status,
        page=page,
        page_size=page_size,
    )

    return OptimizationListResponse(
        items=[optimization_service.to_response(o) for o in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{optimization_id}", response_model=OptimizationResponse)
def get_optimization(optimization_id: str, db: Session = Depends(get_db)):
    """获取优化任务详情"""
    optimization = optimization_service.get(db, optimization_id)
    if not optimization:
        raise HTTPException(status_code=404, detail="优化任务不存在")

    return optimization_service.to_response(optimization)


@router.post("/{optimization_id}/execute", response_model=OptimizationResponse)
def execute_optimization(
    optimization_id: str,
    db: Session = Depends(get_db),
):
    """执行优化任务（同步）"""
    try:
        optimization = optimization_service.execute(db, optimization_id)
        return optimization_service.to_response(optimization)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


@router.get("/{optimization_id}/stream")
def stream_optimization(
    optimization_id: str,
    db: Session = Depends(get_db),
):
    """执行优化任务（SSE 流式）"""
    return StreamingResponse(
        optimization_service.execute_stream(db, optimization_id),
        media_type="text/event-stream",
    )


@router.get("/{optimization_id}/download")
def download_optimization(optimization_id: str, db: Session = Depends(get_db)):
    """下载优化后的简历"""
    optimization = optimization_service.get(db, optimization_id)
    if not optimization:
        raise HTTPException(status_code=404, detail="优化任务不存在")

    if not optimization.optimized_docx_path:
        raise HTTPException(status_code=400, detail="优化结果文件不存在")

    file_path = Path(optimization.optimized_docx_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=str(file_path),
        filename=f"优化简历_{optimization.id[:8]}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
