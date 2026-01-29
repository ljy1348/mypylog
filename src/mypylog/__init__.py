"""
mypylog - loguru + rich 조합 로거
객체(dict, list 등)가 입력되면 자동으로 pretty print
"""

from .logger import get_logger, logger, log_execution

__all__ = ["get_logger", "logger", "log_execution"]
__version__ = "0.1.0"
