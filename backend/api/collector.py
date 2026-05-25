"""
Collector API 路由
搜索匹配相关接口
"""
import asyncio
import sys
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.database import get_db
from models import Resume
from schemas.resume import SearchMatchRequest

# 确保项目根目录在 sys.path（支持 collector 模块导入）
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from collector.matcher import JobMatcher

router = APIRouter(prefix="/collector", tags=["岗位采集"])


@router.post("/search-match")
async def search_and_match(
    data: SearchMatchRequest,
    db: Session = Depends(get_db),
):
    """
    基于简历画像搜索并匹配岗位

    流程：
    1. 读取简历画像
    2. 遍历 selected_positions，每个作为关键词搜索
    3. 对每个搜索结果，计算多维匹配分
    4. 按总分排序返回
    """
    # 读取简历
    resume = db.query(Resume).filter(Resume.id == data.resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    profile = resume.profile
    if not profile:
        raise HTTPException(status_code=400, detail="简历未进行职业画像，请先执行职业画像")

    job_preference = resume.job_preference or {}
    if data.salary_min:
        job_preference["salary_min"] = data.salary_min
    if data.salary_max:
        job_preference["salary_max"] = data.salary_max
    if data.city:
        job_preference["city"] = data.city

    # 初始化匹配器
    matcher = JobMatcher(profile, job_preference)

    # 动态导入 collector 模块
    from collector.browser import BrowserController
    from collector.platforms.boss import BossPlatform
    from collector.analyzer import JDAnalyzer
    import yaml

    # 加载 collector 配置
    config_path = Path(__file__).parent.parent.parent / "collector" / "config.yaml"
    if not config_path.exists():
        raise HTTPException(status_code=500, detail="collector 配置文件不存在")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 初始化浏览器
    browser = BrowserController(config.get("browser", {}))
    connected = await browser.connect()
    if not connected:
        raise HTTPException(status_code=500, detail="浏览器启动失败")

    try:
        platform_config = config.get("platforms", {}).get("boss", {})
        platform = BossPlatform(platform_config, browser)
        analyzer = JDAnalyzer(config.get("filter", {}))

        all_jobs = []

        # 遍历选中的岗位关键词
        for i, keyword in enumerate(data.selected_positions):
            try:
                jobs = await platform.search(
                    keyword,
                    data.city,
                    "不限",  # 经验不限，让匹配器自己判断
                    limit=data.limit_per_keyword,
                    is_first=(i == 0),
                )

                # 分析每个岗位
                for job in jobs:
                    job.analysis = analyzer.analyze(job)

                all_jobs.extend(jobs)
            except Exception as e:
                print(f"搜索 {keyword} 失败: {e}")
                continue

        # 去重
        seen_urls = set()
        unique_jobs = []
        for job in all_jobs:
            if job.url and job.url not in seen_urls:
                seen_urls.add(job.url)
                unique_jobs.append(job)

        # 多维匹配打分
        results = []
        for job in unique_jobs:
            job_data = {
                "title": job.title,
                "company_name": job.company_name,
                "salary": job.salary,
                "experience": job.experience,
                "education": job.education,
                "location": job.location,
                "description": job.description,
                "tags": job.tags,
                "url": job.url,
                "platform": job.platform,
                "analysis": {
                    "score": job.analysis.score if job.analysis else 0,
                    "friendly": job.analysis.friendly if job.analysis else False,
                    "age_profile": {
                        "implied_age_min": job.analysis.age_profile.implied_age_min if job.analysis and job.analysis.age_profile else None,
                        "implied_age_max": job.analysis.age_profile.implied_age_max if job.analysis and job.analysis.age_profile else None,
                        "has_explicit_age_limit": job.analysis.age_profile.has_explicit_age_limit if job.analysis and job.analysis.age_profile else False,
                        "age_limit_text": job.analysis.age_profile.age_limit_text if job.analysis and job.analysis.age_profile else "",
                    } if job.analysis and job.analysis.age_profile else None,
                },
            }

            match_result = matcher.match(job_data)
            results.append({
                **job_data,
                **match_result,
            })

        # 按总分排序
        results.sort(key=lambda x: x["total_score"], reverse=True)

        return {
            "total": len(results),
            "jobs": results,
        }

    finally:
        await browser.disconnect()
