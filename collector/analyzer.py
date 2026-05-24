"""
JD 分析器 - 判断大龄友好度
基于职位标题、描述、标签、薪资等多维度信号
核心：通过要求的工作经验年限反推隐含年龄范围
"""
import re
from dataclasses import dataclass, field
from typing import Optional


# 正常大学毕业年龄基准
GRADUATION_AGE = 23


@dataclass
class AgeProfile:
    """年龄画像"""
    implied_age_min: Optional[int] = None    # 反推最小年龄
    implied_age_max: Optional[int] = None    # 反推最大年龄
    age_range_width: Optional[int] = None    # 年龄范围宽度
    has_explicit_age_limit: bool = False     # 是否有明确年龄限制
    age_limit_text: str = ""                 # 年龄限制原文
    age_friendly: bool = True                # 年龄是否友好
    is_unrestricted: bool = False            # 经验不限
    signals: list = field(default_factory=list)  # 信号列表


@dataclass
class AnalysisResult:
    """分析结果"""
    score: int                           # 友好度分数 0-100
    friendly: bool                       # 是否友好
    positive_signals: list[str]          # 正向信号
    negative_signals: list[str]          # 负向信号
    salary_min: Optional[int] = None     # 最低薪资
    salary_max: Optional[int] = None     # 最高薪资
    age_profile: Optional[AgeProfile] = None  # 年龄画像


