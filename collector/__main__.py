"""
Collector CLI 入口
用法：python -m collector search -k "架构师" -c 上海
"""
import argparse
import asyncio
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中（支持 from backend.xxx import）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import yaml
from collector.browser import BrowserController
from collector.platforms.boss import BossPlatform
from collector.analyzer import JDAnalyzer, AnalysisResult, AgeProfile
from collector.importer import SystemImporter
from collector.utils import (
    SearchHistory, print_table, print_import_results,
    load_json, save_json,
)
from collector.platforms.base import JobInfo

# 模块目录
MODULE_DIR = Path(__file__).resolve().parent


def load_config() -> dict:
    """加载配置文件"""
    config_path = MODULE_DIR / "config.yaml"
    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_platform(name: str, config: dict, browser) -> object:
    """获取平台实例"""
    platform_config = config.get("platforms", {}).get(name, {})
    if not platform_config:
        print(f"❌ 未找到平台配置: {name}")
        sys.exit(1)
    if not platform_config.get("enabled"):
        print(f"❌ 平台未启用: {name}")
        sys.exit(1)

    if name == "boss":
        return BossPlatform(platform_config, browser)
    else:
        print(f"❌ 暂不支持平台: {name}")
        sys.exit(1)


async def cmd_search(args, config: dict):
    """搜索岗位"""
    # 解析参数
    keywords = args.keyword or config["search"]["keywords"]
    city = args.city or config["search"]["cities"][0]
    platform_name = args.platform or "boss"
    limit = args.limit or config["search"]["limit"]
    min_score = args.min_score or config["filter"]["min_score"]
    max_import = args.max_import or config["import"]["max_count"]
    do_import = args.import_flag
    fetch_detail = args.detail or config.get("detail", {}).get("enabled", False)

    print(f"🔍 搜索条件：{'、'.join(keywords)} | {city} | {platform_name}")
    print(f"   最低分数: {min_score} | 最大搜索: {limit} | 最大导入: {max_import}")

    # 连接浏览器
    browser = BrowserController(config.get("browser", {}))
    connected = await browser.connect()
    if not connected:
        return

    try:
        # 初始化平台
        platform = get_platform(platform_name, config, browser)

        # 初始化分析器
        analyzer = JDAnalyzer(config.get("filter", {}))

        # 初始化历史
        history_file = str(MODULE_DIR / config["history"]["file"])
        history = SearchHistory(history_file, config["history"]["max_age_days"])

        # 搜索岗位
        all_jobs = []
        for i, keyword in enumerate(keywords):
            print(f"\n🔎 搜索: {keyword}")
            jobs = await platform.search(
                keyword, city, config["search"]["experience"],
                limit, fetch_detail=fetch_detail,
                is_first=(i == 0),
            )
            print(f"  📊 找到 {len(jobs)} 个岗位")
            all_jobs.extend(jobs)

        # 去重（基于 URL）
        seen_urls = set()
        unique_jobs = []
        for job in all_jobs:
            if job.url and job.url not in seen_urls:
                seen_urls.add(job.url)
                unique_jobs.append(job)
            elif not job.url:
                unique_jobs.append(job)

        print(f"\n📊 去重后: {len(unique_jobs)} 个岗位")

        # 分析筛选
        for job in unique_jobs:
            job.analysis = analyzer.analyze(job)

        # 按分数排序
        unique_jobs.sort(key=lambda j: j.analysis.score if j.analysis else 0, reverse=True)

        # 打印结果
        print(f"\n📋 岗位列表:")
        print_table(unique_jobs)

        # 筛选符合条件的
        filtered = [j for j in unique_jobs if j.analysis and j.analysis.friendly]
        print(f"\n✅ 符合条件: {len(filtered)} 个岗位")

        # 导入系统
        if do_import and filtered:
            print(f"\n📥 开始导入简历优化系统...")
            importer = SystemImporter({
                **config.get("resume_optimizer", {}),
                **config.get("import", {}),
            })
            results = await importer.import_jobs(filtered, max_import)
            print_import_results(results)

            # 记录历史
            for keyword in keywords:
                history.add_search(keyword, city, platform_name, len(filtered))

        # 保存搜索结果到文件（完整数据）
        output_file = str(MODULE_DIR / "data" / "latest_search.json")
        jobs_data = []
        for j in unique_jobs:
            ap = j.analysis.age_profile if j.analysis else None
            jobs_data.append({
                "title": j.title,
                "company_name": j.company_name,
                "company_url": j.company_url,
                "salary": j.salary,
                "experience": j.experience,
                "education": j.education,
                "company_size": j.company_size,
                "industry": j.industry,
                "location": j.location,
                "url": j.url,
                "platform": j.platform,
                "tags": j.tags,
                "description": j.description,
                "analysis": {
                    "score": j.analysis.score if j.analysis else 0,
                    "friendly": j.analysis.friendly if j.analysis else False,
                    "positive_signals": j.analysis.positive_signals if j.analysis else [],
                    "negative_signals": j.analysis.negative_signals if j.analysis else [],
                    "salary_min": j.analysis.salary_min if j.analysis else None,
                    "salary_max": j.analysis.salary_max if j.analysis else None,
                    "age_profile": {
                        "implied_age_min": ap.implied_age_min if ap else None,
                        "implied_age_max": ap.implied_age_max if ap else None,
                        "age_range_width": ap.age_range_width if ap else None,
                        "has_explicit_age_limit": ap.has_explicit_age_limit if ap else False,
                        "age_limit_text": ap.age_limit_text if ap else "",
                        "age_friendly": ap.age_friendly if ap else True,
                        "is_unrestricted": ap.is_unrestricted if ap else False,
                    } if ap else None,
                } if j.analysis else None,
            })
        save_json(output_file, {
            "keywords": keywords,
            "city": city,
            "platform": platform_name,
            "total": len(unique_jobs),
            "filtered": len(filtered),
            "jobs": jobs_data,
        })
        print(f"\n💾 搜索结果已保存: {output_file}")

        # --await 模式：保持浏览器打开，等待用户手动关闭
        if args.await_browser:
            print(f"\n✅ 搜索完成，浏览器保持打开中")
            print(f"   可在浏览器中继续查看结果")
            print(f"   按 Enter 关闭浏览器（5分钟无操作自动关闭）...")
            try:
                await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, input),
                    timeout=300,
                )
            except asyncio.TimeoutError:
                print("\n⏰ 超时，自动关闭浏览器")

    finally:
        await browser.disconnect()


