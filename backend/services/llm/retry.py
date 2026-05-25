"""
LLM 调用工具 - 重试、解析、容错
"""
import json
import re
import time
import logging
from typing import Optional

logger = logging.getLogger("resume_optimizer.llm")

# 重试配置
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2  # 秒


def call_llm_with_retry(
    client,
    messages: list[dict],
    model: str,
    temperature: float = 0.5,
    max_tokens: int = 4000,
    json_mode: bool = True,
) -> str:
    """带重试的 LLM 调用"""
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"LLM 调用 (attempt {attempt + 1}/{MAX_RETRIES})")

            if json_mode:
                response = client.chat_json(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            else:
                response = client.chat(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

            if not response or not response.strip():
                raise ValueError("LLM 返回空响应")

            return response

        except Exception as e:
            last_error = e
            error_msg = str(e)

            # 不可重试的错误
            if any(kw in error_msg.lower() for kw in ["auth", "api_key", "invalid_key"]):
                raise ValueError(f"LLM 认证失败: {error_msg}")

            if attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning(f"LLM 调用失败，{delay}s 后重试: {error_msg}")
                time.sleep(delay)
            else:
                logger.error(f"LLM 调用失败（已重试 {MAX_RETRIES} 次）: {error_msg}")

    raise ValueError(f"LLM 调用失败（已重试 {MAX_RETRIES} 次）: {last_error}")


def parse_json_response(response: str) -> dict:
    """容错解析 LLM 返回的 JSON"""
    # 1. 直接解析
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # 2. 提取 JSON 块
    try:
        start = response.find('{')
        end = response.rfind('}')
        if start != -1 and end != -1 and end > start:
            json_str = response[start:end + 1]
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # 3. 修复常见问题
    try:
        cleaned = _fix_json(response)
        return json.loads(cleaned)
    except (json.JSONDecodeError, Exception):
        pass

    # 4. 全部失败
    logger.error(f"JSON 解析失败，返回空结构。响应前 500 字: {response[:500]}")
    return {}


def _fix_json(text: str) -> str:
    """修复常见 JSON 格式问题"""
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1:
        return text

    json_str = text[start:end + 1]

    # 去除尾部逗号
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)

    # 修复未转义的换行符
    json_str = json_str.replace('\n', '\\n')

    return json_str
