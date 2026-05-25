"""
LLM 调用日志记录工具
在各 service 的 LLM 调用后统一记录
"""
import time
import json
import logging
from typing import Optional
from sqlalchemy.orm import Session
from models.llm_usage_log import LLMUsageLog

logger = logging.getLogger(__name__)


def log_llm_usage(
    db: Session,
    *,
    feature: str,
    llm_provider: str,
    llm_model: str,
    system_prompt: str | None = None,
    user_prompt: str | None = None,
    raw_response: str | None = None,
    parsed_result: dict | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    total_tokens: int | None = None,
    duration_ms: int | None = None,
    status: str = "success",
    error_message: str | None = None,
    retry_count: int = 0,
    related_id: str | None = None,
    related_type: str | None = None,
):
    """
    记录一次 LLM 调用日志

    Args:
        db: 数据库会话
        feature: 功能名称（智能解析/职业画像/JD解析/简历优化/面试攻略）
        llm_provider: LLM 提供商
        llm_model: 模型名称
        system_prompt: 完整 system prompt
        user_prompt: 完整 user prompt
        raw_response: LLM 原始返回
        parsed_result: 解析后的结构化结果
        input_tokens: 输入 token 数
        output_tokens: 输出 token 数
        total_tokens: 总 token 数
        duration_ms: 调用耗时（毫秒）
        status: success/failed/timeout
        error_message: 失败原因
        retry_count: 重试次数
        related_id: 关联业务 ID
        related_type: 关联类型
    """
    try:
        log_entry = LLMUsageLog(
            feature=feature,
            related_id=related_id,
            related_type=related_type,
            llm_provider=llm_provider,
            llm_model=llm_model,
            system_prompt=system_prompt,
            user_prompt=user_prompt[:10000] if user_prompt and len(user_prompt) > 10000 else user_prompt,
            raw_response=raw_response[:10000] if raw_response and len(raw_response) > 10000 else raw_response,
            parsed_result=parsed_result,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            duration_ms=duration_ms,
            status=status,
            error_message=error_message,
            retry_count=retry_count,
        )
        db.add(log_entry)
        db.commit()
        logger.info(
            f"LLM 日志已记录: feature={feature}, model={llm_model}, "
            f"tokens={total_tokens or 'N/A'}, duration={duration_ms}ms, status={status}"
        )
    except Exception as e:
        logger.error(f"LLM 日志记录失败: {e}")
        db.rollback()


def timed_llm_call(
    client,
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.5,
    max_tokens: int = 4000,
    json_mode: bool = True,
) -> tuple[str, dict]:
    """
    带计时的 LLM 调用，返回 (response, metadata)
    复用 client 的 chat_json / chat 方法，避免绕过 provider 特殊逻辑

    Returns:
        (response_text, metadata_dict)
        metadata_dict 包含: input_tokens, output_tokens, total_tokens, duration_ms
    """
    use_model = model or client.default_model
    start_time = time.time()

    # 复用 client 方法（内部已处理 provider 差异）
    if json_mode:
        content = client.chat_json(
            messages=messages,
            model=use_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    else:
        content = client.chat(
            messages=messages,
            model=use_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    duration_ms = int((time.time() - start_time) * 1000)

    metadata = {
        "input_tokens": None,  # client 方法不返回 usage，后续可扩展
        "output_tokens": None,
        "total_tokens": None,
        "duration_ms": duration_ms,
    }

    return content, metadata
