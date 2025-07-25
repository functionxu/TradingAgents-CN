"""
统一日志配置
"""
import logging
import sys
from datetime import datetime
from typing import Optional
from contextvars import ContextVar

# 全局上下文变量，用于存储当前分析ID
current_analysis_id: ContextVar[Optional[str]] = ContextVar('analysis_id', default=None)


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    # 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'RESET': '\033[0m'      # 重置
    }
    
    def format(self, record):
        # 添加颜色
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        # 格式化时间
        record.asctime = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')

        # 获取当前分析ID
        analysis_id = current_analysis_id.get()
        analysis_prefix = f"[{analysis_id[:8]}]" if analysis_id else ""

        # 格式化消息
        log_message = f"{color}[{record.levelname}]{reset} {record.asctime} - {record.name} {analysis_prefix}- {record.getMessage()}"

        # 添加异常信息
        if record.exc_info:
            log_message += f"\n{self.formatException(record.exc_info)}"

        return log_message


def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        log_file: 日志文件路径（可选）
    
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(ColoredFormatter())

    # 设置立即刷新，避免日志缓冲
    console_handler.flush = lambda: sys.stdout.flush()

    logger.addHandler(console_handler)
    
    # 文件处理器（如果指定了文件路径）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper()))
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_service_logger(service_name: str) -> logging.Logger:
    """
    获取服务专用的日志记录器

    Args:
        service_name: 服务名称

    Returns:
        日志记录器
    """
    return setup_logger(f"tradingagents.{service_name}")


def set_analysis_id(analysis_id: str):
    """
    设置当前分析ID到上下文

    Args:
        analysis_id: 分析ID
    """
    current_analysis_id.set(analysis_id)


def get_analysis_id() -> Optional[str]:
    """
    获取当前分析ID

    Returns:
        当前分析ID，如果没有则返回None
    """
    return current_analysis_id.get()


def clear_analysis_id():
    """清除当前分析ID"""
    current_analysis_id.set(None)


class AnalysisLoggerAdapter(logging.LoggerAdapter):
    """
    分析日志适配器，自动添加分析ID到日志消息
    """

    def __init__(self, logger: logging.Logger, analysis_id: str):
        super().__init__(logger, {})
        self.analysis_id = analysis_id

    def process(self, msg, kwargs):
        # 设置分析ID到上下文
        current_analysis_id.set(self.analysis_id)
        return msg, kwargs