async def cmd_import(args, config: dict):
    """导入岗位"""
    max_count = args.max or config["import"]["max_count"]

    # 加载最新搜索结果
    result_file = str(MODULE_DIR / "data" / "latest_search.json")
    if not Path(result_file).exists():
        print("❌ 未找到搜索结果，请先执行搜索")
        return

    data = load_json(result_file)
    jobs_data = data.get("jobs", [])

    # 筛选友好的岗位
    friendly_jobs = [j for j in jobs_data if j.get("analysis", {}).get("friendly", j.get("friendly", False))]
    print(f"📊 找到 {len(friendly_jobs)} 个符合条件的岗位")

    if not friendly_jobs:
        print("暂无需要导入的岗位")
        return

    # 转换为 JobInfo（完整数据）
    jobs = []
    for j in friendly_jobs[:max_count]:
        job = JobInfo(
            title=j["title"],
            company_name=j.get("company_name", j.get("company", "")),
            company_url=j.get("company_url", ""),
            salary=j.get("salary", ""),
            experience=j.get("experience", ""),
            education=j.get("education", ""),
            company_size=j.get("company_size", ""),
            industry=j.get("industry", ""),
            location=j.get("location", ""),
            url=j.get("url", ""),
            platform=j.get("platform", "boss"),
            tags=j.get("tags", []),
            description=j.get("description", ""),
        )
        # 恢复分析结果
        analysis_data = j.get("analysis")
        if analysis_data:
            ap_data = analysis_data.get("age_profile")
            age_profile = AgeProfile(
                implied_age_min=ap_data.get("implied_age_min"),
                implied_age_max=ap_data.get("implied_age_max"),
                age_range_width=ap_data.get("age_range_width"),
                has_explicit_age_limit=ap_data.get("has_explicit_age_limit", False),
                age_limit_text=ap_data.get("age_limit_text", ""),
                age_friendly=ap_data.get("age_friendly", True),
                is_unrestricted=ap_data.get("is_unrestricted", False),
            ) if ap_data else None
            job.analysis = AnalysisResult(
                score=analysis_data.get("score", 0),
                friendly=analysis_data.get("friendly", False),
                positive_signals=analysis_data.get("positive_signals", []),
                negative_signals=analysis_data.get("negative_signals", []),
                salary_min=analysis_data.get("salary_min"),
                salary_max=analysis_data.get("salary_max"),
                age_profile=age_profile,
            )
        jobs.append(job)

    # 导入
    importer = SystemImporter({
        **config.get("resume_optimizer", {}),
        **config.get("import", {}),
    })
    results = await importer.import_jobs(jobs, max_count)
    print_import_results(results)


