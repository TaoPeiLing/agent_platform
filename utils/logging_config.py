"""
日志配置模块 - 提供标准化的日志配置
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import json
from pathlib import Path

# 日志级别映射
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

# 默认日志格式
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 确保日志目录存在
def ensure_log_dir(log_dir='logs'):
    """确保日志目录存在"""
    path = Path(log_dir)
    if not path.exists():
        path.mkdir(parents=True)
    return path


def setup_logging(app_name='sss_agent_platform', 
                 log_level='info',
                 log_to_console=True,
                 log_to_file=True,
                 log_dir='logs',
                 max_bytes=10_485_760,  # 10MB
                 backup_count=5):
    """
    设置日志配置
    
    Args:
        app_name: 应用名称
        log_level: 日志级别
        log_to_console: 是否输出到控制台
        log_to_file: 是否输出到文件
        log_dir: 日志目录
        max_bytes: 每个日志文件最大字节数
        backup_count: 保留的日志文件数量
    """
    # 确保日志目录存在
    if log_to_file:
        ensure_log_dir(log_dir)
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    
    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 设置日志级别
    level = LOG_LEVELS.get(log_level.lower(), logging.INFO)
    root_logger.setLevel(level)
    
    # 创建格式化器
    formatter = logging.Formatter(DEFAULT_FORMAT)
    
    # 添加控制台处理器
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # 添加文件处理器
    if log_to_file:
        # 常规日志
        log_file = Path(log_dir) / f"{app_name}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # 错误日志
        error_log_file = Path(log_dir) / f"{app_name}_error.log"
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    # 记录初始日志
    root_logger.info(f"日志系统初始化完成，级别: {logging.getLevelName(level)}")


def get_logger(name):
    """
    获取指定名称的日志记录器
    
    Args:
        name: 日志记录器名称
    
    Returns:
        Logger: 日志记录器
    """
    return logging.getLogger(name)


# 日志装饰器
def log_function_call(logger=None):
    """
    记录函数调用的装饰器
    
    Args:
        logger: 日志记录器，如果为None则使用函数模块名称
        
    Returns:
        decorator: 装饰器函数
    """
    def decorator(func):
        import functools
        
        # 获取日志记录器
        nonlocal logger
        if logger is None:
            logger = logging.getLogger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 记录函数调用
            arg_str = ", ".join([str(a) for a in args])
            kwarg_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
            params = f"{arg_str}{', ' if arg_str and kwarg_str else ''}{kwarg_str}"
            logger.debug(f"调用函数 {func.__name__}({params})")
            
            try:
                # 执行函数
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                # 记录异常
                logger.exception(f"函数 {func.__name__} 执行失败: {e}")
                raise
        
        return wrapper
    
    return decorator


# 初始化日志配置（如果需要）
if __name__ == "__main__":
    setup_logging()
    logger = get_logger("test")
    logger.debug("这是一条调试日志")
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")
    logger.critical("这是一条严重错误日志") 