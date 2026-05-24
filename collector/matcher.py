"""
多维匹配引擎
简历维度 × 岗位维度 → 匹配度计算
"""
import re
from typing import Optional


class JobMatcher:
    """岗位匹配器"""

    # 权重分配
    WEIGHTS = {
        "skill_match": 0.35,
        "experience_match": 0.20,
        "salary_match": 0.15,
        "title_match": 0.15,
        "age_friendly": 0.10,
        "industry_match": 0.05,
    }

    def __init__(self, profile: dict, job_preference: dict = None):
        """
        Args:
            profile: 求职画像（来自深度解析）
            job_preference: 用户求职偏好
        """
        self.profile = profile
        self.preference = job_preference or {}

        # 提取技能集合（扁平化）
        self.my_skills = set()
        hard_skills = profile.get("hard_skills", {})
        for category in hard_skills.values():
            if isinstance(category, list):
                self.my_skills.update(s.lower() for s in category)

        # 提取软技能
        soft_skills = profile.get("soft_skills", [])
        self.my_skills.update(s.lower() for s in soft_skills)

        # 经验画像
        self.exp_profile = profile.get("experience_profile", {})
        self.my_years = self.exp_profile.get("total_years", 0)
        self.my_titles = set()
        if self.exp_profile.get("highest_title"):
            self.my_titles.add(self.exp_profile["highest_title"].lower())
        # 从工作经历中提取历史职位
        for work in profile.get("work_experience", []):
            if isinstance(work, dict) and work.get("title"):
                self.my_titles.add(work["title"].lower())

        # 行业经验
        self.my_industries = set(
            i.lower() for i in self.exp_profile.get("industries", [])
        )

        # 求职偏好
        self.salary_min = self.preference.get("salary_min")
        self.salary_max = self.preference.get("salary_max")

    def match(self, job_data: dict) -> dict:
        """
        计算单个岗位的匹配度

        Args:
            job_data: 岗位数据（来自采集结果）
                {
                    "title": "架构师",
                    "company_name": "XX公司",
                    "salary": "30-50K",
                    "experience": "5-10年",
                    "education": "本科",
                    "location": "上海",
                    "description": "...",
                    "tags": [...],
                    "analysis": {...}  # 来自 analyzer 的分析结果
                }

        Returns:
            匹配结果字典
        """
        # 合并分析文本
        text = " ".join(filter(None, [
            job_data.get("title", ""),
            job_data.get("description", ""),
            " ".join(job_data.get("tags", [])),
        ])).lower()

        # 各维度打分
        skill_result = self._match_skills(text, job_data)
        exp_result = self._match_experience(job_data)
        salary_result = self._match_salary(job_data)
        title_result = self._match_title(job_data)
        age_result = self._match_age(job_data)
        industry_result = self._match_industry(text)

        # 加权总分
        total_score = (
            skill_result["score"] * self.WEIGHTS["skill_match"]
            + exp_result["score"] * self.WEIGHTS["experience_match"]
            + salary_result["score"] * self.WEIGHTS["salary_match"]
            + title_result["score"] * self.WEIGHTS["title_match"]
            + age_result["score"] * self.WEIGHTS["age_friendly"]
            + industry_result["score"] * self.WEIGHTS["industry_match"]
        )

        # 推荐等级
        if total_score >= 80:
            recommendation = "强烈推荐"
        elif total_score >= 65:
            recommendation = "推荐"
        elif total_score >= 50:
            recommendation = "可以考虑"
        else:
            recommendation = "不太匹配"

        # 汇总理由和差距
        reasons = []
        gaps = []
        for r in [skill_result, exp_result, salary_result, title_result, age_result, industry_result]:
            reasons.extend(r.get("reasons", []))
            gaps.extend(r.get("gaps", []))

        return {
            "total_score": round(total_score),
            "dimension_scores": {
                "skill_match": skill_result,
                "experience_match": exp_result,
                "salary_match": salary_result,
                "title_match": title_result,
                "age_friendly": age_result,
                "industry_match": industry_result,
            },
            "recommendation": recommendation,
            "reasons": reasons[:5],  # 最多5条理由
            "gaps": gaps[:3],  # 最多3条差距
        }

    def _match_skills(self, text: str, job_data: dict) -> dict:
        """技能匹配（0-100）"""
        # 从 JD 中提取技能关键词
        jd_skills = set()
        for skill in self.my_skills:
            # 用简历中的技能去匹配 JD 文本
            if skill in text:
                jd_skills.add(skill)

        if not self.my_skills:
            return {"score": 50, "rate": 0, "matched": [], "missing": [], "reasons": ["无技能数据"], "gaps": []}

        # 计算匹配率：我的技能中有多少在 JD 中出现
        matched = jd_skills
        match_rate = len(matched) / len(self.my_skills) * 100 if self.my_skills else 0

        # 评分
        if match_rate >= 60:
            score = 100
        elif match_rate >= 40:
            score = 80
        elif match_rate >= 25:
            score = 60
        elif match_rate >= 10:
            score = 40
        else:
            score = 20

        reasons = []
        gaps = []
        if matched:
            reasons.append(f"技能匹配率{match_rate:.0f}%：{', '.join(list(matched)[:5])}")
        if len(matched) < 3:
            gaps.append("技能匹配度较低，JD要求的技能栈与你的经验重合度不高")

        return {
            "score": score,
            "rate": round(match_rate),
            "matched": list(matched)[:10],
            "missing": [],
            "reasons": reasons,
            "gaps": gaps,
        }

    def _match_experience(self, job_data: dict) -> dict:
        """经验匹配（0-100）"""
        exp_str = job_data.get("experience", "")
        if not exp_str or not self.my_years:
            return {"score": 50, "detail": "无经验数据", "reasons": [], "gaps": []}

        # 提取 JD 要求的经验范围
        nums = re.findall(r'(\d+)', exp_str)
        if not nums:
            return {"score": 50, "detail": f"JD要求: {exp_str}", "reasons": [], "gaps": []}

        jd_min = int(nums[0])
        jd_max = int(nums[1]) if len(nums) >= 2 else jd_min + 5

        reasons = []
        gaps = []

        if self.my_years >= jd_min and self.my_years <= jd_max:
            # 完美匹配
            score = 100
            detail = f"{self.my_years}年经验完美匹配JD要求{exp_str}"
            reasons.append(detail)
        elif self.my_years > jd_max:
            # 超出上限
            over = self.my_years - jd_max
            if over <= 3:
                score = 80
                detail = f"{self.my_years}年经验略超JD要求{exp_str}，可接受"
                reasons.append(detail)
            elif over <= 7:
                score = 60
                detail = f"{self.my_years}年经验超出JD要求{exp_str}，可能被认为太资深"
                gaps.append("经验超出岗位要求较多")
            else:
                score = 40
                detail = f"{self.my_years}年经验远超JD要求{exp_str}"
                gaps.append("经验远超岗位要求")
        elif self.my_years >= jd_min - 2:
            # 接近下限
            score = 70
            detail = f"{self.my_years}年经验接近JD要求{exp_str}"
            reasons.append(detail)
        else:
            # 不足
            score = 30
            detail = f"{self.my_years}年经验不足JD要求{exp_str}"
            gaps.append(f"经验不足，JD要求{exp_str}，你有{self.my_years}年")

        return {"score": score, "detail": detail, "reasons": reasons, "gaps": gaps}

    def _match_salary(self, job_data: dict) -> dict:
        """薪资匹配（0-100）"""
        salary_str = job_data.get("salary", "")
        if not salary_str:
            return {"score": 50, "detail": "无薪资数据", "reasons": [], "gaps": []}

        # 解析 JD 薪资
        match = re.search(r'(\d+)-(\d+)[Kk]', salary_str)
        if not match:
            return {"score": 50, "detail": f"薪资: {salary_str}", "reasons": [], "gaps": []}

        jd_min = int(match.group(1)) * 1000
        jd_max = int(match.group(2)) * 1000

        reasons = []
        gaps = []

        if not self.salary_min or not self.salary_max:
            return {"score": 50, "detail": f"JD薪资: {salary_str}", "reasons": [], "gaps": []}

        # 匹配逻辑
        if jd_min >= self.salary_min and jd_max <= self.salary_max:
            # JD 范围在期望范围内
            score = 100
            detail = f"JD {salary_str} 在你的期望范围内"
            reasons.append(detail)
        elif jd_min >= self.salary_min:
            # JD 下限 >= 期望下限（薪资不错）
            score = 85
            detail = f"JD {salary_str} 薪资高于或等于期望"
            reasons.append(detail)
        elif jd_max >= self.salary_min:
            # JD 上限 >= 期望下限（有交集）
            score = 70
            detail = f"JD {salary_str} 与期望有交集"
            reasons.append(detail)
        elif jd_max >= self.salary_min * 0.8:
            # 接近期望
            score = 50
            detail = f"JD {salary_str} 略低于期望"
            gaps.append("薪资低于期望")
        else:
            # 远低于期望
            score = 20
            detail = f"JD {salary_str} 远低于期望"
            gaps.append("薪资远低于期望")

        return {"score": score, "detail": detail, "reasons": reasons, "gaps": gaps}

    def _match_title(self, job_data: dict) -> dict:
        """职级匹配（0-100）"""
        jd_title = job_data.get("title", "").lower()
        if not jd_title or not self.my_titles:
            return {"score": 50, "detail": "无职位数据", "reasons": [], "gaps": []}

        reasons = []
        gaps = []

        # 精确匹配
        if jd_title in self.my_titles:
            score = 100
            detail = f"职位 \"{job_data.get('title')}\" 与你的历史职位匹配"
            reasons.append(detail)
            return {"score": score, "detail": detail, "reasons": reasons, "gaps": gaps}

        # 部分匹配
        for my_title in self.my_titles:
            if my_title in jd_title or jd_title in my_title:
                score = 85
                detail = f"职位 \"{job_data.get('title')}\" 与你的历史职位 \"{my_title}\" 相关"
                reasons.append(detail)
                return {"score": score, "detail": detail, "reasons": reasons, "gaps": gaps}

        # 关键词匹配
        title_keywords = ["总监", "经理", "架构师", "vp", "cto", "负责人", "主管", "工程师", "开发"]
        jd_keywords = set(k for k in title_keywords if k in jd_title)
        my_keywords = set()
        for t in self.my_titles:
            my_keywords.update(k for k in title_keywords if k in t)

        overlap = jd_keywords & my_keywords
        if overlap:
            score = 70
            detail = f"职位 \"{job_data.get('title')}\" 有共同关键词：{', '.join(overlap)}"
            reasons.append(detail)
        else:
            score = 30
            detail = f"职位 \"{job_data.get('title')}\" 与你的历史职位不匹配"
            gaps.append(f"职位不匹配：JD要求 \"{job_data.get('title')}\"")

        return {"score": score, "detail": detail, "reasons": reasons, "gaps": gaps}

    def _match_age(self, job_data: dict) -> dict:
        """年龄友好度（0-100）"""
        analysis = job_data.get("analysis")
        if not analysis:
            return {"score": 50, "detail": "无年龄分析数据", "reasons": [], "gaps": []}

        score_100 = analysis.get("score", 50)  # analyzer 的 0-100 分
        friendly = analysis.get("friendly", False)
        age_profile = analysis.get("age_profile")

        reasons = []
        gaps = []

        if friendly:
            reasons.append("岗位对大龄友好")
        else:
            gaps.append("岗位对大龄不太友好")

        if age_profile:
            if age_profile.get("has_explicit_age_limit"):
                gaps.append(f"有明确年龄限制：{age_profile.get('age_limit_text', '')}")

        return {"score": score_100, "detail": f"大龄友好度 {score_100}分", "reasons": reasons, "gaps": gaps}

    def _match_industry(self, text: str) -> dict:
        """行业匹配（0-100）"""
        if not self.my_industries:
            return {"score": 50, "detail": "无行业数据", "reasons": [], "gaps": []}

        # 检查 JD 中是否包含我的行业关键词
        matched_industries = set()
        for industry in self.my_industries:
            if industry in text:
                matched_industries.add(industry)

        reasons = []
        gaps = []

        if matched_industries:
            score = 100
            detail = f"行业匹配：{', '.join(matched_industries)}"
            reasons.append(detail)
        else:
            score = 30
            detail = "行业不匹配"
            gaps.append("JD 行业与你的经验不匹配")

        return {"score": score, "detail": detail, "reasons": reasons, "gaps": gaps}
