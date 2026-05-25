"""
JD API 路由
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from models.database import get_db
from schemas import (
    JDCreate, JDUpdate, JDResponse, JDListResponse,
    JDBatchImportRequest, JDBatchImportResponse,
)
from services import jd_service
from models import JobDescription


class BatchDeleteRequest(BaseModel):
    ids: list[str]

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jd", tags=["JD 管理"])


@router.post("", response_model=JDResponse)
def create_jd(data: JDCreate, db: Session = Depends(get_db)):
    """创建 JD"""
    try:
        jd = jd_service.create(db, data)
        return jd_service.to_response(jd)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch-import", response_model=JDBatchImportResponse)
def batch_import_jds(
    data: JDBatchImportRequest,
    db: Session = Depends(get_db),
):
    """批量导入 JD（自动创建公司）"""
    logger.info(f"批量导入 JD: {len(data.items)} 条")
    result = jd_service.batch_import(db, data.items)
    logger.info(f"批量导入完成: 成功 {result['success']}, 失败 {result['failed']}")
    return JDBatchImportResponse(**result)


@router.get("", response_model=JDListResponse)
def list_jds(
    company_id: Optional[str] = Query(None, description="公司 ID"),
    is_parsed: Optional[bool] = Query(None, description="是否已解析"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """获取 JD 列表"""
    items, total = jd_service.list(
        db,
        company_id=company_id,
        is_parsed=is_parsed,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )

    return JDListResponse(
        items=[jd_service.to_response(jd) for jd in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{jd_id}", response_model=JDResponse)
def get_jd(jd_id: str, db: Session = Depends(get_db)):
    """获取 JD 详情"""
    jd = jd_service.get(db, jd_id)
    if not jd:
        raise HTTPException(status_code=404, detail="JD 不存在")

    return jd_service.to_response(jd)


@router.put("/{jd_id}", response_model=JDResponse)
def update_jd(jd_id: str, data: JDUpdate, db: Session = Depends(get_db)):
    """更新 JD"""
    jd = jd_service.update(db, jd_id, data)
    if not jd:
        raise HTTPException(status_code=404, detail="JD 不存在")

    return jd_service.to_response(jd)


@router.delete("/{jd_id}")
def delete_jd(jd_id: str, db: Session = Depends(get_db)):
    """删除 JD"""
    success = jd_service.delete(db, jd_id)
    if not success:
        raise HTTPException(status_code=404, detail="JD 不存在")

    return {"message": "删除成功"}


@router.post("/batch-delete")
def batch_delete_jds(
    data: BatchDeleteRequest,
    db: Session = Depends(get_db),
):
    """批量删除 JD"""
    if not data.ids:
        raise HTTPException(status_code=400, detail="ids 不能为空")

    jds = db.query(JobDescription).filter(JobDescription.id.in_(data.ids)).all()
    deleted = 0
    for jd in jds:
        db.delete(jd)
        deleted += 1

    db.commit()
    logger.info(f"批量删除 JD: {deleted} 条")
    return {"deleted": deleted}


@router.post("/{jd_id}/parse", response_model=JDResponse)
async def parse_jd(
    jd_id: str,
    llm_provider: Optional[str] = Query(None, description="LLM Provider"),
    llm_model: Optional[str] = Query(None, description="LLM 模型"),
    db: Session = Depends(get_db),
):
    """解析 JD（异步）"""
    import asyncio
    try:
        logger.info(f"开始解析 JD: {jd_id}")
        jd = await asyncio.to_thread(
            jd_service.parse, db, jd_id, llm_provider, llm_model
        )
        logger.info(f"JD 解析完成: {jd_id}")
        return jd_service.to_response(jd)
    except ValueError as e:
        logger.warning(f"JD 解析参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"JD 解析失败: {e}")
        raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")


@router.get("/{jd_id}/parse-stream")
def parse_jd_stream(
    jd_id: str,
    llm_provider: Optional[str] = Query(None, description="LLM Provider"),
    llm_model: Optional[str] = Query(None, description="LLM 模型"),
    db: Session = Depends(get_db),
):
    """解析 JD（SSE 流式）"""
    import json

    def generate():
        try:
            jd = jd_service.get(db, jd_id)
            if not jd:
                yield f"data: {json.dumps({'error': 'JD 不存在'})}\n\n"
                return

            yield f"data: {json.dumps({'status': 'started', 'progress': 0})}\n\n"

            # 获取公司信息
            company = jd.company
            company_name = company.name if company else "未知公司"
            industry = company.industry if company else "未知行业"

            yield f"data: {json.dumps({'status': 'analyzing', 'progress': 20, 'message': '正在分析 JD...'})}\n\n"

            # 获取 LLM 客户端
            from services.llm import get_llm_client
            from services.llm.prompts import get_jd_parse_prompt

            client = get_llm_client(llm_provider)

            # 构建 prompt
            messages = get_jd_parse_prompt(
                title=jd.title,
                company_name=company_name,
                industry=industry,
                jd_text=jd.raw_text,
            )

            yield f"data: {json.dumps({'status': 'calling_llm', 'progress': 40, 'message': '正在调用 AI...'})}\n\n"

            # 流式调用 LLM
            full_response = ""
            for chunk in client.chat_stream(
                messages=messages,
                model=llm_model,
                temperature=0.3,
                max_tokens=2000,
            ):
                full_response += chunk
                yield f"data: {json.dumps({'status': 'streaming', 'progress': 60, 'content': chunk})}\n\n"

            yield f"data: {json.dumps({'status': 'parsing', 'progress': 80, 'message': '正在解析结果...'})}\n\n"

            # 解析结果
            import re
            try:
                result = json.loads(full_response)
            except json.JSONDecodeError:
                json_match = re.search(r'\{.*\}', full_response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise ValueError("LLM 返回格式错误")

            # 更新 JD
            jd.parsed_requirements = result
            jd.hard_skills = result.get("hard_skills", [])
            jd.soft_skills = result.get("soft_skills", [])
            jd.hidden_requirements = result.get("hidden_requirements", [])
            jd.experience_years = result.get("experience_years")
            jd.difficulty_level = result.get("difficulty_level")
            jd.senior_friendly = result.get("senior_friendly")
            jd.senior_friendly_signals = result.get("senior_friendly_signals", [])
            jd.concern_signals = result.get("concern_signals", [])
            jd.key_keywords = result.get("key_keywords", [])
            jd.is_parsed = True

            db.commit()

            yield f"data: {json.dumps({'status': 'completed', 'progress': 100, 'jd_id': jd.id})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
