"""
简历优化系统导入器
支持两种模式：
  1. direct（默认）：直接调用 backend service（同项目内，高效）
  2. http：通过 REST API 调用（独立运行，解耦）
"""
import asyncio
from typing import Optional
from .platforms.base import JobInfo


class SystemImporter:
    """简历优化系统导入器"""

    def __init__(self, config: dict):
        self.mode = config.get("import_mode", "direct")
        self.api_base = config.get("api_base", "http://localhost:8000/api/v1")
        self.auto_parse = config.get("auto_parse", True)
        self.skip_duplicates = config.get("skip_duplicates", True)
        self.interval = config.get("interval", 1)
        self._company_cache: dict[str, str] = {}  # company_name -> company_id

    async def import_jobs(
        self,
        jobs: list[JobInfo],
        max_count: int = 50,
    ) -> dict:
        """
        批量导入岗位

        Args:
            jobs: 岗位列表
            max_count: 最多导入数量

        Returns:
            导入结果统计
        """
        results = {
            "total": len(jobs),
            "imported": 0,
            "skipped": 0,
            "failed": 0,
            "details": [],
        }

        # 限制数量
        jobs_to_import = jobs[:max_count]

        if self.mode == "direct":
            return await self._import_direct(jobs_to_import, results)
        else:
            return await self._import_http(jobs_to_import, results)

    async def _import_direct(self, jobs: list[JobInfo], results: dict) -> dict:
        """直接调用 backend service（同项目内）"""
        try:
            from backend.services.jd_service import JDService
            from backend.services.company_service import CompanyService
            from backend.models.database import get_db_session
        except ImportError as e:
            print(f"❌ 无法导入 backend service: {e}")
            print("   请确保在项目根目录运行，或使用 --mode http 模式")
            return results

        for i, job in enumerate(jobs):
            print(f"  📥 导入 [{i+1}/{len(jobs)}]: {job.title} - {job.company_name}")

            try:
                async with get_db_session() as session:
                    company_service = CompanyService(session)
                    jd_service = JDService(session)

                    # 检查重复
                    if self.skip_duplicates:
                        existing = await jd_service.find_by_title_and_company(
                            job.title, job.company_name
                        )
                        if existing:
                            print(f"    ⏭️ 跳过（已存在）")
                            results["skipped"] += 1
                            continue

                    # 创建或获取公司
                    company = await company_service.find_or_create(
                        name=job.company_name,
                        industry=job.industry or None,
                        size=job.company_size or None,
                        website=job.company_url or None,
                    )

                    # 创建 JD
                    jd = await jd_service.create(
                        company_id=company.id,
                        title=job.title,
                        raw_text=job.description or f"{job.title}\n{job.salary}\n{job.experience}\n{job.location}",
                        source_url=job.url,
                    )

                    # 自动解析
                    if self.auto_parse:
                        try:
                            await jd_service.parse(jd.id)
                            print(f"    ✅ 已导入并解析")
                        except Exception:
                            print(f"    ✅ 已导入（解析失败）")
                    else:
                        print(f"    ✅ 已导入")

                    results["imported"] += 1
                    results["details"].append({
                        "company_id": company.id,
                        "jd_id": jd.id,
                        "title": job.title,
                        "company": job.company_name,
                    })

                    # 间隔
                    if self.interval > 0 and i < len(jobs) - 1:
                        await asyncio.sleep(self.interval)

            except Exception as e:
                print(f"    ❌ 失败: {e}")
                results["failed"] += 1

        return results

    async def _import_http(self, jobs: list[JobInfo], results: dict) -> dict:
        """通过 REST API 调用（独立运行模式）"""
        import httpx

        async with httpx.AsyncClient(timeout=30) as client:
            for i, job in enumerate(jobs):
                print(f"  📥 导入 [{i+1}/{len(jobs)}]: {job.title} - {job.company_name}")

                try:
                    # 检查重复
                    if self.skip_duplicates:
                        is_dup = await self._check_duplicate_http(client, job)
                        if is_dup:
                            print(f"    ⏭️ 跳过（已存在）")
                            results["skipped"] += 1
                            continue

                    # 导入
                    result = await self._import_single_http(client, job)
                    results["imported"] += 1
                    results["details"].append(result)

                    # 间隔
                    if self.interval > 0 and i < len(jobs) - 1:
                        await asyncio.sleep(self.interval)

                except Exception as e:
                    print(f"    ❌ 失败: {e}")
                    results["failed"] += 1

        return results

    async def _import_single_http(self, client, job: JobInfo) -> dict:
        """通过 HTTP 导入单个岗位"""
        # 1. 创建或获取公司
        company_id = await self._ensure_company_http(client, job)

        # 2. 创建 JD
        jd_data = {
            "company_id": company_id,
            "title": job.title,
            "raw_text": job.description or f"{job.title}\n{job.salary}\n{job.experience}\n{job.location}",
            "source_url": job.url,
        }

        resp = await client.post(f"{self.api_base}/jd", json=jd_data)
        resp.raise_for_status()
        jd = resp.json()

        # 3. 自动解析
        if self.auto_parse and jd.get("id"):
            try:
                await client.post(f"{self.api_base}/jd/{jd['id']}/parse")
                print(f"    ✅ 已导入并解析")
            except Exception:
                print(f"    ✅ 已导入（解析失败）")
        else:
            print(f"    ✅ 已导入")

        return {
            "company_id": company_id,
            "jd_id": jd.get("id"),
            "title": job.title,
            "company": job.company_name,
        }

    async def _ensure_company_http(self, client, job: JobInfo) -> str:
        """通过 HTTP 确保公司存在，返回公司 ID"""
        # 检查缓存
        if job.company_name in self._company_cache:
            return self._company_cache[job.company_name]

        # 查询公司列表
        resp = await client.get(
            f"{self.api_base}/companies",
            params={"keyword": job.company_name, "page_size": 1}
        )
        resp.raise_for_status()
        companies = resp.json().get("items", [])

        # 找到匹配的公司
        for company in companies:
            if company["name"] == job.company_name:
                self._company_cache[job.company_name] = company["id"]
                return company["id"]

        # 创建新公司
        company_data = {
            "name": job.company_name,
            "industry": job.industry or None,
            "size": job.company_size or None,
            "website": job.company_url or None,
        }

        resp = await client.post(f"{self.api_base}/companies", json=company_data)
        resp.raise_for_status()
        company = resp.json()

        self._company_cache[job.company_name] = company["id"]
        return company["id"]

    async def _check_duplicate_http(self, client, job: JobInfo) -> bool:
        """通过 HTTP 检查是否重复"""
        try:
            resp = await client.get(
                f"{self.api_base}/jd",
                params={"keyword": job.title, "page_size": 10}
            )
            resp.raise_for_status()
            jds = resp.json().get("items", [])

            for jd in jds:
                if (jd.get("title") == job.title and
                    jd.get("company_name") == job.company_name):
                    return True

            return False
        except Exception:
            return False
