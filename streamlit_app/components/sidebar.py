"""
侧边栏组件

提供配置面板，用于模拟第三方业务系统的设置，包括用户身份、API配置、权限和连接设置
"""

import streamlit as st
import sys
import os
from typing import Dict, Any, List

# 确保可以导入相关模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import session_state

def render_sidebar():
    """渲染侧边栏配置面板"""
    with st.sidebar:
        st.title("SSS Agent Platform")
        st.caption("企业连接器配置")
        
        # 添加分隔线
        st.divider()
        
        # 渲染用户身份设置
        render_user_settings()
        
        # 添加分隔线
        st.divider()
        
        # 渲染API设置
        render_api_settings()
        
        # 添加分隔线
        st.divider()
        
        # 渲染权限设置
        render_permission_settings()
        
        # 添加分隔线
        st.divider()
        
        # 渲染连接设置
        render_connection_settings()
        
        # 添加分隔线
        st.divider()
        
        # 底部显示版本信息
        st.caption("版本 v1.0.0")
        st.caption("© 2023-2024 SSS Tech")

def render_user_settings():
    """渲染用户身份设置"""
    st.subheader("🧑‍💼 用户身份")
    
    # 用户ID
    user_id = st.text_input(
        "用户ID", 
        value=st.session_state.get("user_id", "user123"), 
        key="user_id_input"
    )
    if user_id != st.session_state.get("user_id"):
        st.session_state.user_id = user_id
    
    # 用户角色选择
    default_roles = st.session_state.get("user_roles", ["普通用户"])
    available_roles = ["普通用户", "管理员", "财务", "人力资源", "技术支持", "客服"]
    
    selected_roles = st.multiselect(
        "用户角色", 
        options=available_roles,
        default=default_roles,
        key="user_roles_input"
    )
    
    if selected_roles != st.session_state.get("user_roles"):
        st.session_state.user_roles = selected_roles
    
    # 用户部门
    departments = ["销售部", "技术部", "人事部", "财务部", "客服部", "市场部"]
    department = st.selectbox(
        "所属部门",
        options=departments,
        index=departments.index(st.session_state.get("department", "技术部")),
        key="department_input"
    )
    
    if department != st.session_state.get("department"):
        st.session_state.department = department
    
    # 更新认证上下文
    session_state.set_auth_context({
        "user_id": user_id,
        "roles": selected_roles,
        "department": department,
        "auth_tokens": {
            "access_token": f"simulated_token_{user_id}",
            "refresh_token": f"simulated_refresh_{user_id}"
        }
    })

def render_api_settings():
    """渲染API设置"""
    st.subheader("🔌 API设置")
    
    # API地址
    api_url = st.text_input(
        "API地址", 
        value=st.session_state.get("api_url", "http://localhost:8000"),
        key="api_url_input"
    )
    if api_url != st.session_state.get("api_url"):
        st.session_state.api_url = api_url
    
    # API类型
    api_types = ["HTTP", "HTTPS", "WebSocket", "gRPC"]
    api_type = st.selectbox(
        "API类型",
        options=api_types,
        index=api_types.index(st.session_state.get("api_type", "HTTP")),
        key="api_type_input"
    )
    if api_type != st.session_state.get("api_type"):
        st.session_state.api_type = api_type
    
    # 模型选择
    models = ["gpt-4", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet", "gemini-pro", "llama-3-70b"]
    model_id = st.selectbox(
        "模型选择",
        options=models,
        index=models.index(st.session_state.get("model_id", "gpt-4")),
        key="model_id_input"
    )
    if model_id != st.session_state.get("model_id"):
        st.session_state.model_id = model_id

def render_permission_settings():
    """渲染权限设置"""
    st.subheader("🔐 权限设置")
    
    # 访问权限
    access_levels = ["只读", "读写", "管理员"]
    access_level = st.selectbox(
        "访问级别",
        options=access_levels,
        index=access_levels.index(st.session_state.get("access_level", "读写")),
        key="access_level_input"
    )
    if access_level != st.session_state.get("access_level"):
        st.session_state.access_level = access_level
    
    # 功能权限
    feature_permissions = [
        "查看报表", "导出数据", "上传文件", "编辑配置", 
        "管理用户", "调用高级API", "执行工作流", "批量操作"
    ]
    
    default_permissions = st.session_state.get(
        "feature_permissions", 
        ["查看报表", "导出数据", "上传文件"]
    )
    
    selected_permissions = st.multiselect(
        "功能权限",
        options=feature_permissions,
        default=default_permissions,
        key="feature_permissions_input"
    )
    
    if selected_permissions != st.session_state.get("feature_permissions"):
        st.session_state.feature_permissions = selected_permissions
    
    # 数据访问范围
    data_scopes = ["全部数据", "部门数据", "个人数据"]
    data_scope = st.selectbox(
        "数据访问范围",
        options=data_scopes,
        index=data_scopes.index(st.session_state.get("data_scope", "部门数据")),
        key="data_scope_input"
    )
    if data_scope != st.session_state.get("data_scope"):
        st.session_state.data_scope = data_scope

def render_connection_settings():
    """渲染连接设置"""
    st.subheader("⚙️ 连接设置")
    
    # 启用流式响应
    enable_streaming = st.toggle(
        "启用流式响应",
        value=st.session_state.get("enable_streaming", True),
        key="enable_streaming_input"
    )
    if enable_streaming != st.session_state.get("enable_streaming"):
        st.session_state.enable_streaming = enable_streaming
    
    # 超时设置
    timeout = st.slider(
        "请求超时(秒)",
        min_value=5,
        max_value=120,
        value=st.session_state.get("timeout", 30),
        step=5,
        key="timeout_input"
    )
    if timeout != st.session_state.get("timeout"):
        st.session_state.timeout = timeout
    
    # 最大重试次数
    max_retries = st.slider(
        "最大重试次数",
        min_value=0,
        max_value=5,
        value=st.session_state.get("max_retries", 2),
        step=1,
        key="max_retries_input"
    )
    if max_retries != st.session_state.get("max_retries"):
        st.session_state.max_retries = max_retries 