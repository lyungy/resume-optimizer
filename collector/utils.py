"""
工具函数
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional


def load_json(file_path: str, default=None) -> dict:
    """加载 JSON 文件"""
    path = Path(file_path)
    if not path.exists():
        return default or {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(file_path: str, data: dict):
    """保存 JSON 文件"""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def format_salary(salary_min: Optional[int], salary_max: Optional[int]) -> str:
    """格式化薪资"""
    if salary_min and salary_max:
        if salary_min >= 1000:
            return f"{salary_min//1000}-{salary_max//1000}K"
        return f"{salary_min}-{salary_max}"
    return "-"


def format_score(score: int) -> str:
    """格式化分数"""
    if score >= 80:
        return f"🟢 {score}分"
    elif score >= 60:
        return f"🟡 {score}分"
    else:
        return f"🔴 {score}分"


def truncate(text: str, max_len: int = 20) -> str:
    """截断文本"""
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len-2] + "..."


def print_table(jobs: list):
    """打印岗位表格"""
    if not jobs:
        print("  暂无数据")
        return

    # 表头
    print(f"  {'#':<4} {'职位':<20} {'公司':<16} {'薪资':<12} {'友好度':<10} {'年龄画像':<18} {'状态'}")
    print(f"  {'─'*4} {'─'*20} {'─'*16} {'─'*12} {'─'*10} {'─'*18} {'─'*8}")

    # 数据行
    for i, job in enumerate(jobs, 1):
        title = truncate(job.title, 18)
        company = truncate(job.company_name, 14)
        salary = job.salary or "-"
        score = format_score(job.analysis.score) if job.analysis else "-"
        status = "✅" if job.analysis and job.analysis.friendly else "❌"

        # 年龄画像
        age_str = "-"
        if job.analysis and job.analysis.age_profile:
            ap = job.analysis.age_profile
            if ap.has_explicit_age_limit:
                age_str = f"⚠️ {ap.age_limit_text}"
            elif ap.implied_age_min is not None:
                age_icon = "👤" if ap.age_friendly else "⚠️"
                age_str = f"{age_icon} {ap.implied_age_min}-{ap.implied_age_max}岁"

        print(f"  {i:<4} {title:<20} {company:<16} {salary:<12} {score:<10} {age_str:<18} {status}")


def print_import_results(results: dict):
    """打印导入结果"""
    print(f"\n📊 导入结果:")
    print(f"  总数: {results['total']}")
    print(f"  成功: {results['imported']}")
    print(f"  跳过: {results['skipped']}")
    print(f"  失败: {results['failed']}")


class SearchHistory:
    """搜索历史管理"""

    def __init__(self, file_path: str, max_age_days: int = 30):
        self.file_path = file_path
        self.max_age_days = max_age_days
        self.data = load_json(file_path, {"searches": [], "imported_urls": []})

    def add_search(self, keyword: str, city: str, platform: str, count: int):
        """记录搜索"""
        self.data["searches"].append({
            "keyword": keyword,
            "city": city,
            "platform": platform,
            "count": count,
            "timestamp": datetime.now().isoformat(),
        })
        self._cleanup()
        self._save()

    def add_imported(self, url: str):
        """记录已导入的 URL"""
        if url and url not in self.data["imported_urls"]:
            self.data["imported_urls"].append(url)
            self._save()

    def is_imported(self, url: str) -> bool:
        """检查是否已导入"""
        return url in self.data.get("imported_urls", [])

    def get_searches(self) -> list:
        """获取搜索历史"""
        return self.data.get("searches", [])

    def clear(self):
        """清空历史"""
        self.data = {"searches": [], "imported_urls": []}
        self._save()

    def _cleanup(self):
        """清理过期记录"""
        cutoff = datetime.now() - timedelta(days=self.max_age_days)
        self.data["searches"] = [
            s for s in self.data["searches"]
            if datetime.fromisoformat(s["timestamp"]) > cutoff
        ]

    def _save(self):
        """保存"""
        save_json(self.file_path, self.data)
