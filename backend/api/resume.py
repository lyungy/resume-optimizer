"""
简历 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
from models.database import get_db
from schemas import ResumeResponse, ResumeListResponse
from services import resume_service

router = APIRouter(prefix="/resume", tags=["简历管理"])


@router.post("/upload", response_model=ResumeResponse)
async def upload_resume(
    file: UploadFile = File(..., description="简历文件（DOCX）"),
    db: Session = Depends(get_db),
):
    """上传简历"""
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="仅支持 .docx 格式的简历文件")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")

    try:
        resume = resume_service.upload(db, file.filename, content)
        return resume_service.to_response(resume)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/{resume_id}/parse", response_model=ResumeResponse)
def parse_resume(
    resume_id: str,
    llm_provider: Optional[str] = Query(None, description="LLM Provider"),
    db: Session = Depends(get_db),
):
    """使用 LLM 解析简历（提取技能、工作年限等）"""
    try:
        resume = resume_service.parse_with_llm(db, resume_id, llm_provider)
        return resume_service.to_response(resume)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")


@router.get("", response_model=ResumeListResponse)
def list_resumes(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """获取简历列表"""
    items, total = resume_service.list(
        db,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )

    return ResumeListResponse(
        items=[resume_service.to_response(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume(resume_id: str, db: Session = Depends(get_db)):
    """获取简历详情"""
    resume = resume_service.get(db, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    return resume_service.to_response(resume)


@router.delete("/{resume_id}")
def delete_resume(resume_id: str, db: Session = Depends(get_db)):
    """删除简历"""
    success = resume_service.delete(db, resume_id)
    if not success:
        raise HTTPException(status_code=404, detail="简历不存在")

    return {"message": "删除成功"}
