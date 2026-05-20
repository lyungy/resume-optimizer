"""
LLM 配置 API 路由
"""
from fastapi import APIRouter
from services.llm import llm_manager

router = APIRouter(prefix="/llm", tags=["LLM 配置"])


@router.get("/providers")
def list_providers():
    """获取可用的 LLM Provider 列表"""
    providers = llm_manager.available_providers
    return {
        "providers": providers,
        "default": llm_manager.get_client().provider.name,
    }


@router.get("/providers/{provider_name}/models")
def list_models(provider_name: str):
    """获取指定 Provider 的模型列表"""
    try:
        models = llm_manager.get_provider_models(provider_name)
        return {
            "provider": provider_name,
            "models": models,
        }
    except ValueError as e:
        return {"error": str(e)}


@router.get("/models")
def list_all_models():
    """获取所有可用的模型"""
    result = {}
    for provider_name in llm_manager.available_providers:
        result[provider_name] = llm_manager.get_provider_models(provider_name)
    return result
