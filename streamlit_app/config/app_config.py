"""
应用配置模块

管理Streamlit应用的配置信息
"""

import os
import json
from typing import Dict, Any, Optional
import streamlit as st

# 默认配置
DEFAULT_CONFIG = {
    "app_name": "SSS Agent Platform - 企业连接器",
    "version": "1.0.0",
    "build_year": "2023",
    "theme": {
        "primary_color": "#FF4B4B",
        "background_color": "#FFFFFF",
        "secondary_background_color": "#F0F2F6",
        "text_color": "#262730",
        "font": "sans-serif"
    },
    "connectors": {
        "http": {
            "base_url": "http://localhost",
            "port": 8000,
            "enabled": True
        },
        "sse": {
            "base_url": "http://localhost",
            "port": 8001,
            "enabled": True
        }
    },
    "auth": {
        "default_user_id": "test_user",
        "default_roles": ["user"],
        "check_auth": False
    }
}

CONFIG_FILE_PATH = "streamlit_app/config/config.json"

def load_config() -> Dict[str, Any]:
    """加载配置信息
    
    从配置文件加载配置，如果文件不存在则返回默认配置
    
    Returns:
        配置字典
    """
    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config
        except Exception as e:
            st.error(f"加载配置文件失败: {e}")
            return DEFAULT_CONFIG
    else:
        # 如果配置文件不存在，创建一个默认的
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

def save_config(config: Dict[str, Any]) -> bool:
    """保存配置信息
    
    将配置保存到配置文件
    
    Args:
        config: 要保存的配置字典
        
    Returns:
        是否保存成功
    """
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE_PATH), exist_ok=True)
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"保存配置文件失败: {e}")
        return False

def get_connector_config(connector_type: str) -> Dict[str, Any]:
    """获取特定连接器的配置
    
    Args:
        connector_type: 连接器类型（'http'或'sse'）
        
    Returns:
        连接器配置字典
    """
    config = load_config()
    return config.get("connectors", {}).get(connector_type, {})

def update_connector_config(connector_type: str, new_config: Dict[str, Any]) -> bool:
    """更新特定连接器的配置
    
    Args:
        connector_type: 连接器类型（'http'或'sse'）
        new_config: 新的连接器配置
        
    Returns:
        是否更新成功
    """
    config = load_config()
    if "connectors" not in config:
        config["connectors"] = {}
    
    config["connectors"][connector_type] = new_config
    return save_config(config)

def get_app_info() -> Dict[str, str]:
    """获取应用信息
    
    Returns:
        包含应用名称、版本和构建年份的字典
    """
    config = load_config()
    return {
        "app_name": config.get("app_name", DEFAULT_CONFIG["app_name"]),
        "version": config.get("version", DEFAULT_CONFIG["version"]),
        "build_year": config.get("build_year", DEFAULT_CONFIG["build_year"])
    }

def get_theme() -> Dict[str, str]:
    """获取应用主题配置
    
    Returns:
        主题配置字典
    """
    config = load_config()
    return config.get("theme", DEFAULT_CONFIG["theme"])

def get_auth_config() -> Dict[str, Any]:
    """获取认证配置
    
    Returns:
        认证配置字典
    """
    config = load_config()
    return config.get("auth", DEFAULT_CONFIG["auth"]) 