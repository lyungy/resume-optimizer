"""
招聘平台基类
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class JobInfo:
    """岗位信息"""
    title: str                           # 职位名称
    company_name: str                    # 公司名称
    company_url: str = ""                # 公司链接
    salary: str = ""                     # 薪资范围
    experience: str = ""                 # 经验要求
    education: str = ""                  # 学历要求
    company_size: str = ""               # 公司规模
    industry: str = ""                   # 行业
    location: str = ""                   # 工作地点
    description: str = ""                # JD 内容
    url: str = ""                        # 详情链接
    platform: str = ""                   # 来源平台
    tags: list[str] = field(default_factory=list)  # 标签
    analysis: Optional[dict] = None      # 分析结果


class BasePlatform(ABC):
    """招聘平台基类"""

    def __init__(self, config: dict):
        self.config = config
        self.name = config.get("name", "unknown")
        self.base_url = config.get("base_url", "")
        self.city_codes = config.get("city_codes", {})
        self.experience_codes = config.get("experience_codes", {})

    @abstractmethod
    async def search(
        self,
        keyword: str,
        city: str,
        experience: str,
        limit: int = 20,
    ) -> list[JobInfo]:
        """
        搜索岗位

        Args:
            keyword: 搜索关键词
            city: 城市名称
            experience: 经验要求
            limit: 最大返回数量

        Returns:
            岗位信息列表
        """
        pass

    @abstractmethod
    async def extract_jd(self, job_url: str) -> str:
        """
        提取 JD 详情

        Args:
            job_url: 岗位详情页 URL

        Returns:
            JD 完整文本
        """
        pass

    def get_city_code(self, city_name: str) -> str:
        """获取城市代码"""
        return self.city_codes.get(city_name, "")

    def get_experience_code(self, experience: str) -> str:
        """获取经验代码"""
        return self.experience_codes.get(experience, "108")

    def is_enabled(self) -> bool:
        """是否启用"""
        return self.config.get("enabled", False)
