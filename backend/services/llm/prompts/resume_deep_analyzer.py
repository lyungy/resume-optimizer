"""
简历职业画像 Prompt
提取多维度求职画像 + 推荐适合岗位
"""


# 系统 prompt 常量
DEEP_ANALYZE_SYSTEM = """你是资深职业规划师和简历分析专家。根据简历内容，完成以下任务：

1. 提取硬性技能（按类别分类：语言、框架、中间件、架构能力、运维工具、数据库）
2. 提取软技能（管理能力、技术能力、业务能力）
3. 分析经验画像（工作年限、最高职位、管理规模、行业经验、公司规模）
4. 提取教育背景
5. 提取项目亮点（项目名、技术栈、规模、成果）
6. 推荐 5-8 个适合的职业岗位，每个给出匹配度百分比（0-100）和匹配理由

匹配度计算依据：
- 技能匹配度（技能栈与岗位要求的重合度）
- 经验匹配度（工作年限和职位级别是否匹配）
- 行业匹配度（行业经验是否相关）
- 管理经验（是否有团队管理经验，管理岗位需要）

必须输出纯 JSON，不要任何额外文字。"""


# 用于 API 返回给前端展示
DEEP_ANALYZE_PROMPT_TEMPLATE = DEEP_ANALYZE_SYSTEM


def get_deep_analyze_prompt(resume_text: str, custom_system: str | None = None) -> list[dict]:
    """
    构建职业画像的 Prompt，支持自定义 system prompt
    返回消息列表，用于 LLM 调用
    """
    system_prompt = custom_system or DEEP_ANALYZE_SYSTEM

    user_prompt = f"""请分析以下简历内容：

{resume_text}

输出格式：
{{
  "profile": {{
    "hard_skills": {{
      "languages": ["语言列表"],
      "frameworks": ["框架列表"],
      "middleware": ["中间件列表"],
      "architecture": ["架构能力列表"],
      "devops": ["运维工具列表"],
      "databases": ["数据库列表"]
    }},
    "soft_skills": ["软技能列表"],
    "experience_profile": {{
      "total_years": 数字,
      "highest_title": "最高职位",
      "management_scale": "管理规模描述",
      "industries": ["行业列表"],
      "company_sizes": ["公司规模列表"]
    }},
    "education": {{
      "degree": "学历",
      "major": "专业",
      "school": "学校",
      "school_tier": "985/211/普通"
    }},
    "project_highlights": [
      {{
        "name": "项目名",
        "tech_stack": ["技术栈"],
        "scale": "规模",
        "achievement": "成果"
      }}
    ]
  }},
  "recommended_positions": [
    {{
      "title": "岗位名称",
      "match_score": 匹配度百分比数字,
      "match_reasons": ["匹配理由1", "匹配理由2"]
    }}
  ]
}}"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
