"""
简历解析 Prompt 模板
"""

RESUME_PARSE_SYSTEM = """你是一位资深 HR 和 ATS 系统专家，擅长从简历中提取结构化信息。

请从以下简历文本中提取关键信息。简历可能包含表格、列表等复杂格式。

请以 JSON 格式输出，包含以下字段：
{
  "name": "候选人姓名（如果有的话）",
  "experience_years": 16,
  "education": {
    "degree": "最高学历",
    "school": "毕业院校",
    "major": "专业"
  },
  "skills": ["技术技能1", "技术技能2", "框架名", "工具名"],
  "work_experience": [
    {
      "company": "公司名称",
      "title": "职位名称",
      "period": "2020.06 - 2024.12",
      "highlights": ["主要职责或成果"]
    }
  ],
  "projects": [
    {
      "name": "项目名称",
      "role": "担任角色",
      "period": "2024.01 - 2024.12",
      "highlights": ["项目成果"]
    }
  ],
  "self_evaluation": "自我评价摘要（100字以内）"
}

重要提示：
1. experience_years 必须是数字，根据工作经历的时间段推算总年限
2. skills 要提取所有提到的技术栈、框架、工具、编程语言、数据库、云平台等
3. work_experience 要提取所有工作经历，按时间倒序
4. projects 要提取所有项目经历
5. 如果文本中提到"XX年工作经验"，直接使用该数字
6. 不要遗漏任何工作经历或项目"""


# 用于 API 返回给前端展示
RESUME_PARSE_PROMPT_TEMPLATE = RESUME_PARSE_SYSTEM


def get_resume_parse_prompt(resume_text: str, custom_system: str | None = None) -> list[dict]:
    """获取简历解析的完整 prompt，支持自定义 system prompt"""
    # 截取前 8000 字符，避免超出 token 限制
    truncated_text = resume_text[:8000] if len(resume_text) > 8000 else resume_text

    user_content = f"""请分析以下简历内容，提取结构化信息：

{truncated_text}

请以 JSON 格式输出。注意提取所有工作经历和项目经历。"""

    system = custom_system or RESUME_PARSE_SYSTEM

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]
