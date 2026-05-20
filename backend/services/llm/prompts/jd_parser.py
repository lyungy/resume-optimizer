"""
JD 解析 Prompt 模板
"""

JD_PARSE_SYSTEM = """你是一位资深 HR 和技术面试官，擅长分析职位描述。
请从以下 JD 中提取结构化信息，特别关注对大龄 IT 从业者（35岁+）友好的信号。

请以 JSON 格式输出，包含以下字段：
{
  "hard_skills": ["必须掌握的技能，如：Java、Spring Boot、MySQL 等"],
  "soft_skills": ["软性要求，如：沟通能力、团队协作等"],
  "experience_years": "工作年限要求，如：3-5年、5年以上",
  "hidden_requirements": ["隐性需求推断，如：需要带团队、需要出差等"],
  "company_culture": "公司文化关键词，如：扁平化管理、加班文化等",
  "key_keywords": ["ATS 关键词，用于简历优化的核心词汇"],
  "difficulty_level": "junior/mid/senior",
  "senior_friendly": true或false,
  "senior_friendly_signals": ["对大龄友好的信号，如：看重经验、不强调加班、技术深度优先等"],
  "concern_signals": ["对大龄不利的信号，如：强调年轻团队、高强度工作、35岁以下等"]
}

注意：
1. hard_skills 应该是具体的技能名称，不要包含年限要求
2. key_keywords 是 ATS 系统会搜索的关键词，包括技能缩写、行业术语等
3. senior_friendly 的判断要基于 JD 中的实际描述，不要臆测
4. 如果 JD 中没有明确的年龄相关信号，senior_friendly 设为 true"""


def get_jd_parse_prompt(
    title: str,
    company_name: str,
    industry: str,
    jd_text: str,
) -> list[dict]:
    """获取 JD 解析的完整 prompt"""
    user_content = f"""请分析以下职位描述：

职位名称：{title}
公司名称：{company_name}
行业：{industry}

JD 内容：
{jd_text}

请以 JSON 格式输出分析结果。"""

    return [
        {"role": "system", "content": JD_PARSE_SYSTEM},
        {"role": "user", "content": user_content},
    ]
