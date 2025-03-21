"""
会话状态管理工具

提供管理Streamlit会话状态的功能，包括初始化会话状态、存储和检索认证上下文等
"""

import streamlit as st
from typing import Dict, Any, List, Optional
import json
import os
import logging

def init_session_state():
    """初始化会话状态，确保所有必要的键都存在"""
    # 用户和认证相关
    if "user_id" not in st.session_state:
        st.session_state.user_id = "user123"
    
    if "user_roles" not in st.session_state:
        st.session_state.user_roles = ["普通用户"]
    
    if "department" not in st.session_state:
        st.session_state.department = "技术部"
    
    if "auth_context" not in st.session_state:
        st.session_state.auth_context = {
            "user_id": st.session_state.user_id,
            "roles": st.session_state.user_roles,
            "department": st.session_state.department,
            "auth_tokens": {
                "access_token": f"simulated_token_{st.session_state.user_id}",
                "refresh_token": f"simulated_refresh_{st.session_state.user_id}"
            }
        }
    
    # API配置相关
    if "api_url" not in st.session_state:
        st.session_state.api_url = "http://localhost:8000"
    
    if "api_type" not in st.session_state:
        st.session_state.api_type = "HTTP"
    
    if "model_id" not in st.session_state:
        st.session_state.model_id = "gpt-4"
    
    # 权限相关
    if "access_level" not in st.session_state:
        st.session_state.access_level = "读写"
    
    if "feature_permissions" not in st.session_state:
        st.session_state.feature_permissions = ["查看报表", "导出数据", "上传文件"]
    
    if "data_scope" not in st.session_state:
        st.session_state.data_scope = "部门数据"
    
    # 连接设置相关
    if "enable_streaming" not in st.session_state:
        st.session_state.enable_streaming = True
    
    if "timeout" not in st.session_state:
        st.session_state.timeout = 30
    
    if "max_retries" not in st.session_state:
        st.session_state.max_retries = 2
    
    # 聊天相关
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "session_id" not in st.session_state:
        st.session_state.session_id = ""
    
    # 其他设置
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False

def get_auth_context() -> Dict[str, Any]:
    """获取当前认证上下文
    
    Returns:
        包含认证信息的字典
    """
    if "auth_context" not in st.session_state:
        init_session_state()
    
    return st.session_state.auth_context

def set_auth_context(auth_context: Dict[str, Any]) -> None:
    """设置认证上下文
    
    Args:
        auth_context: 包含认证信息的字典
    """
    st.session_state.auth_context = auth_context

def has_permission(permission: str) -> bool:
    """检查当前用户是否拥有指定权限
    
    Args:
        permission: 要检查的权限名称
        
    Returns:
        如果用户拥有该权限，返回True，否则返回False
    """
    # 管理员拥有所有权限
    if "管理员" in st.session_state.get("user_roles", []):
        return True
    
    # 检查用户是否拥有该功能权限
    return permission in st.session_state.get("feature_permissions", [])

def save_settings_to_file(filepath: str = "config/user_settings.json") -> bool:
    """将当前会话状态保存到文件
    
    Args:
        filepath: 保存设置的文件路径
        
    Returns:
        如果保存成功，返回True，否则返回False
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 收集需要保存的设置
        settings = {
            "user_id": st.session_state.get("user_id", "user123"),
            "user_roles": st.session_state.get("user_roles", ["普通用户"]),
            "department": st.session_state.get("department", "技术部"),
            "api_url": st.session_state.get("api_url", "http://localhost:8000"),
            "api_type": st.session_state.get("api_type", "HTTP"),
            "model_id": st.session_state.get("model_id", "gpt-4"),
            "access_level": st.session_state.get("access_level", "读写"),
            "feature_permissions": st.session_state.get("feature_permissions", []),
            "data_scope": st.session_state.get("data_scope", "部门数据"),
            "enable_streaming": st.session_state.get("enable_streaming", True),
            "timeout": st.session_state.get("timeout", 30),
            "max_retries": st.session_state.get("max_retries", 2)
        }
        
        # 保存到文件
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        
        return True
    
    except Exception as e:
        logging.error(f"保存设置失败: {str(e)}")
        return False

def load_settings_from_file(filepath: str = "config/user_settings.json") -> bool:
    """从文件加载设置到会话状态
    
    Args:
        filepath: 设置文件的路径
        
    Returns:
        如果加载成功，返回True，否则返回False
    """
    try:
        if not os.path.exists(filepath):
            return False
        
        # 从文件加载设置
        with open(filepath, "r", encoding="utf-8") as f:
            settings = json.load(f)
        
        # 更新会话状态
        for key, value in settings.items():
            if key in st.session_state:
                st.session_state[key] = value
        
        # 更新认证上下文
        set_auth_context({
            "user_id": settings.get("user_id", "user123"),
            "roles": settings.get("user_roles", ["普通用户"]),
            "department": settings.get("department", "技术部"),
            "auth_tokens": {
                "access_token": f"simulated_token_{settings.get('user_id', 'user123')}",
                "refresh_token": f"simulated_refresh_{settings.get('user_id', 'user123')}"
            }
        })
        
        return True
    
    except Exception as e:
        logging.error(f"加载设置失败: {str(e)}")
        return False 