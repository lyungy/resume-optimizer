"""
LLM 客户端 - OpenAI 兼容
支持 MiMo、DeepSeek 等多个 Provider
"""
import logging
from typing import Generator, Optional
from openai import OpenAI
from config import config, LLMProviderConfig, LLMModelConfig

logger = logging.getLogger("resume_optimizer.llm")


class LLMClient:
    """OpenAI 兼容 LLM 客户端"""

    def __init__(self, provider_config: LLMProviderConfig):
        self.provider = provider_config
        self.client = OpenAI(
            api_key=provider_config.api_key,
            base_url=provider_config.base_url,
            timeout=300.0,  # 5分钟超时
        )
        # 获取默认模型
        self._default_model = self._get_default_model()

    def _get_default_model(self) -> str:
        """获取默认模型 ID"""
        for model in self.provider.models:
            if model.is_default:
                return model.id
        return self.provider.models[0].id if self.provider.models else ""

    @property
    def default_model(self) -> str:
        return self._default_model

    @property
    def available_models(self) -> list[LLMModelConfig]:
        return self.provider.models

    def chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[dict] = None,
    ) -> str:
        """同步对话"""
        use_model = model or self._default_model
        logger.info(f"LLM 请求: provider={self.provider.name}, model={use_model}")
        kwargs = {
            "model": use_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        response = self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        logger.info(f"LLM 响应: model={use_model}, tokens={response.usage.total_tokens if response.usage else 'N/A'}")
        return content

    def chat_json(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """同步对话 - JSON 格式输出"""
        return self.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

    def chat_stream(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Generator[str, None, None]:
        """流式对话（用于 SSE）"""
        stream = self.client.chat.completions.create(
            model=model or self._default_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class LLMClientManager:
    """LLM 客户端管理器 - 管理多个 Provider"""

    def __init__(self):
        self._clients: dict[str, LLMClient] = {}

    def _init_clients(self):
        """初始化所有 Provider 的客户端"""
        for name, provider_config in config.llm.providers.items():
            if name not in self._clients:
                self._clients[name] = LLMClient(provider_config)

    def get_client(self, provider_name: Optional[str] = None) -> LLMClient:
        """获取指定 Provider 的客户端"""
        self._init_clients()
        name = provider_name or config.llm.default_provider
        if name not in self._clients:
            raise ValueError(
                f"LLM Provider '{name}' 未配置。可用: {list(self._clients.keys())}"
            )
        return self._clients[name]

    @property
    def available_providers(self) -> list[str]:
        """获取所有可用的 Provider 名称"""
        self._init_clients()
        return list(self._clients.keys())

    def get_provider_models(self, provider_name: Optional[str] = None) -> list[dict]:
        """获取指定 Provider 的所有模型"""
        client = self.get_client(provider_name)
        return [
            {"id": m.id, "name": m.name, "is_default": m.is_default}
            for m in client.available_models
        ]


# 全局客户端管理器
llm_manager = LLMClientManager()


def get_llm_client(provider_name: Optional[str] = None) -> LLMClient:
    """获取 LLM 客户端的便捷函数"""
    return llm_manager.get_client(provider_name)
