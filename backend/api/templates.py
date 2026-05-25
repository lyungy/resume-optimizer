"""
简历模板 API 路由
"""
import json
import logging
from pathlib import Path
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/templates", tags=["简历模板"])

TEMPLATES_DIR = Path(__file__).parent.parent / "data" / "templates"


@router.get("")
def list_templates():
    """获取可用的简历模板列表"""
    templates_file = TEMPLATES_DIR / "templates.json"
    if not templates_file.exists():
        return {"templates": []}

    with open(templates_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {"templates": data.get("templates", [])}


@router.get("/{template_id}")
def get_template(template_id: str):
    """获取指定模板详情"""
    templates_file = TEMPLATES_DIR / "templates.json"
    if not templates_file.exists():
        return {"error": "模板文件不存在"}

    with open(templates_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for template in data.get("templates", []):
        if template["id"] == template_id:
            return template

    return {"error": "模板不存在"}
