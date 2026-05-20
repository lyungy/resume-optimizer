"""
简历服务层
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from models import Resume
from schemas import ResumeResponse
from utils import docx_parser
from services.llm import get_llm_client
from services.llm.prompts import get_resume_parse_prompt
from config import config


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
        db.commit()
        db.refresh(resume)
        return resume

    def parse_with_llm(
        self,
        db: Session,
        resume_id: str,
        llm_provider: Optional[str] = None,
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
        messages = get_resume_parse_prompt(resume_text)

        # 调用 LLM
        try:
            response = client.chat_json(
                messages=messages,
                temperature=0.3,
                max_tokens=4000,
            )
        except Exception as e:
            raise ValueError(f"LLM 调用失败: {str(e)}")

        # 解析结果
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                raise ValueError(f"LLM 返回格式错误: {response[:200]}")

        # 更新简历（保留已有数据，合并新数据）
        resume.skills = result.get("skills", []) or resume.skills
        resume.experience_years = result.get("experience_years") or resume.experience_years
        resume.education = result.get("education") or resume.education
        resume.work_experience = result.get("work_experience", []) or resume.work_experience
        resume.projects = result.get("projects", []) or resume.projects
        resume.is_parsed = True

        # 更新 parsed_content 中加入 LLM 解析结果
        resume.parsed_content["llm_parsed"] = result

        db.commit()
        db.refresh(resume)
        return resume

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
            created_at=resume.created_at,
            updated_at=resume.updated_at,
        )


# 全局实例
resume_service = ResumeService()
