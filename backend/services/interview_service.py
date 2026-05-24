"""
面试攻略服务层 - 增强版
支持重试、容错解析、DOCX 降级
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from models import InterviewGuide, Optimization, JobDescription
from schemas import InterviewGuideCreate, InterviewGuideResponse
from services.llm import get_llm_client
from services.llm.retry import call_llm_with_retry, parse_json_response
from services.llm.prompts import get_interview_guide_prompt
from utils import docx_writer
from config import config

logger = logging.getLogger(__name__)


class InterviewService:
    """面试攻略服务"""

    # 重试配置
    MAX_RETRIES = 3
    RETRY_BASE_DELAY = 2  # 秒

    def create(self, db: Session, data: InterviewGuideCreate) -> InterviewGuide:
        """创建面试攻略"""
        optimization = db.query(Optimization).filter(
            Optimization.id == data.optimization_id
        ).first()
        if not optimization:
            raise ValueError(f"优化任务不存在: {data.optimization_id}")

        if optimization.status != "completed":
            raise ValueError(f"优化任务未完成，当前状态: {optimization.status}")

        existing = db.query(InterviewGuide).filter(
            InterviewGuide.optimization_id == data.optimization_id
        ).first()
        if existing:
            return existing

        guide = InterviewGuide(
            optimization_id=data.optimization_id,
        )
        db.add(guide)
        db.commit()
        db.refresh(guide)
        return guide

    def get(self, db: Session, guide_id: str) -> Optional[InterviewGuide]:
        """获取面试攻略"""
        return db.query(InterviewGuide).filter(InterviewGuide.id == guide_id).first()

    def get_by_optimization(
        self, db: Session, optimization_id: str
    ) -> Optional[InterviewGuide]:
        """根据优化任务获取攻略"""
        return db.query(InterviewGuide).filter(
            InterviewGuide.optimization_id == optimization_id
        ).first()

    def list(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[InterviewGuide], int]:
        """获取攻略列表"""
        query = db.query(InterviewGuide)
        total = query.count()
        items = query.order_by(InterviewGuide.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return items, total

    def generate(
        self,
        db: Session,
        guide_id: str,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
    ) -> InterviewGuide:
        """生成面试攻略内容（带重试和容错）"""
        guide = self.get(db, guide_id)
        if not guide:
            raise ValueError(f"攻略不存在: {guide_id}")

        # 获取优化任务和关联数据
        optimization = db.query(Optimization).filter(
            Optimization.id == guide.optimization_id
        ).first()
        jd = db.query(JobDescription).filter(
            JobDescription.id == optimization.jd_id
        ).first()

        # 获取优化后的简历摘要
        optimized_summary = self._extract_optimized_summary(optimization)

        # 获取 LLM 客户端
        provider = llm_provider or optimization.llm_provider
        client = get_llm_client(provider)
        model = llm_model or optimization.llm_model

        # 构建 prompt
        messages = get_interview_guide_prompt(
            jd_title=jd.title if jd else "",
            company_name=jd.company.name if jd and jd.company else "",
            hard_skills=jd.hard_skills if jd and jd.hard_skills else [],
            difficulty_level=jd.difficulty_level if jd else "mid",
            senior_friendly=jd.senior_friendly if jd and jd.senior_friendly is not None else True,
            optimized_summary=optimized_summary,
        )

        # 调用 LLM（带重试）
        response = call_llm_with_retry(client, messages, model)

        # 解析结果（带容错）
        result = parse_json_response(response)

        # 更新攻略
        guide.knowledge_points = result.get("knowledge_points", [])
        guide.high_frequency_questions = result.get("high_frequency_questions", [])
        guide.answer_templates = result.get("high_frequency_questions", [])
        guide.preparation_strategy = result.get("preparation_strategy", {})
        guide.company_research = result.get("company_research", {})

        # 生成 DOCX（带降级）
        docx_path = self._generate_docx_safe(guide, result, jd)
        guide.export_docx_path = docx_path

        db.commit()
        db.refresh(guide)
        return guide

    def _extract_optimized_summary(self, optimization: Optimization) -> str:
        """提取优化后的简历摘要"""
        if not optimization.optimization_result:
            return ""

        sections = optimization.optimization_result.get("optimized_sections", {})
        parts = []

        if "summary" in sections:
            parts.append(sections["summary"])
        if "skills" in sections:
            parts.append("技能：" + "、".join(sections["skills"]))

        return "\n".join(parts)

    def _generate_docx_safe(
        self,
        guide: InterviewGuide,
        result: dict,
        jd: JobDescription = None,
    ) -> Optional[str]:
        """生成 DOCX（带降级保护）"""
        try:
            output_dir = Path(config.files.dir) / "optimized"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{guide.id}_interview.docx"

            docx_writer.create_interview_guide(
                content=result,
                output_path=str(output_path),
                jd_title=jd.title if jd else "",
                company_name=jd.company.name if jd and jd.company else "",
            )

            return str(output_path)

        except Exception as e:
            # DOCX 生成失败不影响攻略内容
            logger.error(f"DOCX 生成失败（攻略内容已保存）: {e}")
            return None

    def to_response(self, guide: InterviewGuide) -> InterviewGuideResponse:
        """转换为响应格式"""
        optimization = guide.optimization
        jd = optimization.jd if optimization else None

        return InterviewGuideResponse(
            id=guide.id,
            optimization_id=guide.optimization_id,
            knowledge_points=guide.knowledge_points,
            high_frequency_questions=guide.high_frequency_questions,
            answer_templates=guide.answer_templates,
            preparation_strategy=guide.preparation_strategy,
            company_research=guide.company_research,
            export_docx_path=guide.export_docx_path,
            created_at=guide.created_at,
            updated_at=guide.updated_at,
            jd_title=jd.title if jd else None,
            company_name=jd.company.name if jd and jd.company else None,
        )


# 全局实例
interview_service = InterviewService()
