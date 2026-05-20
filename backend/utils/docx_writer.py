"""
DOCX 文件生成工具
"""
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from datetime import datetime


class DocxWriter:
    """DOCX 文件生成器"""

    def __init__(self):
        self._setup_styles()

    def _setup_styles(self):
        """设置文档样式"""
        pass

    def create_resume(
        self,
        content: dict,
        output_path: str,
        original_doc_path: str = None,
    ) -> str:
        """
        生成优化后的简历 DOCX 文件
        
        参数:
            content: 优化后的内容
            output_path: 输出文件路径
            original_doc_path: 原始简历路径（用于保留格式）
        
        返回:
            输出文件路径
        """
        doc = Document()

        # 设置文档样式
        style = doc.styles["Normal"]
        style.font.name = "微软雅黑"
        style.font.size = Pt(10.5)

        # 添加标题（个人姓名）
        if "name" in content:
            heading = doc.add_heading(content["name"], level=1)
            heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # 添加个人总结
        if "summary" in content.get("optimized_sections", {}):
            doc.add_heading("个人总结", level=2)
            doc.add_paragraph(content["optimized_sections"]["summary"])

        # 添加技能
        if "skills" in content.get("optimized_sections", {}):
            doc.add_heading("专业技能", level=2)
            skills = content["optimized_sections"]["skills"]
            doc.add_paragraph("、".join(skills))

        # 添加工作经历
        if "experience" in content.get("optimized_sections", {}):
            doc.add_heading("工作经历", level=2)
            for exp in content["optimized_sections"]["experience"]:
                # 公司和职位
                p = doc.add_paragraph()
                run = p.add_run(f"{exp.get('company', '')} - {exp.get('title', '')}")
                run.bold = True
                if "period" in exp:
                    p.add_run(f"  ({exp['period']})")

                # 亮点
                for highlight in exp.get("highlights", []):
                    doc.add_paragraph(highlight, style="List Bullet")

        # 添加项目经历
        if "projects" in content.get("optimized_sections", {}):
            doc.add_heading("项目经历", level=2)
            for proj in content["optimized_sections"]["projects"]:
                # 项目名
                p = doc.add_paragraph()
                run = p.add_run(proj.get("name", ""))
                run.bold = True
                if "role" in proj:
                    p.add_run(f"  |  {proj['role']}")

                # 亮点
                for highlight in proj.get("highlights", []):
                    doc.add_paragraph(highlight, style="List Bullet")

        # 添加优化建议（作为备注）
        if "suggestions" in content and content["suggestions"]:
            doc.add_heading("优化建议", level=2)
            for suggestion in content["suggestions"]:
                doc.add_paragraph(suggestion, style="List Bullet")

        # 保存文档
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(output))

        return str(output)

    def create_interview_guide(
        self,
        content: dict,
        output_path: str,
        jd_title: str = "",
        company_name: str = "",
    ) -> str:
        """
        生成面试攻略 DOCX 文件
        
        参数:
            content: 面试攻略内容
            output_path: 输出文件路径
            jd_title: 职位名称
            company_name: 公司名称
        
        返回:
            输出文件路径
        """
        doc = Document()

        # 设置文档样式
        style = doc.styles["Normal"]
        style.font.name = "微软雅黑"
        style.font.size = Pt(10.5)

        # 标题
        title = f"面试攻略 - {company_name} {jd_title}" if company_name else "面试攻略"
        heading = doc.add_heading(title, level=1)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # 生成时间
        doc.add_paragraph(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
        doc.add_paragraph("")

        # 知识点清单
        if "knowledge_points" in content:
            doc.add_heading("知识点清单", level=2)
            for kp in content["knowledge_points"]:
                doc.add_heading(kp.get("category", "未分类"), level=3)
                priority = kp.get("priority", "medium")
                doc.add_paragraph(f"优先级：{priority} | 预计准备时间：{kp.get('estimated_prep_hours', 0)}小时")
                for point in kp.get("points", []):
                    doc.add_paragraph(point, style="List Bullet")
                if "study_resources" in kp:
                    doc.add_paragraph("推荐学习方向：")
                    for resource in kp["study_resources"]:
                        doc.add_paragraph(resource, style="List Bullet 2")

        # 高频面试题
        if "high_frequency_questions" in content:
            doc.add_heading("高频面试题", level=2)
            for i, q in enumerate(content["high_frequency_questions"], 1):
                doc.add_heading(f"Q{i}: {q.get('question', '')}", level=3)
                doc.add_paragraph(f"分类：{q.get('category', '')} | 难度：{q.get('difficulty', '')}")

                if "answer_template" in q:
                    doc.add_paragraph("答题模板：")
                    doc.add_paragraph(q["answer_template"])

                if "key_points" in q:
                    doc.add_paragraph("回答要点：")
                    for point in q["key_points"]:
                        doc.add_paragraph(point, style="List Bullet")

                if "common_mistakes" in q:
                    doc.add_paragraph("常见错误：")
                    for mistake in q["common_mistakes"]:
                        doc.add_paragraph(mistake, style="List Bullet")

        # 准备策略
        if "preparation_strategy" in content:
            strategy = content["preparation_strategy"]
            doc.add_heading("准备策略", level=2)
            doc.add_paragraph(f"建议准备天数：{strategy.get('total_days', 7)} 天")

            if "daily_plan" in strategy:
                doc.add_heading("每日计划", level=3)
                for day_plan in strategy["daily_plan"]:
                    doc.add_paragraph(
                        f"第{day_plan.get('day', '')}天 - {day_plan.get('focus', '')} "
                        f"(预计 {day_plan.get('hours', 0)} 小时)"
                    )
                    for task in day_plan.get("tasks", []):
                        doc.add_paragraph(task, style="List Bullet")

            if "tips" in strategy:
                doc.add_heading("面试技巧", level=3)
                for tip in strategy["tips"]:
                    doc.add_paragraph(tip, style="List Bullet")

        # 公司调研
        if "company_research" in content:
            cr = content["company_research"]
            doc.add_heading("公司调研", level=2)

            if "what_to_prepare" in cr:
                doc.add_paragraph("需要了解的信息：")
                for item in cr["what_to_prepare"]:
                    doc.add_paragraph(item, style="List Bullet")

            if "questions_to_ask" in cr:
                doc.add_paragraph("可以反问面试官的问题：")
                for q in cr["questions_to_ask"]:
                    doc.add_paragraph(q, style="List Bullet")

            if "red_flags" in cr:
                doc.add_paragraph("需要注意的信号：")
                for flag in cr["red_flags"]:
                    doc.add_paragraph(flag, style="List Bullet")

        # 薪资谈判
        if "salary_negotiation" in content:
            sn = content["salary_negotiation"]
            doc.add_heading("薪资谈判参考", level=2)
            if "market_range" in sn:
                doc.add_paragraph(f"市场薪资范围：{sn['market_range']}")
            if "negotiation_tips" in sn:
                for tip in sn["negotiation_tips"]:
                    doc.add_paragraph(tip, style="List Bullet")

        # 保存文档
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(output))

        return str(output)


# 全局实例
docx_writer = DocxWriter()
