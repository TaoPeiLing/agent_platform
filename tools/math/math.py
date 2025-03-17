"""
数学工具模块 - 提供基本计算和科学计算功能

包含两个主要工具函数：
1. calculate: 执行基本数学运算
2. scientific_calculate: 执行科学计算
"""
import logging
import math
import re
from typing import Dict, Any, Union, Optional

# 配置日志
logger = logging.getLogger(__name__)


def calculate(expression: str) -> str:
    """
    执行基本数学计算
    
    Args:
        expression: 要计算的数学表达式
        
    Returns:
        计算结果字符串
    """
    logger.info(f"执行基本计算: {expression}")
    
    try:
        # 清理输入
        expression = expression.strip()
        
        # 检查表达式是否安全
        if not _is_safe_expression(expression):
            return f"错误: 不安全的表达式 '{expression}'，只允许基本数学运算"
        
        # 为了计算更加安全，使用有限制的环境
        # 只允许使用基本数学运算符和函数
        safe_env = {
            "abs": abs, 
            "round": round, 
            "min": min, 
            "max": max,
            "sum": sum, 
            "pow": pow
        }
        
        # 执行计算
        result = eval(expression, {"__builtins__": {}}, safe_env)
        
        return f"计算结果: {result}"
    
    except Exception as e:
        logger.error(f"计算出错: {str(e)}")
        return f"计算错误: {str(e)}"


def scientific_calculate(expression: str) -> str:
    """
    执行科学计算，支持更多数学函数
    
    Args:
        expression: 要计算的科学表达式
        
    Returns:
        计算结果字符串
    """
    logger.info(f"执行科学计算: {expression}")
    
    try:
        # 清理输入
        expression = expression.strip()
        
        # 检查表达式是否安全
        if not _is_safe_expression(expression, include_scientific=True):
            return f"错误: 不安全的表达式 '{expression}'，只允许数学运算"
        
        # 为了计算更加安全，使用有限制的环境
        # 允许使用基本数学和科学计算函数
        safe_env = {
            # 基本函数
            "abs": abs, 
            "round": round, 
            "min": min, 
            "max": max,
            "sum": sum, 
            "pow": pow,
            
            # 科学计算函数
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "asin": math.asin,
            "acos": math.acos,
            "atan": math.atan,
            "log": math.log,
            "log10": math.log10,
            "exp": math.exp,
            "floor": math.floor,
            "ceil": math.ceil,
            
            # 常量
            "pi": math.pi,
            "e": math.e
        }
        
        # 执行计算
        result = eval(expression, {"__builtins__": {}}, safe_env)
        
        return f"科学计算结果: {result}"
    
    except Exception as e:
        logger.error(f"科学计算出错: {str(e)}")
        return f"科学计算错误: {str(e)}"


def _is_safe_expression(expression: str, include_scientific: bool = False) -> bool:
    """
    检查表达式是否安全
    
    Args:
        expression: 要检查的表达式
        include_scientific: 是否包含科学计算函数
        
    Returns:
        表达式是否安全
    """
    # 只允许数字、基本运算符和括号
    allowed_pattern = r'^[\d\s\+\-\*\/\(\)\.\,\^\%]+$'
    
    # 如果表达式只包含允许的字符，则初步认为安全
    if re.match(allowed_pattern, expression):
        return True
    
    # 基本允许的数学函数
    allowed_functions = [
        'abs', 'round', 'min', 'max', 'sum', 'pow'
    ]
    
    # 添加科学计算函数
    if include_scientific:
        allowed_functions.extend([
            'sqrt', 'sin', 'cos', 'tan', 'asin', 'acos', 'atan',
            'log', 'log10', 'exp', 'floor', 'ceil', 'pi', 'e'
        ])
    
    # 提取可能的函数调用
    function_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
    potential_functions = re.findall(function_pattern, expression)
    
    # 检查所有潜在函数是否都在允许列表中
    for func in potential_functions:
        if func not in allowed_functions:
            return False
    
    return True 