"""
JD 服务层
"""
from __future__ import annotations
import json
from typing import Optional
from sqlalchemy.orm import Session
from models import JobDescription, Company
from schemas import JDCreate, JDUpdate, JDResponse, JDParseResult
from services.llm import get_llm_client
from services.llm.prompts import get_jd_parse_prompt


class JDService:
    """JD 服务"""

    def create(self, db: Session, data: JDCreate) -> JobDescription:
        """创建 JD"""
        # 检查公司是否存在
        company = db.query(Company).filter(Company.id == data.company_id).first()
        if not company:
            raise ValueError(f"公司不存在: {data.company_id}")

        jd = JobDescription(
            company_id=data.company_id,
            title=data.title,
            raw_text=data.raw_text,
            source_url=data.source_url,
        )
        db.add(jd)
        db.commit()
        db.refresh(jd)
        return jd

    def get(self, db: Session, jd_id: str) -> Optional[JobDescription]:
        """获取 JD"""
        return db.query(JobDescription).filter(JobDescription.id == jd_id).first()

    def list(
        self,
        db: Session,
        company_id: Optional[str] = None,
        is_parsed: Optional[bool] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[JobDescription], int]:
        """获取 JD 列表"""
        query = db.query(JobDescription)

        if company_id:
            query = query.filter(JobDescription.company_id == company_id)
        if is_parsed is not None:
            query = query.filter(JobDescription.is_parsed == is_parsed)
        if keyword:
            query = query.filter(
                JobDescription.title.contains(keyword)
                | JobDescription.raw_text.contains(keyword)
            )

        total = query.count()
        items = query.order_by(JobDescription.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total

    def update(self, db: Session, jd_id: str, data: JDUpdate) -> Optional[JobDescription]:
        """更新 JD"""
        jd = self.get(db, jd_id)
        if not jd:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(jd, key, value)

        db.commit()
        db.refresh(jd)
        return jd

    def delete(self, db: Session, jd_id: str) -> bool:
        """删除 JD"""
        jd = self.get(db, jd_id)
        if not jd:
            return False

        db.delete(jd)
        db.commit()
        return True

    def parse(
        self,
        db: Session,
        jd_id: str,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
    ) -> JobDescription:
        """
        解析 JD - 使用 LLM 提取结构化信息
        """
        jd = self.get(db, jd_id)
        if not jd:
            raise ValueError(f"JD 不存在: {jd_id}")

        # 获取公司信息
        company = db.query(Company).filter(Company.id == jd.company_id).first()
        company_name = company.name if company else "未知公司"
        industry = company.industry if company else "未知行业"

        # 获取 LLM 客户端
        client = get_llm_client(llm_provider)

        # 构建 prompt
        messages = get_jd_parse_prompt(
            title=jd.title,
            company_name=company_name,
            industry=industry,
            jd_text=jd.raw_text,
        )

        # 调用 LLM
        response = client.chat_json(
            messages=messages,
            model=llm_model,
            temperature=0.3,
            max_tokens=2000,
        )

        # 解析结果
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取 JSON 部分
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                raise ValueError(f"LLM 返回格式错误: {response[:200]}")

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
        db.refresh(jd)
        return jd

    def to_response(self, jd: JobDescription) -> JDResponse:
        """转换为响应格式"""
        return JDResponse(
            id=jd.id,
            company_id=jd.company_id,
            company_name=jd.company.name if jd.company else None,
            title=jd.title,
            raw_text=jd.raw_text,
            source_url=jd.source_url,
            is_parsed=jd.is_parsed,
            parsed_requirements=jd.parsed_requirements,
            hard_skills=jd.hard_skills,
            soft_skills=jd.soft_skills,
            hidden_requirements=jd.hidden_requirements,
            experience_years=jd.experience_years,
            difficulty_level=jd.difficulty_level,
            senior_friendly=jd.senior_friendly,
            senior_friendly_signals=jd.senior_friendly_signals,
            concern_signals=jd.concern_signals,
            key_keywords=jd.key_keywords,
            created_at=jd.created_at,
            updated_at=jd.updated_at,
        )


# 全局实例
jd_service = JDService()
