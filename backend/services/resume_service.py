"""
简历服务层
"""
from __future__ import annotations
import json
import logging
import re
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from models import Resume, ResumeVersion
from schemas import ResumeResponse
from utils import docx_parser
from services.llm import get_llm_client
from services.llm.prompts import get_resume_parse_prompt
from services.llm.prompts.resume_deep_analyzer import get_deep_analyze_prompt
from services.llm.usage_logger import log_llm_usage, timed_llm_call
from config import config

logger = logging.getLogger(__name__)


class ResumeService:
    """简历服务"""

    def _get_upload_dir(self) -> Path:
        """获取上传目录"""
        upload_dir = Path(config.files.dir) / "resumes"
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir

    def upload(self, db: Session, file_name: str, file_content: bytes) -> Resume:
        """上传简历"""
        # 生成文件路径
        upload_dir = self._get_upload_dir()
        import time
        timestamp = int(time.time())
        safe_name = f"{timestamp}_{file_name}"
        file_path = upload_dir / safe_name

        # 保存文件
        with open(file_path, "wb") as f:
            f.write(file_content)
        logger.info(f"简历文件已保存: {file_path}")

        # 解析简历内容（基础解析）
        parsed = docx_parser.parse(str(file_path))

        # 创建数据库记录（基础信息）
        resume = Resume(
            name=file_name,
            original_file_path=str(file_path),
            parsed_content=parsed,
            skills=[],
            experience_years=None,
            is_parsed=False,
        )
        db.add(resume)
        db.flush()

        # 创建初始版本快照
        self._create_snapshot(db, resume, "初始上传")

        db.commit()
        db.refresh(resume)
        logger.info(f"简历记录已创建: {resume.id}")
        return resume

    def parse_with_llm(
        self,
        db: Session,
        resume_id: str,
        llm_provider: Optional[str] = None,
        custom_prompt: Optional[str] = None,
    ) -> Resume:
        """使用 LLM 解析简历"""
        resume = self.get(db, resume_id)
        if not resume:
            raise ValueError(f"简历不存在: {resume_id}")

        # 获取简历文本
        resume_text = ""
        if resume.parsed_content and "text" in resume.parsed_content:
            resume_text = resume.parsed_content["text"]
        else:
            parsed = docx_parser.parse(resume.original_file_path)
            resume_text = parsed["text"]
            resume.parsed_content = parsed

        # 获取 LLM 客户端
        client = get_llm_client(llm_provider)

        # 构建 prompt
        messages = get_resume_parse_prompt(resume_text, custom_system=custom_prompt)

        # 调用 LLM（带计时）
        try:
            response, metadata = timed_llm_call(
                client, messages,
                model=None, temperature=0.3, max_tokens=4000,
            )
        except Exception as e:
            log_llm_usage(
                db, feature="智能解析", llm_provider=client.provider.name,
                llm_model=client.default_model, system_prompt=messages[0]["content"],
                user_prompt=messages[1]["content"] if len(messages) > 1 else None,
                status="failed", error_message=str(e),
                related_id=resume_id, related_type="resume",
            )
            raise ValueError(f"LLM 调用失败: {str(e)}")

        # 解析结果
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                log_llm_usage(
                    db, feature="智能解析", llm_provider=client.provider.name,
                    llm_model=client.default_model, system_prompt=messages[0]["content"],
                    user_prompt=messages[1]["content"] if len(messages) > 1 else None,
                    raw_response=response, status="failed",
                    error_message="JSON 解析失败", related_id=resume_id, related_type="resume",
                    **metadata,
                )
                raise ValueError(f"LLM 返回格式错误: {response[:200]}")

        # 记录成功日志
        log_llm_usage(
            db, feature="智能解析", llm_provider=client.provider.name,
            llm_model=client.default_model, system_prompt=messages[0]["content"],
            user_prompt=messages[1]["content"] if len(messages) > 1 else None,
            raw_response=response, parsed_result=result,
            related_id=resume_id, related_type="resume",
            **metadata,
        )

        # 更新简历（保留已有数据，合并新数据）
        resume.skills = result.get("skills", []) or resume.skills
        resume.experience_years = result.get("experience_years") or resume.experience_years
        resume.education = result.get("education") or resume.education
        resume.work_experience = result.get("work_experience", []) or resume.work_experience
        resume.projects = result.get("projects", []) or resume.projects
        resume.is_parsed = True

        # 更新 parsed_content 中加入 LLM 解析结果
        resume.parsed_content["llm_parsed"] = result

        # 创建版本快照
        self._create_snapshot(db, resume, "智能解析")

        db.commit()
        db.refresh(resume)
        return resume

    def deep_analyze(
        self,
        db: Session,
        resume_id: str,
        llm_provider: Optional[str] = None,
        custom_prompt: Optional[str] = None,
    ) -> dict:
        """职业画像分析，提取求职画像+推荐岗位"""
        resume = self.get(db, resume_id)
        if not resume:
            raise ValueError(f"简历不存在: {resume_id}")

        # 获取简历文本
        resume_text = ""
        if resume.parsed_content and "text" in resume.parsed_content:
            resume_text = resume.parsed_content["text"]
        else:
            parsed = docx_parser.parse(resume.original_file_path)
            resume_text = parsed["text"]
            resume.parsed_content = parsed

        # 获取 LLM 客户端
        client = get_llm_client(llm_provider)

        # 构建 prompt
        messages = get_deep_analyze_prompt(resume_text, custom_system=custom_prompt)

        # 调用 LLM（带计时）
        try:
            response, metadata = timed_llm_call(
                client, messages,
                model=None, temperature=0.3, max_tokens=6000,
            )
        except Exception as e:
            log_llm_usage(
                db, feature="职业画像", llm_provider=client.provider.name,
                llm_model=client.default_model, system_prompt=messages[0]["content"],
                user_prompt=messages[1]["content"] if len(messages) > 1 else None,
                status="failed", error_message=str(e),
                related_id=resume_id, related_type="resume",
            )
            raise ValueError(f"LLM 调用失败: {str(e)}")

        # 解析结果
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                log_llm_usage(
                    db, feature="职业画像", llm_provider=client.provider.name,
                    llm_model=client.default_model, system_prompt=messages[0]["content"],
                    user_prompt=messages[1]["content"] if len(messages) > 1 else None,
                    raw_response=response, status="failed",
                    error_message="JSON 解析失败", related_id=resume_id, related_type="resume",
                    **metadata,
                )
                raise ValueError(f"LLM 返回格式错误: {response[:200]}")

        # 记录成功日志
        log_llm_usage(
            db, feature="职业画像", llm_provider=client.provider.name,
            llm_model=client.default_model, system_prompt=messages[0]["content"],
            user_prompt=messages[1]["content"] if len(messages) > 1 else None,
            raw_response=response, parsed_result=result,
            related_id=resume_id, related_type="resume",
            **metadata,
        )

        profile = result.get("profile", {})
        recommended = result.get("recommended_positions", [])

        # 推导搜索关键词
        search_keywords = []
        for pos in recommended:
            if pos.get("title") and pos["title"] not in search_keywords:
                search_keywords.append(pos["title"])

        # 保存到简历
        resume.profile = profile
        resume.recommended_positions = recommended

        # 创建版本快照
        self._create_snapshot(db, resume, "职业画像")

        db.commit()
        db.refresh(resume)

        return {
            "profile": profile,
            "recommended_positions": recommended,
            "search_keywords": search_keywords,
        }

    def update_profile(
        self,
        db: Session,
        resume_id: str,
        profile: Optional[dict] = None,
        recommended_positions: Optional[list] = None,
        job_preference: Optional[dict] = None,
    ) -> Resume:
        """更新求职画像（用户编辑后保存）"""
        resume = self.get(db, resume_id)
        if not resume:
            raise ValueError(f"简历不存在: {resume_id}")

        if profile is not None:
            resume.profile = profile
        if recommended_positions is not None:
            resume.recommended_positions = recommended_positions
        if job_preference is not None:
            resume.job_preference = job_preference

        # 创建手动编辑版本快照
        self._create_snapshot(db, resume, "手动编辑")

        db.commit()
        db.refresh(resume)
        return resume

    def _create_snapshot(self, db: Session, resume: Resume, label: str) -> ResumeVersion:
        """创建简历版本快照"""
        # 获取当前最大版本号
        max_version = db.query(ResumeVersion.version_no).filter(
            ResumeVersion.resume_id == resume.id
        ).order_by(ResumeVersion.version_no.desc()).first()
        version_no = (max_version[0] + 1) if max_version else 1

        snapshot = ResumeVersion(
            resume_id=resume.id,
            version_no=version_no,
            label=label,
            skills=resume.skills,
            experience_years=resume.experience_years,
            education=resume.education,
            work_experience=resume.work_experience,
            projects=resume.projects,
            profile=resume.profile,
            recommended_positions=resume.recommended_positions,
            parsed_content=resume.parsed_content,
        )
        db.add(snapshot)
        logger.info(f"创建简历版本快照: {resume.id} v{version_no} ({label})")
        return snapshot

    def get(self, db: Session, resume_id: str) -> Optional[Resume]:
        """获取简历"""
        return db.query(Resume).filter(Resume.id == resume_id).first()

    def list(
        self,
        db: Session,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Resume], int]:
        """获取简历列表"""
        query = db.query(Resume)

        if keyword:
            query = query.filter(Resume.name.contains(keyword))

        total = query.count()
        items = query.order_by(Resume.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total

    def delete(self, db: Session, resume_id: str) -> bool:
        """删除简历"""
        resume = self.get(db, resume_id)
        if not resume:
            return False

        # 删除文件
        file_path = Path(resume.original_file_path)
        if file_path.exists():
            file_path.unlink()

        db.delete(resume)
        db.commit()
        return True

    def get_text_content(self, db: Session, resume_id: str) -> str:
        """获取简历的纯文本内容"""
        resume = self.get(db, resume_id)
        if not resume:
            raise ValueError(f"简历不存在: {resume_id}")

        if resume.parsed_content and "text" in resume.parsed_content:
            return resume.parsed_content["text"]

        parsed = docx_parser.parse(resume.original_file_path)
        return parsed["text"]

    def to_response(self, resume: Resume) -> ResumeResponse:
        """转换为响应格式"""
        return ResumeResponse(
            id=resume.id,
            name=resume.name,
            original_file_path=resume.original_file_path,
            is_parsed=resume.is_parsed,
            parsed_content=resume.parsed_content,
            skills=resume.skills,
            experience_years=resume.experience_years,
            education=resume.education,
            work_experience=resume.work_experience,
            projects=resume.projects,
            profile=resume.profile,
            recommended_positions=resume.recommended_positions,
            job_preference=resume.job_preference,
            created_at=resume.created_at,
            updated_at=resume.updated_at,
        )


# 全局实例
resume_service = ResumeService()
