"""
从 OpenClaw 配置文件读取 LLM 配置
"""
import json
from pathlib import Path
from dataclasses import dataclass

OPENCLAW_CONFIG_PATH = Path.home() / ".openclaw" / "openclaw.json"


@dataclass
class LLMModelInfo:
    """模型信息"""
    id: str
    name: str
    context_window: int = 0
    max_tokens: int = 4096


@dataclass
class LLMProviderInfo:
    """Provider 信息"""
    name: str
    base_url: str
    api_key: str
    models: list[LLMModelInfo]


class OpenClawConfigReader:
    """从 OpenClaw 配置文件读取 LLM 配置"""

    def __init__(self, config_path: Path = OPENCLAW_CONFIG_PATH):
        self.config_path = config_path

    def read(self) -> dict:
        """读取配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"OpenClaw 配置文件不存在: {self.config_path}"
            )
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_provider(self, provider_name: str) -> LLMProviderInfo:
        """获取指定 Provider 的配置"""
        config = self.read()
        providers = config.get("models", {}).get("providers", {})

        if provider_name not in providers:
            raise ValueError(f"Provider '{provider_name}' 不存在于 OpenClaw 配置中")

        provider = providers[provider_name]
        models = [
            LLMModelInfo(
                id=m["id"],
                name=m.get("name", m["id"]),
                context_window=m.get("contextWindow", 0),
                max_tokens=m.get("maxTokens", 4096),
            )
            for m in provider.get("models", [])
        ]

        return LLMProviderInfo(
            name=provider_name,
            base_url=provider.get("baseUrl", ""),
            api_key=provider.get("apiKey", ""),
            models=models,
        )

    def get_all_providers(self) -> list[LLMProviderInfo]:
        """获取所有可用的 Provider"""
        config = self.read()
        providers = config.get("models", {}).get("providers", {})
        return [self.get_provider(name) for name in providers.keys()]

    def get_provider_names(self) -> list[str]:
        """获取所有 Provider 名称"""
        config = self.read()
        return list(config.get("models", {}).get("providers", {}).keys())


def import_providers_to_config() -> dict:
    """
    从 OpenClaw 导入配置，返回可写入 config.yaml 的格式
    """
    reader = OpenClawConfigReader()
    providers = {}

    for provider_info in reader.get_all_providers():
        providers[provider_info.name] = {
            "name": provider_info.name,
            "base_url": provider_info.base_url,
            "api_key": provider_info.api_key,
            "models": [
                {
                    "id": m.id,
                    "name": m.name,
                    "is_default": i == 0,  # 第一个模型为默认
                }
                for i, m in enumerate(provider_info.models)
            ],
        }

    return providers


if __name__ == "__main__":
    # 测试读取配置
    reader = OpenClawConfigReader()
    print("可用 Providers:", reader.get_provider_names())
    for provider in reader.get_all_providers():
        print(f"\n{provider.name}:")
        print(f"  Base URL: {provider.base_url}")
        print(f"  API Key: {provider.api_key[:10]}...")
        for m in provider.models:
            print(f"  模型: {m.id} ({m.name})")
