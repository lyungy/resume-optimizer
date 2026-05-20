"""
DOCX 文件解析工具
"""
from pathlib import Path
from docx import Document


class DocxParser:
    """DOCX 文件解析器"""

    def parse(self, file_path: str) -> dict:
        """
        解析 DOCX 文件，提取文本内容
        
        返回:
            {
                "text": "完整文本",
                "paragraphs": ["段落列表"],
                "tables": [{"headers": [], "rows": []}],
                "sections": {"section_name": "content"}
            }
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        doc = Document(file_path)

        # 按文档顺序提取所有内容（段落 + 表格）
        all_text_parts = []
        paragraphs = []
        tables = []

        # 遍历文档元素，保持原始顺序
        for element in doc.element.body:
            tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag

            if tag == 'p':
                # 段落
                text = element.text
                if text and text.strip():
                    paragraphs.append(text.strip())
                    all_text_parts.append(text.strip())
            elif tag == 'tbl':
                # 表格
                table_text = self._extract_table_text(element, doc)
                if table_text:
                    tables.append(table_text)
                    all_text_parts.append(table_text["formatted_text"])

        # 合并所有文本
        full_text = "\n".join(all_text_parts)

        # 尝试按常见简历结构分段
        sections = self._extract_sections(paragraphs)

        return {
            "text": full_text,
            "paragraphs": paragraphs,
            "tables": tables,
            "sections": sections,
        }

    def _extract_table_text(self, table_element, doc) -> dict:
        """从表格元素中提取文本"""
        from docx.table import Table
        from docx.oxml.ns import qn

        table = Table(table_element, doc)
        headers = []
        rows = []
        all_row_texts = []

        for i, row in enumerate(table.rows):
            row_data = []
            for cell in row.cells:
                # 获取单元格的完整文本（包括换行）
                cell_text = cell.text.strip()
                row_data.append(cell_text)

            if i == 0:
                headers = row_data
            rows.append(row_data)
            all_row_texts.append(" | ".join([t for t in row_data if t]))

        # 格式化为可读文本
        formatted_text = "\n".join(all_row_texts)

        return {
            "headers": headers,
            "rows": rows,
            "formatted_text": formatted_text,
        }

    def _extract_sections(self, paragraphs: list[str]) -> dict[str, str]:
        """
        尝试从段落中提取简历的各个部分
        """
        section_keywords = {
            "基本信息": ["个人信息", "基本信息", "联系方式", "姓名"],
            "求职意向": ["求职意向", "期望职位", "期望薪资"],
            "教育经历": ["教育经历", "教育背景", "学历"],
            "工作经历": ["工作经历", "工作经验", "项目经验", "任职经历"],
            "项目经历": ["项目经历", "项目经验", "项目描述"],
            "技能": ["专业技能", "技术栈", "技能特长", "技术能力"],
            "自我评价": ["自我评价", "自我介绍", "个人简介", "个人总结"],
            "证书": ["证书", "资格证书", "荣誉证书"],
        }

        sections = {}
        current_section = "其他"
        current_content = []

        for para in paragraphs:
            # 检查是否是新的段落标题
            is_section_header = False
            for section_name, keywords in section_keywords.items():
                if any(keyword in para for keyword in keywords):
                    # 保存之前的内容
                    if current_content:
                        sections[current_section] = "\n".join(current_content)
                    current_section = section_name
                    current_content = []
                    is_section_header = True
                    break

            if not is_section_header:
                current_content.append(para)

        # 保存最后一段
        if current_content:
            sections[current_section] = "\n".join(current_content)

        return sections

    def extract_text(self, file_path: str) -> str:
        """仅提取纯文本"""
        result = self.parse(file_path)
        return result["text"]


# 全局实例
docx_parser = DocxParser()
