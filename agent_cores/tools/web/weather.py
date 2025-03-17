"""
天气工具模块 - 提供天气查询功能

包含两个主要函数：
1. search_weather: 搜索指定城市的天气信息
2. weather_tool: 对接代理的天气查询工具函数
"""
import logging
import random
from datetime import datetime
from typing import Dict, Any, Optional

# 配置日志
logger = logging.getLogger(__name__)

# 模拟天气数据
WEATHER_DATA = {
    "北京": {
        "temp_range": (-10, 40),  # 温度范围（摄氏度）
        "conditions": ["晴朗", "多云", "阴天", "小雨", "大雨", "雷雨", "雾霾"],
        "humidity_range": (20, 95),  # 湿度范围（百分比）
        "wind_range": (0, 50)  # 风速范围（公里/小时）
    },
    "上海": {
        "temp_range": (0, 40),
        "conditions": ["晴朗", "多云", "阴天", "小雨", "大雨", "台风"],
        "humidity_range": (30, 100),
        "wind_range": (0, 60)
    },
    "广州": {
        "temp_range": (10, 40),
        "conditions": ["晴朗", "多云", "阴天", "小雨", "大雨", "雷雨"],
        "humidity_range": (40, 100),
        "wind_range": (0, 40)
    },
    "深圳": {
        "temp_range": (15, 40),
        "conditions": ["晴朗", "多云", "阴天", "小雨", "大雨"],
        "humidity_range": (45, 100),
        "wind_range": (0, 35)
    },
    "成都": {
        "temp_range": (0, 35),
        "conditions": ["晴朗", "多云", "阴天", "小雨", "雾"],
        "humidity_range": (40, 95),
        "wind_range": (0, 30)
    },
    "重庆": {
        "temp_range": (5, 40),
        "conditions": ["晴朗", "多云", "阴天", "小雨", "大雨", "雾"],
        "humidity_range": (40, 95),
        "wind_range": (0, 30)
    },
    "杭州": {
        "temp_range": (0, 40),
        "conditions": ["晴朗", "多云", "阴天", "小雨", "大雨", "雷雨"],
        "humidity_range": (30, 95),
        "wind_range": (0, 40)
    },
    "南京": {
        "temp_range": (-5, 40),
        "conditions": ["晴朗", "多云", "阴天", "小雨", "大雨", "雷雨"],
        "humidity_range": (30, 95),
        "wind_range": (0, 40)
    },
    "武汉": {
        "temp_range": (-5, 40),
        "conditions": ["晴朗", "多云", "阴天", "小雨", "大雨", "雷雨", "雾"],
        "humidity_range": (30, 95),
        "wind_range": (0, 40)
    },
    "西安": {
        "temp_range": (-10, 40),
        "conditions": ["晴朗", "多云", "阴天", "小雨", "大雨", "沙尘暴"],
        "humidity_range": (20, 90),
        "wind_range": (0, 50)
    },
    "天津": {
        "temp_range": (-10, 40),
        "conditions": ["晴朗", "多云", "阴天", "小雨", "雾霾"],
        "humidity_range": (20, 90),
        "wind_range": (0, 45)
    },
    "苏州": {
        "temp_range": (0, 40),
        "conditions": ["晴朗", "多云", "阴天", "小雨", "大雨"],
        "humidity_range": (35, 95),
        "wind_range": (0, 35)
    },
    "沈阳": {
        "temp_range": (-25, 35),
        "conditions": ["晴朗", "多云", "阴天", "小雪", "大雪", "暴雪"],
        "humidity_range": (20, 85),
        "wind_range": (0, 40)
    },
    "哈尔滨": {
        "temp_range": (-30, 30),
        "conditions": ["晴朗", "多云", "阴天", "小雪", "大雪", "暴雪"],
        "humidity_range": (20, 85),
        "wind_range": (0, 40)
    },
    "拉萨": {
        "temp_range": (-15, 25),
        "conditions": ["晴朗", "多云", "阴天", "小雪"],
        "humidity_range": (10, 60),
        "wind_range": (0, 30)
    },
    "乌鲁木齐": {
        "temp_range": (-30, 35),
        "conditions": ["晴朗", "多云", "阴天", "小雪", "大雪", "沙尘暴"],
        "humidity_range": (15, 70),
        "wind_range": (0, 60)
    }
}

# 默认使用的城市，当请求的城市不存在时使用
DEFAULT_CITY = "北京"


