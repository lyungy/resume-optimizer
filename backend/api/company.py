"""
公司 API 路由
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from models.database import get_db
from schemas import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyListResponse
from models import Company


class BatchDeleteRequest(BaseModel):
    ids: list[str]

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/companies", tags=["公司管理"])


@router.post("", response_model=CompanyResponse)
def create_company(data: CompanyCreate, db: Session = Depends(get_db)):
    """创建公司"""
    company = Company(
        name=data.name,
        industry=data.industry,
        size=data.size,
        website=data.website,
        notes=data.notes,
    )
    db.add(company)
    db.commit()
    db.refresh(company)

    return CompanyResponse(
        id=company.id,
        name=company.name,
        industry=company.industry,
        size=company.size,
        website=company.website,
        notes=company.notes,
        created_at=company.created_at,
        updated_at=company.updated_at,
        jd_count=0,
    )


@router.get("", response_model=CompanyListResponse)
def list_companies(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """获取公司列表"""
    query = db.query(Company)

    if keyword:
        query = query.filter(
            Company.name.contains(keyword)
            | Company.industry.contains(keyword)
        )

    total = query.count()
    companies = query.order_by(Company.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    items = []
    for company in companies:
        items.append(CompanyResponse(
            id=company.id,
            name=company.name,
            industry=company.industry,
            size=company.size,
            website=company.website,
            notes=company.notes,
            created_at=company.created_at,
            updated_at=company.updated_at,
            jd_count=len(company.jds),
        ))

    return CompanyListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(company_id: str, db: Session = Depends(get_db)):
    """获取公司详情"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")

    return CompanyResponse(
        id=company.id,
        name=company.name,
        industry=company.industry,
        size=company.size,
        website=company.website,
        notes=company.notes,
        created_at=company.created_at,
        updated_at=company.updated_at,
        jd_count=len(company.jds),
    )


@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: str,
    data: CompanyUpdate,
    db: Session = Depends(get_db),
):
    """更新公司"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(company, key, value)

    db.commit()
    db.refresh(company)

    return CompanyResponse(
        id=company.id,
        name=company.name,
        industry=company.industry,
        size=company.size,
        website=company.website,
        notes=company.notes,
        created_at=company.created_at,
        updated_at=company.updated_at,
        jd_count=len(company.jds),
    )


@router.delete("/{company_id}")
def delete_company(company_id: str, db: Session = Depends(get_db)):
    """删除公司"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")

    if company.jds:
        raise HTTPException(
            status_code=400,
            detail="该公司下存在 JD，无法删除"
        )

    db.delete(company)
    db.commit()

    return {"message": "删除成功"}


@router.post("/batch-delete")
def batch_delete_companies(
    data: BatchDeleteRequest,
    db: Session = Depends(get_db),
):
    """批量删除公司"""
    if not data.ids:
        raise HTTPException(status_code=400, detail="ids 不能为空")

    companies = db.query(Company).filter(Company.id.in_(data.ids)).all()
    skipped = []
    deleted = 0
    for company in companies:
        if company.jds:
            skipped.append(company.name)
            continue
        db.delete(company)
        deleted += 1

    db.commit()
    logger.info(f"批量删除公司: 成功 {deleted}, 跳过 {len(skipped)}")

    result = {"deleted": deleted, "skipped": len(skipped)}
    if skipped:
        result["skipped_names"] = skipped[:10]
    return result
