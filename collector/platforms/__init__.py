"""
招聘平台适配器
"""
from .base import BasePlatform, JobInfo
from .boss import BossPlatform

__all__ = ["BasePlatform", "JobInfo", "BossPlatform"]
