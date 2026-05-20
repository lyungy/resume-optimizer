#!/usr/bin/env python3
"""
从 OpenClaw 配置文件导入 LLM 配置到项目 config.yaml
"""
import sys
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import yaml
from services.llm.config_reader import OpenClawConfigReader

CONFIG_FILE = project_root / "config.yaml"


def import_config():
    """从 OpenClaw 导入 LLM 配置"""
    print("📥 正在从 OpenClaw 读取 LLM 配置...")

    try:
        reader = OpenClawConfigReader()
    except FileNotFoundError as e:
        print(f"❌ 错误: {e}")
        print("请确认 OpenClaw 已安装，配置文件存在于 ~/.openclaw/openclaw.json")
        sys.exit(1)

    # 读取现有配置
    existing_config = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            existing_config = yaml.safe_load(f) or {}

    # 构建 LLM 配置
    llm_config = {"default_provider": "xiaomi-coding", "providers": {}}

    for provider_info in reader.get_all_providers():
        provider_config = {
            "name": provider_info.name,
            "base_url": provider_info.base_url,
            "api_key": provider_info.api_key,
            "models": [
                {
                    "id": m.id,
                    "name": m.name,
                    "is_default": i == 0,
                }
                for i, m in enumerate(provider_info.models)
            ],
        }
        llm_config["providers"][provider_info.name] = provider_config
        print(f"✅ 已导入 {provider_info.name} 配置:")
        print(f"   Base URL: {provider_info.base_url}")
        print(f"   API Key: {provider_info.api_key[:10]}...")
        for idx, m in enumerate(provider_info.models):
            default_mark = " (默认)" if idx == 0 else ""
            print(f"   模型: {m.id} ({m.name}){default_mark}")

    # 合并配置
    existing_config["llm"] = llm_config

    # 确保其他配置存在
    if "database" not in existing_config:
        existing_config["database"] = {
            "url": f"sqlite:///{project_root / 'data' / 'db' / 'resume_optimizer.db'}"
        }
    if "files" not in existing_config:
        existing_config["files"] = {"dir": str(project_root / "data" / "files")}

    # 写入配置文件
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(existing_config, f, allow_unicode=True, default_flow_style=False)

    print(f"\n📝 配置已写入: {CONFIG_FILE}")
    print(f"默认模型: {llm_config['default_provider']}")
    print("\n✅ 导入完成！")


if __name__ == "__main__":
    import_config()
