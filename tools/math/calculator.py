"""
计算器工具模块 - 提供基本计算和单位转换功能

包含两个主要工具函数：
1. calculator_tool: 执行基本数学运算
2. converter_tool: 执行单位转换
"""
import logging
import math
import re
from typing import Dict, Any, Union, Optional, TYPE_CHECKING

# 类型检查时导入，避免循环导入
if TYPE_CHECKING:
    from agent_cores.core.agent_context import AgentContext
    from agents.run_context import RunContextWrapper

# 配置日志
logger = logging.getLogger(__name__)

# 导入工具注册装饰器
from agent_cores.tools.core.tool_registry import register_tool

# 单位转换常量
UNIT_CONVERSIONS = {
    # 长度单位转换 (转换为米)
    "length": {
        "mm": 0.001,     # 毫米
        "cm": 0.01,      # 厘米
        "m": 1.0,        # 米
        "km": 1000.0,    # 千米
        "inch": 0.0254,  # 英寸
        "ft": 0.3048,    # 英尺
        "yd": 0.9144,    # 码
        "mi": 1609.344   # 英里
    },
    # 重量单位转换 (转换为克)
    "weight": {
        "mg": 0.001,     # 毫克
        "g": 1.0,        # 克
        "kg": 1000.0,    # 千克
        "t": 1000000.0,  # 吨
        "oz": 28.349523, # 盎司
        "lb": 453.59237, # 磅
    },
    # 体积单位转换 (转换为升)
    "volume": {
        "ml": 0.001,     # 毫升
        "l": 1.0,        # 升
        "m3": 1000.0,    # 立方米
        "gal": 3.78541,  # 加仑(美制)
        "pt": 0.473176,  # 品脱(美制)
    },
    # 温度单位转换 (特殊处理)
    "temperature": {
        "c": "celsius",     # 摄氏度
        "f": "fahrenheit",  # 华氏度
        "k": "kelvin"       # 开尔文
    }
}


@register_tool(
    category="math",
    description="执行基本数学运算，如加减乘除、三角函数等",
    tags=["math", "calculation"]
)
def calculator_tool(expression: str) -> Dict[str, Any]:
    """
    计算器工具 - 执行基本数学运算
    
    Args:
        expression: 要计算的数学表达式
        
    Returns:
        包含计算结果的字典
    """
    try:
        # 清理输入
        expression = expression.strip()
        
        # 检查表达式是否安全
        if not is_safe_expression(expression):
            return {
                "success": False,
                "error": True,
                "message": "不安全的表达式，只允许基本数学运算"
            }
        
        # 为了计算更加安全，使用有限制的环境
        # 只允许使用数学相关函数
        safe_env = {
            "abs": abs, 
            "round": round, 
            "min": min, 
            "max": max,
            "sum": sum, 
            "pow": pow, 
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "log10": math.log10,
            "pi": math.pi,
            "e": math.e
        }
        
        # 安全计算表达式
        result = eval(expression, {"__builtins__": {}}, safe_env)
        
        return {
            "success": True,
            "expression": expression,
            "result": result,
            "error": False
        }
        
    except Exception as e:
        logger.error(f"计算错误: {str(e)}")
        return {
            "success": False,
            "expression": expression,
            "error": True,
            "message": f"计算错误: {str(e)}"
        }


@register_tool(
    category="math",
    description="执行单位转换，如长度、重量、体积和温度的单位转换",
    tags=["math", "conversion", "units"]
)
def converter_tool(value: Union[float, int], from_unit: str, to_unit: str) -> Dict[str, Any]:
    """
    单位转换工具 - 转换不同单位的值
    
    Args:
        value: 要转换的值
        from_unit: 源单位
        to_unit: 目标单位
        
    Returns:
        包含转换结果的字典
    """
    try:
        # 将单位转为小写
        from_unit = from_unit.lower()
        to_unit = to_unit.lower()
        
        # 检查单位类型
        unit_type = get_unit_type(from_unit, to_unit)
        
        if not unit_type:
            return {
                "success": False,
                "error": True,
                "message": f"不支持的单位转换: {from_unit} -> {to_unit}"
            }
        
        # 温度单位转换需要特殊处理
        if unit_type == "temperature":
            converted_value = convert_temperature(value, from_unit, to_unit)
        else:
            # 其他单位的转换（通过基准单位）
            base_unit_value = value * UNIT_CONVERSIONS[unit_type][from_unit]
            converted_value = base_unit_value / UNIT_CONVERSIONS[unit_type][to_unit]
        
        return {
            "success": True,
            "value": value,
            "from_unit": from_unit,
            "to_unit": to_unit,
            "result": converted_value,
            "unit_type": unit_type,
            "error": False
        }
        
    except Exception as e:
        logger.error(f"单位转换错误: {str(e)}")
        return {
            "success": False,
            "error": True,
            "message": f"单位转换错误: {str(e)}"
        }


def is_safe_expression(expression: str) -> bool:
    """
    检查表达式是否安全 - 仅允许基本数学运算
    
    Args:
        expression: 要检查的表达式
        
    Returns:
        是否安全
    """
    # 删除空格
    expression = expression.replace(" ", "")
    
    # 检查是否包含不安全的字符或模式
    unsafe_patterns = [
        r"import",
        r"exec",
        r"eval",
        r"compile",
        r"__",        # 双下划线通常表示特殊方法
        r"globals",
        r"locals",
        r"getattr",
        r"setattr",
        r"delattr",
        r"open",
        r"file",
        r"os\.",
        r"sys\.",
        r"subprocess",
        r"lambda"
    ]
    
    for pattern in unsafe_patterns:
        if re.search(pattern, expression, re.IGNORECASE):
            return False
    
    # 检查是否只包含允许的字符
    allowed_chars = r"[0-9\+\-\*\/\(\)\.\,\s\%abcdefghijklmnopqrstuvwxyzπ]"
    if not re.match(f"^{allowed_chars}+$", expression, re.IGNORECASE):
        return False
        
    return True


def get_unit_type(unit1: str, unit2: str) -> Optional[str]:
    """
    获取单位类型 - 确定两个单位所属的类型
    
    Args:
        unit1: 第一个单位
        unit2: 第二个单位
        
    Returns:
        单位类型，如果单位不兼容则返回None
    """
    # 查找每个单位所属的类型
    unit1_type = None
    unit2_type = None
    
    for unit_type, units in UNIT_CONVERSIONS.items():
        if unit1 in units:
            unit1_type = unit_type
        if unit2 in units:
            unit2_type = unit_type
    
    # 检查两个单位是否属于同一类型
    if unit1_type and unit2_type and unit1_type == unit2_type:
        return unit1_type
    
    return None


def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    """
    温度单位转换 - 转换不同的温度单位
    
    Args:
        value: 要转换的温度值
        from_unit: 源温度单位
        to_unit: 目标温度单位
        
    Returns:
        转换后的温度值
    """
    # 首先转换为摄氏度
    if from_unit == "f":
        celsius = (value - 32) * 5/9
    elif from_unit == "k":
        celsius = value - 273.15
    else:  # 摄氏度
        celsius = value
    
    # 然后从摄氏度转换为目标单位
    if to_unit == "f":
        return celsius * 9/5 + 32
    elif to_unit == "k":
        return celsius + 273.15
    else:  # 摄氏度
        return celsius 