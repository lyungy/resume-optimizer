"""
简历优化服务层
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Optional, Generator
from sqlalchemy.orm import Session
from models import Optimization, JobDescription, Resume
from schemas import OptimizationCreate, OptimizationResponse
from services.llm import get_llm_client
from services.llm.retry import call_llm_with_retry, parse_json_response
from services.llm.prompts import get_resume_optimize_prompt
from services.llm.usage_logger import log_llm_usage, timed_llm_call
from utils import docx_writer
from config import config

logger = logging.getLogger(__name__)


class OptimizationService:
    """简历优化服务"""

    def create(self, db: Session, data: OptimizationCreate) -> Optimization:
        """创建优化任务"""
        # 验证 JD 存在
        jd = db.query(JobDescription).filter(JobDescription.id == data.jd_id).first()
        if not jd:
            raise ValueError(f"JD 不存在: {data.jd_id}")

        # 验证简历存在
        resume = db.query(Resume).filter(Resume.id == data.resume_id).first()
        if not resume:
            raise ValueError(f"简历不存在: {data.resume_id}")

        # 创建优化任务
        optimization = Optimization(
            jd_id=data.jd_id,
            resume_id=data.resume_id,
            llm_provider=data.llm_provider or config.llm.default_provider,
            llm_model=data.llm_model or "",
            status="pending",
        )

        # 如果未指定模型，使用 Provider 默认
        if not data.llm_model:
            client = get_llm_client(data.llm_provider)
            optimization.llm_model = client.default_model

        db.add(optimization)
        db.commit()
        db.refresh(optimization)
        return optimization

    def get(self, db: Session, optimization_id: str) -> Optional[Optimization]:
        """获取优化任务"""
        return db.query(Optimization).filter(Optimization.id == optimization_id).first()

    def list(
        self,
        db: Session,
        jd_id: Optional[str] = None,
        resume_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Optimization], int]:
        """获取优化任务列表"""
        query = db.query(Optimization)

        if jd_id:
            query = query.filter(Optimization.jd_id == jd_id)
        if resume_id:
            query = query.filter(Optimization.resume_id == resume_id)
        if status:
            query = query.filter(Optimization.status == status)

        total = query.count()
        items = query.order_by(Optimization.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total

    def execute(
        self,
        db: Session,
        optimization_id: str,
    ) -> Optimization:
        """执行优化任务（同步）"""
        optimization = self.get(db, optimization_id)
        if not optimization:
            raise ValueError(f"优化任务不存在: {optimization_id}")

        # 更新状态
        optimization.status = "processing"
        db.commit()
        logger.info(f"开始执行优化任务: {optimization_id}")

        try:
            # 获取 JD 和简历
            jd = db.query(JobDescription).filter(
                JobDescription.id == optimization.jd_id
            ).first()
            resume = db.query(Resume).filter(
                Resume.id == optimization.resume_id
            ).first()

            # 获取简历文本
            resume_text = ""
            if resume.parsed_content and "text" in resume.parsed_content:
                resume_text = resume.parsed_content["text"]

            # 获取 LLM 客户端
            client = get_llm_client(optimization.llm_provider)

            # 构建 prompt
            messages = get_resume_optimize_prompt(
                jd_title=jd.title,
                company_name=jd.company.name if jd.company else "未知公司",
                hard_skills=jd.hard_skills or [],
                soft_skills=jd.soft_skills or [],
                key_keywords=jd.key_keywords or [],
                difficulty_level=jd.difficulty_level or "mid",
                senior_friendly=jd.senior_friendly if jd.senior_friendly is not None else True,
                resume_text=resume_text,
            )

            # 调用 LLM（带重试+计时+日志）
            import time as _time
            _start = _time.time()
            _retry_count = 0
            try:
                response = call_llm_with_retry(
                    client=client,
                    messages=messages,
                    model=optimization.llm_model,
                )
                _duration_ms = int((_time.time() - _start) * 1000)
            except Exception as e:
                _duration_ms = int((_time.time() - _start) * 1000)
                log_llm_usage(
                    db, feature="简历优化", llm_provider=client.provider.name,
                    llm_model=optimization.llm_model,
                    system_prompt=messages[0]["content"],
                    user_prompt=messages[1]["content"] if len(messages) > 1 else None,
                    duration_ms=_duration_ms, status="failed",
                    error_message=str(e), retry_count=_retry_count,
                    related_id=optimization_id, related_type="optimization",
                )
                raise

            # 解析结果（带容错）
            result = parse_json_response(response)
            if not result:
                log_llm_usage(
                    db, feature="简历优化", llm_provider=client.provider.name,
                    llm_model=optimization.llm_model,
                    system_prompt=messages[0]["content"],
                    user_prompt=messages[1]["content"] if len(messages) > 1 else None,
                    raw_response=response, duration_ms=_duration_ms,
                    status="failed", error_message="JSON 解析失败",
                    related_id=optimization_id, related_type="optimization",
                )
                raise ValueError("LLM 返回格式错误")

            # 记录成功日志
            log_llm_usage(
                db, feature="简历优化", llm_provider=client.provider.name,
                llm_model=optimization.llm_model,
                system_prompt=messages[0]["content"],
                user_prompt=messages[1]["content"] if len(messages) > 1 else None,
                raw_response=response, parsed_result=result,
                duration_ms=_duration_ms, related_id=optimization_id,
                related_type="optimization",
            )

            # 更新优化结果
            optimization.optimization_result = result
            optimization.match_score = result.get("match_score", 0)
            optimization.keyword_coverage = result.get("keyword_coverage", {})
            optimization.suggestions = result.get("suggestions", [])
            optimization.ats_tips = result.get("ats_tips", [])
            optimization.status = "completed"

            # 生成优化后的 DOCX
            docx_path = self._generate_optimized_docx(optimization, result)
            optimization.optimized_docx_path = docx_path

            db.commit()
            db.refresh(optimization)
            logger.info(f"优化任务完成: {optimization_id}, 匹配度: {optimization.match_score}")
            return optimization

        except Exception as e:
            optimization.status = "failed"
            optimization.error_message = str(e)
            db.commit()
            logger.error(f"优化任务失败: {optimization_id}, error={e}")
            raise

    def execute_stream(
        self,
        db: Session,
        optimization_id: str,
    ) -> Generator[str, None, None]:
        """执行优化任务（流式）"""
        optimization = self.get(db, optimization_id)
        if not optimization:
            yield f"data: {json.dumps({'error': '优化任务不存在'})}\n\n"
            return

        # 更新状态
        optimization.status = "processing"
        db.commit()

        try:
            yield f"data: {json.dumps({'status': 'started', 'progress': 0})}\n\n"

            # 获取 JD 和简历
            jd = db.query(JobDescription).filter(
                JobDescription.id == optimization.jd_id
            ).first()
            resume = db.query(Resume).filter(
                Resume.id == optimization.resume_id
            ).first()

            yield f"data: {json.dumps({'status': 'loading_data', 'progress': 10})}\n\n"

            # 获取简历文本
            resume_text = ""
            if resume.parsed_content and "text" in resume.parsed_content:
                resume_text = resume.parsed_content["text"]

            # 获取 LLM 客户端
            client = get_llm_client(optimization.llm_provider)

            yield f"data: {json.dumps({'status': 'analyzing', 'progress': 20, 'message': '正在分析 JD 和简历...'})}\n\n"

            # 构建 prompt
            messages = get_resume_optimize_prompt(
                jd_title=jd.title,
                company_name=jd.company.name if jd.company else "未知公司",
                hard_skills=jd.hard_skills or [],
                soft_skills=jd.soft_skills or [],
                key_keywords=jd.key_keywords or [],
                difficulty_level=jd.difficulty_level or "mid",
                senior_friendly=jd.senior_friendly if jd.senior_friendly is not None else True,
                resume_text=resume_text,
            )

            yield f"data: {json.dumps({'status': 'optimizing', 'progress': 30, 'message': '正在优化简历...'})}\n\n"

            # 流式调用 LLM
            full_response = ""
            for chunk in client.chat_stream(
                messages=messages,
                model=optimization.llm_model,
                temperature=0.5,
                max_tokens=4000,
            ):
                full_response += chunk
                yield f"data: {json.dumps({'status': 'streaming', 'progress': 50, 'content': chunk})}\n\n"

            yield f"data: {json.dumps({'status': 'parsing', 'progress': 80, 'message': '正在解析结果...'})}\n\n"

            # 解析结果（带容错）
            result = parse_json_response(full_response)
            if not result:
                raise ValueError("LLM 返回格式错误")

            # 更新优化结果
            optimization.optimization_result = result
            optimization.match_score = result.get("match_score", 0)
            optimization.keyword_coverage = result.get("keyword_coverage", {})
            optimization.suggestions = result.get("suggestions", [])
            optimization.ats_tips = result.get("ats_tips", [])
            optimization.status = "completed"

            # 生成优化后的 DOCX
            docx_path = self._generate_optimized_docx(optimization, result)
            optimization.optimized_docx_path = docx_path

            db.commit()

            yield f"data: {json.dumps({'status': 'completed', 'progress': 100, 'optimization_id': optimization.id})}\n\n"

        except Exception as e:
            optimization.status = "failed"
            optimization.error_message = str(e)
            db.commit()
            yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"

    def _generate_optimized_docx(
        self,
        optimization: Optimization,
        result: dict,
    ) -> Optional[str]:
        """生成优化后的 DOCX 文件（带降级保护）"""
        try:
            from config import config

            output_dir = Path(config.files.dir) / "optimized"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{optimization.id}_resume.docx"

            jd = optimization.jd
            resume = optimization.resume

            content = {
                "name": resume.name.replace(".docx", ""),
                "optimized_sections": result.get("optimized_sections", {}),
                "suggestions": result.get("suggestions", []),
            }

            docx_writer.create_resume(
                content=content,
                output_path=str(output_path),
            )

            return str(output_path)

        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"DOCX 生成失败（优化结果已保存）: {e}")
            return None

    def to_response(self, optimization: Optimization) -> OptimizationResponse:
        """转换为响应格式"""
        return OptimizationResponse(
            id=optimization.id,
            jd_id=optimization.jd_id,
            resume_id=optimization.resume_id,
            llm_provider=optimization.llm_provider,
            llm_model=optimization.llm_model,
            status=optimization.status,
            match_score=optimization.match_score,
            keyword_coverage=optimization.keyword_coverage,
            optimization_result=optimization.optimization_result,
            suggestions=optimization.suggestions,
            ats_tips=optimization.ats_tips,
            optimized_docx_path=optimization.optimized_docx_path,
            error_message=optimization.error_message,
            created_at=optimization.created_at,
            updated_at=optimization.updated_at,
            jd_title=optimization.jd.title if optimization.jd else None,
            company_name=optimization.jd.company.name if optimization.jd and optimization.jd.company else None,
            resume_name=optimization.resume.name if optimization.resume else None,
            has_interview_guide=optimization.interview_guide is not None,
        )


# 全局实例
optimization_service = OptimizationService()
