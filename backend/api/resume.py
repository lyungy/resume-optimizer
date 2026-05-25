"""
简历 API 路由
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
from models.database import get_db
from schemas import ResumeResponse, ResumeListResponse
from schemas.resume import DeepAnalyzeResponse, ProfileUpdateRequest
from services import resume_service
from services.llm.prompts import RESUME_PARSE_PROMPT_TEMPLATE, DEEP_ANALYZE_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)
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
        logger.info(f"简历上传成功: {file.filename} -> {resume.id}")
        return resume_service.to_response(resume)
    except Exception as e:
        logger.error(f"简历上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/{resume_id}/parse", response_model=ResumeResponse)
async def parse_resume(
    resume_id: str,
    llm_provider: Optional[str] = Query(None, description="LLM Provider"),
    custom_prompt: Optional[str] = Query(None, description="自定义 system prompt"),
    db: Session = Depends(get_db),
):
    """使用 LLM 智能解析简历"""
    import asyncio
    try:
        logger.info(f"开始智能解析简历: {resume_id}")
        resume = await asyncio.to_thread(
            resume_service.parse_with_llm, db, resume_id, llm_provider, custom_prompt
        )
        logger.info(f"简历解析完成: {resume_id}")
        return resume_service.to_response(resume)
    except ValueError as e:
        logger.warning(f"简历解析参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"简历解析失败: {e}")
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


@router.get("/prompts/parse")
def get_parse_prompt():
    """获取智能解析的默认 prompt"""
    return {"prompt": RESUME_PARSE_PROMPT_TEMPLATE}


@router.get("/prompts/deep-analyze")
def get_deep_analyze_prompt_api():
    """获取职业画像的默认 prompt"""
    return {"prompt": DEEP_ANALYZE_PROMPT_TEMPLATE}


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


@router.post("/{resume_id}/deep-analyze", response_model=DeepAnalyzeResponse)
async def deep_analyze_resume(
    resume_id: str,
    llm_provider: Optional[str] = Query(None, description="LLM Provider"),
    custom_prompt: Optional[str] = Query(None, description="自定义 system prompt"),
    db: Session = Depends(get_db),
):
    """职业画像分析"""
    import asyncio
    try:
        logger.info(f"开始职业画像分析: {resume_id}")
        result = await asyncio.to_thread(
            resume_service.deep_analyze, db, resume_id, llm_provider, custom_prompt
        )
        logger.info(f"简历职业画像完成: {resume_id}")
        return result
    except ValueError as e:
        logger.warning(f"职业画像参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"简历职业画像失败: {e}")
        raise HTTPException(status_code=500, detail=f"职业画像失败: {str(e)}")


@router.put("/{resume_id}/profile", response_model=ResumeResponse)
def update_resume_profile(
    resume_id: str,
    data: ProfileUpdateRequest,
    db: Session = Depends(get_db),
):
    """更新求职画像（用户编辑后保存）"""
    try:
        resume = resume_service.update_profile(
            db, resume_id,
            profile=data.profile,
            recommended_positions=data.recommended_positions,
            job_preference=data.job_preference,
        )
        return resume_service.to_response(resume)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.get("/{resume_id}/versions")
def list_resume_versions(
    resume_id: str,
    db: Session = Depends(get_db),
):
    """获取简历版本历史"""
    from models import ResumeVersion
    versions = db.query(ResumeVersion).filter(
        ResumeVersion.resume_id == resume_id
    ).order_by(ResumeVersion.version_no.desc()).all()

    return [{
        "id": v.id,
        "version_no": v.version_no,
        "label": v.label,
        "skills": v.skills,
        "experience_years": v.experience_years,
        "created_at": v.created_at.isoformat() if v.created_at else None,
    } for v in versions]


@router.get("/{resume_id}/versions/{version_id}")
def get_resume_version(
    resume_id: str,
    version_id: str,
    db: Session = Depends(get_db),
):
    """获取指定版本详情"""
    from models import ResumeVersion
    version = db.query(ResumeVersion).filter(
        ResumeVersion.id == version_id,
        ResumeVersion.resume_id == resume_id,
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")

    return {
        "id": version.id,
        "version_no": version.version_no,
        "label": version.label,
        "skills": version.skills,
        "experience_years": version.experience_years,
        "education": version.education,
        "work_experience": version.work_experience,
        "projects": version.projects,
        "profile": version.profile,
        "recommended_positions": version.recommended_positions,
        "parsed_content": version.parsed_content,
        "created_at": version.created_at.isoformat() if version.created_at else None,
    }


@router.post("/{resume_id}/versions/{version_id}/restore", response_model=ResumeResponse)
def restore_resume_version(
    resume_id: str,
    version_id: str,
    db: Session = Depends(get_db),
):
    """恢复到指定版本"""
    from models import ResumeVersion
    resume = resume_service.get(db, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    version = db.query(ResumeVersion).filter(
        ResumeVersion.id == version_id,
        ResumeVersion.resume_id == resume_id,
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")

    # 恢复快照数据
    resume.skills = version.skills
    resume.experience_years = version.experience_years
    resume.education = version.education
    resume.work_experience = version.work_experience
    resume.projects = version.projects
    resume.profile = version.profile
    resume.recommended_positions = version.recommended_positions
    resume.parsed_content = version.parsed_content

    # 创建恢复版本快照
    resume_service._create_snapshot(db, resume, f"恢复到 v{version.version_no}")

    db.commit()
    db.refresh(resume)
    return resume_service.to_response(resume)
