"""
工具函数包
"""
from .docx_parser import docx_parser, DocxParser
from .docx_writer import docx_writer, DocxWriter
from .logger import logger, get_logger, setup_logger

__all__ = [
    "docx_parser",
    "DocxParser",
    "docx_writer",
    "DocxWriter",
    "logger",
    "get_logger",
    "setup_logger",
]