class JDAnalyzer:
    """JD 分析器"""

    def __init__(self, config: dict):
        self.min_score = config.get("min_score", 60)
        self.positive_signals = config.get("positive_signals", [])
        self.negative_signals = config.get("negative_signals", [])

    def analyze(self, job) -> AnalysisResult:
        """
        分析岗位的大龄友好度
        """
        # 合并分析文本（标题 + 描述 + 经验 + 标签 + 公司名）
        text = " ".join(filter(None, [
            job.title,
            job.description,
            job.experience,
            job.education,
            " ".join(job.tags),
            job.company_name,
            job.salary,
        ]))

        positive_found = []
        negative_found = []

        # 1. 年龄维度分析（核心）—— 通过经验反推年龄
        age_profile = self._analyze_age(job.experience, job.description, job.title, text)
        if age_profile:
            positive_found.extend([s for s in age_profile.signals if not s.startswith("-")])
            negative_found.extend([s[1:] for s in age_profile.signals if s.startswith("-")])

        # 2. 正向信号（配置文件中的）
        for signal in self.positive_signals:
            if signal in text:
                positive_found.append(signal)

        # 3. 负向信号（配置文件中的）
        for signal in self.negative_signals:
            if signal in text:
                negative_found.append(signal)

        # 4. 经验维度分析
        exp_score, exp_signals = self._analyze_experience(job.experience)
        positive_found.extend(exp_signals[0])
        negative_found.extend(exp_signals[1])

        # 5. 薪资维度分析
        salary_min, salary_max = self._parse_salary(job.salary)
        salary_score, salary_signals = self._analyze_salary(salary_min, salary_max)
        positive_found.extend(salary_signals[0])
        negative_found.extend(salary_signals[1])

        # 6. 学历维度分析
        edu_signals = self._analyze_education(job.education)
        positive_found.extend(edu_signals[0])
        negative_found.extend(edu_signals[1])

        # 7. 描述内容分析
        desc_signals = self._analyze_description(job.description)
        positive_found.extend(desc_signals[0])
        negative_found.extend(desc_signals[1])

        # 计算总分（带维度权重）
        score = self._calculate_score(age_profile, positive_found, negative_found,
                                       exp_score, salary_score)

        return AnalysisResult(
            score=score,
            friendly=score >= self.min_score,
            positive_signals=list(set(positive_found)),
            negative_signals=list(set(negative_found)),
            salary_min=salary_min,
            salary_max=salary_max,
            age_profile=age_profile,
        )

    def _analyze_age(self, experience: str, description: str, title: str, full_text: str) -> Optional[AgeProfile]:
        """
        年龄维度分析（核心）
        通过要求的工作经验年限反推隐含年龄范围
        正常大学毕业年龄：22~23岁，取基准23岁
        """
        profile = AgeProfile()

        # === 1. 检测明确的年龄限制（最严重的歧视） ===
        age_limit_patterns = [
            (r'(\d{2})岁以下', 'max'),
            (r'(\d{2})岁以内', 'max'),
            (r'(\d{2})岁\s*[-~]\s*(\d{2})岁', 'range'),
            (r'年龄\s*(\d{2})\s*[-~]\s*(\d{2})', 'range'),
            (r'\b(90|95|00)\s*后\b', 'gen_limit'),
            (r'限\s*(90|95|00)\s*后', 'gen_limit'),
        ]

        for pattern, limit_type in age_limit_patterns:
            match = re.search(pattern, full_text)
            if match:
                profile.has_explicit_age_limit = True
                if limit_type == 'max':
                    max_age = int(match.group(1))
                    profile.age_limit_text = f"{max_age}岁以下"
                    profile.age_friendly = False
                    profile.signals.append(f"-明确年龄上限{max_age}岁")
                elif limit_type == 'range':
                    ages = [int(g) for g in match.groups() if g]
                    profile.age_limit_text = f"{ages[0]}-{ages[1]}岁"
                    profile.age_friendly = ages[1] >= 35
                    if ages[1] < 35:
                        profile.signals.append(f"-年龄限制{ages[0]}-{ages[1]}岁")
                elif limit_type == 'gen_limit':
                    gen = match.group(1)
                    profile.age_limit_text = f"仅限{gen}后"
                    profile.age_friendly = False
                    profile.signals.append(f"-仅限{gen}后")
                break

        # === 2. 通过工作经验反推年龄范围 ===
        if not experience:
            return profile

        # 特殊关键词处理
        exp_lower = experience.lower()
        if '应届' in exp_lower:
            profile.implied_age_min = GRADUATION_AGE
            profile.implied_age_max = GRADUATION_AGE + 1
            profile.age_range_width = 1
            if not profile.has_explicit_age_limit:
                profile.age_friendly = False
                profile.signals.append("-经验要求:应届(仅限22-23岁)")
            return profile

        if '1年以内' in exp_lower:
            profile.implied_age_min = GRADUATION_AGE
            profile.implied_age_max = GRADUATION_AGE + 2
            profile.age_range_width = 2
            if not profile.has_explicit_age_limit:
                profile.age_friendly = False
                profile.signals.append("-经验要求:1年以内(仅限23-25岁)")
            return profile

        if '不限' in exp_lower:
            # 经验不限 → 年龄范围宽，友好
            profile.implied_age_min = 22
            profile.implied_age_max = 50
            profile.age_range_width = 28
            profile.age_friendly = True
            profile.is_unrestricted = True
            profile.signals.append("经验不限→年龄范围宽(22-50岁)")
            return profile

        # 提取经验年数
        nums = re.findall(r'(\d+)', experience)
        if not nums:
            return profile

        if len(nums) >= 2:
            min_exp = int(nums[0])
            max_exp = int(nums[1])
        else:
            min_exp = int(nums[0])
            max_exp = min_exp

        # 反推年龄（以23岁大学毕业为基准）
        profile.implied_age_min = GRADUATION_AGE + min_exp
        profile.implied_age_max = GRADUATION_AGE + max_exp

        # 处理 "X年以上"（只有最小值，无上限）→ 给合理宽度
        if len(nums) == 1 and ('以上' in experience or 'plus' in exp_lower):
            profile.age_range_width = 10  # 无上限，给宽范围
        else:
            profile.age_range_width = max_exp - min_exp

        # === 3. 年龄范围评估 ===
        if not profile.has_explicit_age_limit:
            age_min = profile.implied_age_min
            age_max = profile.implied_age_max
            width = profile.age_range_width

            if max_exp <= 2:
                # 经验1-2年 → 24-25岁，非常窄，对大龄不友好
                profile.age_friendly = False
                profile.signals.append(f"-经验{experience}→隐含年龄{age_min}-{age_max}岁(范围仅{width}年)")
            elif max_exp <= 3:
                # 经验1-3年 → 24-26岁，较窄
                profile.age_friendly = False
                profile.signals.append(f"-经验{experience}→隐含年龄{age_min}-{age_max}岁(范围{width}年)")
            elif min_exp >= 5:
                # 经验5-10年 → 28-33岁，宽范围，友好
                profile.age_friendly = True
                profile.signals.append(f"经验{experience}→隐含年龄{age_min}-{age_max}岁(范围{width}年)")
            elif min_exp >= 3:
                # 经验3-5年 → 26-28岁，中等
                profile.age_friendly = True
                profile.signals.append(f"经验{experience}→隐含年龄{age_min}-{age_max}岁(范围{width}年)")
            else:
                # 其他情况
                profile.age_friendly = width >= 3  # 范围≥3年算友好
                prefix = "" if profile.age_friendly else "-"
                profile.signals.append(f"{prefix}经验{experience}→隐含年龄{age_min}-{age_max}岁(范围{width}年)")

        return profile

    def _analyze_experience(self, experience: str) -> tuple[int, tuple[list, list]]:
        """经验维度分析（补充评分）"""
        score = 0
        positive = []
        negative = []

        if not experience:
            return 0, (positive, negative)

        # 提取数字
        nums = re.findall(r'(\d+)', experience)
        if len(nums) >= 2:
            min_exp = int(nums[0])
            max_exp = int(nums[1])
        elif len(nums) == 1:
            min_exp = int(nums[0])
            max_exp = min_exp
        else:
            return 0, (positive, negative)

        # 5-10年、10年以上 → 正向
        if min_exp >= 5:
            score += 10
            positive.append(f"经验{experience}")
        # 1-3年 → 轻微负向
        elif max_exp <= 3:
            score -= 5
            negative.append(f"经验{experience}")
        # 应届/1年以内 → 负向
        if "应届" in experience or "1年以内" in experience:
            score -= 10
            negative.append("应届/1年以内")

        return score, (positive, negative)

    def _calculate_score(self, age_profile: Optional[AgeProfile],
                         positive: list, negative: list,
                         exp_score: int, salary_score: int) -> int:
        """
        加权计算总分
        权重分配（满分100）：
          年龄维度：40分（核心）
          经验维度：15分
          薪资维度：15分
          正向信号：每项 +3分，上限 +15分
          负向信号：每项 -5分，无下限（截断到0）
        """
        score = 0

        # 1. 年龄维度（40分）—— 核心权重
        if age_profile:
            if age_profile.has_explicit_age_limit:
                # 有明确年龄限制 → 直接扣分
                if not age_profile.age_friendly:
                    score += 0  # 最低分
                else:
                    score += 15
            elif age_profile.implied_age_min is not None:
                age_min = age_profile.implied_age_min
                age_max = age_profile.implied_age_max
                width = age_profile.age_range_width or 0

                # 经验不限 → 特别加分（最友好）
                if age_profile.is_unrestricted:
                    score += 38
                elif age_min >= 30:
                    # 要求30+岁经验 → 非常友好
                    score += 40
                elif age_min >= 28:
                    # 要求5年+ → 友好
                    score += 35
                elif age_min >= 26:
                    # 要求3-5年 → 26-28岁，偏年轻，不算友好
                    score += 18
                elif age_min >= 25:
                    # 要求2年+ → 中等
                    score += 20
                else:
                    # 应届/1年 → 不友好
                    score += 5

                # 范围宽度奖励：越宽越友好
                if width >= 7:
                    score += 5
                elif width >= 5:
                    score += 3
            else:
                # 无经验要求 → 不确定，给中间分
                score += 20

        # 2. 经验维度（15分）
        score += max(-15, min(15, exp_score * 1.5))

        # 3. 薪资维度（15分）
        score += max(-15, min(15, salary_score * 1.5))

        # 4. 正向信号（每项+3，上限+15）
        pos_bonus = min(15, len(positive) * 3)
        score += pos_bonus

        # 5. 负向信号（每项-5，无下限）
        neg_penalty = len(negative) * 5
        score -= neg_penalty

        return max(0, min(100, score))

    def _analyze_salary(self, salary_min: Optional[int], salary_max: Optional[int]) -> tuple[int, tuple[list, list]]:
        """薪资维度分析"""
        positive = []
        negative = []
        score = 0

        if not salary_min or not salary_max:
            return 0, (positive, negative)

        # 高薪（30K+）→ 正向
        if salary_min >= 30000:
            score += 10
            positive.append(f"高薪{salary_min//1000}K+")
        elif salary_min >= 20000:
            score += 5
            positive.append(f"薪资{salary_min//1000}K+")

        # 低薪（10K以下）→ 轻微负向
        if salary_max <= 10000:
            score -= 5
            negative.append(f"低薪{salary_max//1000}K")

        return score, (positive, negative)

    def _analyze_education(self, education: str) -> tuple[list, list]:
        """学历维度分析"""
        positive = []
        negative = []

        if not education:
            return positive, negative

        if "大专" in education or "中专" in education or "高中" in education:
            positive.append("学历要求低")
        elif "硕士" in education or "博士" in education:
            negative.append("高学历要求")

        return positive, negative

    def _analyze_description(self, description: str) -> tuple[list, list]:
        """描述内容分析"""
        positive = []
        negative = []

        if not description:
            return positive, negative

        # 正向关键词
        pos_keywords = [
            "弹性工作", "不加班", "双休", "扁平管理", "技术驱动",
            "团队氛围", "发展空间", "期权", "股票", "年终奖",
            "带薪年假", "补充医疗", "定期体检", "下午茶", "团建",
            "远程办公", "混合办公", "work-life balance",
        ]
        for kw in pos_keywords:
            if kw in description:
                positive.append(kw)

        # 负向关键词
        neg_keywords = [
            "加班", "996", "大小周", "高强度", "抗压能力",
            "出差频繁", "轮班", "夜班", "单休",
        ]
        for kw in neg_keywords:
            if kw in description:
                negative.append(kw)

        return positive, negative

    def _parse_salary(self, salary_str: str) -> tuple[Optional[int], Optional[int]]:
        """解析薪资字符串"""
        if not salary_str:
            return None, None

        # 匹配 "25-40K" 或 "25-40K·15薪"
        match = re.search(r'(\d+)-(\d+)[Kk]', salary_str)
        if match:
            return int(match.group(1)) * 1000, int(match.group(2)) * 1000

        # 匹配 "25000-40000"
        match = re.search(r'(\d{4,})-(\d{4,})', salary_str)
        if match:
            return int(match.group(1)), int(match.group(2))

        return None, None

    def filter_jobs(self, jobs: list, min_score: int = None) -> list:
        """筛选符合条件的岗位"""
        threshold = min_score or self.min_score
        return [job for job in jobs if job.analysis and job.analysis.score >= threshold]