def search_weather(city: str) -> str:
    """
    搜索指定城市的天气信息
    
    Args:
        city: 城市名称
        
    Returns:
        天气信息字符串
    """
    logger.info(f"查询天气: {city}")
    
    # 规范化城市名称
    city = _normalize_city_name(city)
    
    # 检查城市是否存在
    if city not in WEATHER_DATA:
        logger.warning(f"未找到城市: {city}，使用默认城市: {DEFAULT_CITY}")
        city = DEFAULT_CITY
    
    # 获取天气信息
    weather_info = _generate_weather(city)
    
    # 格式化天气信息
    formatted_info = (
        f"{city}天气：\n"
        f"温度: {weather_info['temperature']}°C (体感温度: {weather_info['feels_like']}°C)\n"
        f"天气状况: {weather_info['condition']}\n"
        f"湿度: {weather_info['humidity']}%\n"
        f"风速: {weather_info['wind_speed']} km/h\n"
        f"更新时间: {weather_info['updated_time']}"
    )
    
    return formatted_info


def weather_tool(city: str) -> Dict[str, Any]:
    """
    天气查询工具 - 用于代理调用的函数
    
    Args:
        city: 城市名称
        
    Returns:
        包含天气信息的字典
    """
    logger.info(f"使用天气工具查询: {city}")
    
    # 规范化城市名称
    city = _normalize_city_name(city)
    
    # 检查城市是否存在
    if city not in WEATHER_DATA:
        logger.warning(f"未找到城市: {city}，使用默认城市: {DEFAULT_CITY}")
        city = DEFAULT_CITY
    
    # 获取天气信息
    weather_info = _generate_weather(city)
    
    # 返回结果
    return {
        "city": city,
        "temperature": weather_info["temperature"],
        "feels_like": weather_info["feels_like"],
        "condition": weather_info["condition"],
        "humidity": weather_info["humidity"],
        "wind_speed": weather_info["wind_speed"],
        "updated_time": weather_info["updated_time"],
        "error": False
    }


def _normalize_city_name(city: str) -> str:
    """
    规范化城市名称
    
    Args:
        city: 原始城市名称
        
    Returns:
        规范化后的城市名称
    """
    # 去除空格和特殊字符
    city = city.strip()
    
    # 处理常见的城市名称变体
    city_mapping = {
        "北京市": "北京",
        "上海市": "上海",
        "广州市": "广州",
        "深圳市": "深圳",
        "成都市": "成都",
        "beijing": "北京",
        "shanghai": "上海",
        "guangzhou": "广州",
        "shenzhen": "深圳",
        "chengdu": "成都"
    }
    
    # 如果有映射，使用映射后的名称
    return city_mapping.get(city.lower(), city)


def _generate_weather(city: str) -> Dict[str, Any]:
    """
    生成城市天气信息
    
    Args:
        city: 城市名称
        
    Returns:
        天气信息字典
    """
    city_data = WEATHER_DATA.get(city, WEATHER_DATA[DEFAULT_CITY])
    
    # 生成随机天气数据
    temp_min, temp_max = city_data["temp_range"]
    temperature = round(random.uniform(temp_min, temp_max), 1)
    
    # 根据季节调整温度
    now = datetime.now()
    month = now.month
    
    # 冬季 (12-2月)
    if month in [12, 1, 2]:
        temperature = min(temperature, round(random.uniform(temp_min, temp_min + (temp_max - temp_min) * 0.4), 1))
    # 春秋季 (3-5月, 9-11月)
    elif month in [3, 4, 5, 9, 10, 11]:
        temperature = round(random.uniform(temp_min + (temp_max - temp_min) * 0.2, temp_min + (temp_max - temp_min) * 0.7), 1)
    # 夏季 (6-8月)
    else:
        temperature = max(temperature, round(random.uniform(temp_min + (temp_max - temp_min) * 0.6, temp_max), 1))
    
    # 选择天气状况
    condition = random.choice(city_data["conditions"])
    
    # 计算体感温度
    feels_like = temperature
    
    # 如果有风，体感温度会降低
    wind_speed = round(random.uniform(*city_data["wind_range"]), 1)
    if wind_speed > 20:
        feels_like -= round(random.uniform(1, 3), 1)
    
    # 如果湿度高，体感温度会升高（夏季）或降低（冬季）
    humidity = round(random.uniform(*city_data["humidity_range"]))
    if humidity > 80:
        if temperature > 25:  # 夏季
            feels_like += round(random.uniform(1, 3), 1)
        elif temperature < 5:  # 冬季
            feels_like -= round(random.uniform(1, 2), 1)
    
    # 根据天气状况调整
    if condition in ["小雨", "大雨", "雷雨"]:
        feels_like -= round(random.uniform(0.5, 2), 1)
    elif condition in ["小雪", "大雪", "暴雪"]:
        feels_like -= round(random.uniform(1.5, 4), 1)
    
    # 更新时间
    updated_time = now.strftime("%Y-%m-%d %H:%M:%S")
    
    return {
        "temperature": temperature,
        "feels_like": round(feels_like, 1),
        "condition": condition,
        "humidity": humidity,
        "wind_speed": wind_speed,
        "updated_time": updated_time
    } 