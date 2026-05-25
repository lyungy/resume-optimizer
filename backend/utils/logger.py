"""
统一日志配置
"""
import logging
import sys
from pathlib import Path


def setup_logger(
    name: str = "resume_optimizer",
    level: int = logging.INFO,
    log_file: str | None = None,
) -> logging.Logger:
    """
    配置统一日志格式

    Args:
        name: logger 名称
        level: 日志级别
        log_file: 日志文件路径（可选）
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件输出（可选）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# 全局 logger 实例
logger = setup_logger()


def get_logger(name: str) -> logging.Logger:
    """获取子 logger"""
    return logging.getLogger(f"resume_optimizer.{name}")