def cmd_history(args, config: dict):
    """查看搜索历史"""
    history_file = str(MODULE_DIR / config["history"]["file"])
    history = SearchHistory(history_file)

    searches = history.get_searches()
    if not searches:
        print("暂无搜索历史")
        return

    print("📜 搜索历史:")
    for i, s in enumerate(searches[-10:], 1):  # 显示最近10条
        print(f"  {i}. {s['keyword']} | {s['city']} | {s['platform']} | {s['count']}个 | {s['timestamp'][:16]}")


def cmd_clear_history(args, config: dict):
    """清空搜索历史"""
    history_file = str(MODULE_DIR / config["history"]["file"])
    history = SearchHistory(history_file)
    history.clear()
    print("✅ 搜索历史已清空")


def cmd_open_browser(args, config: dict):
    """打开浏览器（有头模式，手动操作用）"""
    browser_config = config.get("browser", {})
    browser_config["headless"] = False

    async def _open():
        browser = BrowserController(browser_config)
        connected = await browser.connect()
        if not connected:
            print("❌ 浏览器启动失败")
            return

        url = "https://www.zhipin.com/web/geek/job"
        await browser.open_page(url)
        print("✅ 浏览器已打开，登录态已保留，可以手动操作")
        print("   按 Ctrl+C 退出")

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n关闭中...")
            await browser.disconnect()
            print("✅ 已关闭")

    asyncio.run(_open())


def main():
    parser = argparse.ArgumentParser(
        description="Collector - 求职岗位自动采集模块",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # search 子命令
    search_parser = subparsers.add_parser("search", help="搜索岗位")
    search_parser.add_argument("-k", "--keyword", action="append", help="搜索关键词（可多次指定）")
    search_parser.add_argument("-c", "--city", help="城市名称")
    search_parser.add_argument("-p", "--platform", help="平台（boss/lagou/liepin）")
    search_parser.add_argument("-i", "--import", dest="import_flag", action="store_true", help="搜索后自动导入")
    search_parser.add_argument("-l", "--limit", type=int, help="最大搜索数量")
    search_parser.add_argument("-s", "--min-score", type=int, help="最低友好度分数")
    search_parser.add_argument("-m", "--max-import", type=int, help="最多导入数量")
    search_parser.add_argument("--detail", action="store_true", help="抓取详情页 JD（较慢，建议调试时使用）")
    search_parser.add_argument("--await", dest="await_browser", action="store_true", help="采集完成后保持浏览器打开，等待用户手动关闭")

    # import 子命令
    import_parser = subparsers.add_parser("import", help="导入岗位")
    import_parser.add_argument("-m", "--max", type=int, help="最多导入数量")

    # history 子命令
    subparsers.add_parser("history", help="查看搜索历史")

    # clear-history 子命令
    subparsers.add_parser("clear-history", help="清空搜索历史")

    # open-browser 子命令
    subparsers.add_parser("open-browser", help="打开浏览器（手动登录/操作）")

    # clean-jd 子命令
    clean_parser = subparsers.add_parser("clean-jd", help="清洗数据库 JD 文本")
    clean_parser.add_argument("--db", help="数据库路径（默认项目 data/db/）")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 加载配置
    config = load_config()

    # 执行命令
    if args.command == "search":
        asyncio.run(cmd_search(args, config))
    elif args.command == "import":
        asyncio.run(cmd_import(args, config))
    elif args.command == "history":
        cmd_history(args, config)
    elif args.command == "clear-history":
        cmd_clear_history(args, config)
    elif args.command == "open-browser":
        cmd_open_browser(args, config)
    elif args.command == "clean-jd":
        from collector.clean_jd import clean_database
        clean_database(args.db)


if __name__ == "__main__":
    main()
