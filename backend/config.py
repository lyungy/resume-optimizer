"""
配置管理模块
支持从 config.yaml 读取配置
"""
from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel

# 项目根目录（backend 目录）
BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.yaml"


class LLMModelConfig(BaseModel):
    """单个模型配置"""
    id: str
    name: str
    is_default: bool = False


class LLMProviderConfig(BaseModel):
    """LLM Provider 配置"""
    name: str
    base_url: str
    api_key: str
    models: list[LLMModelConfig] = []


class LLMConfig(BaseModel):
    """LLM 整体配置"""
    default_provider: str = "xiaomi-coding"
    providers: dict[str, LLMProviderConfig] = {}


class DatabaseConfig(BaseModel):
    """数据库配置"""
    url: str = f"sqlite:///{BASE_DIR.parent / 'data' / 'db' / 'resume_optimizer.db'}"


class FilesConfig(BaseModel):
    """文件存储配置"""
    dir: str = str(BASE_DIR.parent / "data" / "files")


class AppConfig(BaseModel):
    """应用配置"""
    app_name: str = "简历优化系统"
    app_version: str = "1.0.0"
    debug: bool = False
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    database: DatabaseConfig = DatabaseConfig()
    llm: LLMConfig = LLMConfig()
    files: FilesConfig = FilesConfig()


def load_config_from_yaml(config_path: Path = CONFIG_FILE) -> dict:
    """从 YAML 文件加载配置"""
    if not config_path.exists():
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_config() -> AppConfig:
    """获取应用配置"""
    yaml_config = load_config_from_yaml()

    # 构建配置数据
    config_data = {}

    # 基础配置（支持环境变量覆盖）
    import os
    config_data["debug"] = os.getenv("DEBUG", "false").lower() == "true"
    config_data["backend_host"] = os.getenv("BACKEND_HOST", "0.0.0.0")
    config_data["backend_port"] = int(os.getenv("BACKEND_PORT", "8000"))

    # 数据库配置
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        config_data["database"] = {"url": db_url}
    elif "database" in yaml_config:
        config_data["database"] = yaml_config["database"]

    # 文件配置
    files_dir = os.getenv("FILES_DIR")
    if files_dir:
        config_data["files"] = {"dir": files_dir}
    elif "files" in yaml_config:
        config_data["files"] = yaml_config["files"]

    # LLM 配置（从 YAML 读取，手动解析嵌套对象）
    if "llm" in yaml_config:
        llm_data = yaml_config["llm"]
        providers = {}
        for name, p_data in llm_data.get("providers", {}).items():
            providers[name] = LLMProviderConfig(**p_data)
        config_data["llm"] = LLMConfig(
            default_provider=llm_data.get("default_provider", "xiaomi-coding"),
            providers=providers
        )

    return AppConfig(**config_data)


# 全局配置实例
config = get_config()
