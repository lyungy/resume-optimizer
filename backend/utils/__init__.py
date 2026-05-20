"""
工具函数包
"""
from .docx_parser import docx_parser, DocxParser
from .docx_writer import docx_writer, DocxWriter

__all__ = [
    "docx_parser",
    "DocxParser",
    "docx_writer",
    "DocxWriter",
]
