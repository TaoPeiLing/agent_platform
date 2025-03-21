"""
聊天界面组件

提供统一的聊天界面，支持与智能体进行多轮对话
"""

import streamlit as st
import json
import time
from datetime import datetime
import sys
import os
import requests
import uuid
from typing import Dict, Any, List, Optional

# 确保可以导入相关模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import session_state

def render_chat_interface():
    """渲染聊天界面"""
    # 初始化聊天历史
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # 添加默认欢迎消息
        st.session_state.messages.append({
            "role": "assistant",
            "content": "代码问题，就问Eagle! 请告诉我您需要分析的项目或问题。"
        })
    
    # 设置页面样式为深色主题，与侧边栏颜色一致
    st.markdown("""
    <style>
    /* 整体背景色调整为更深的颜色，与侧边栏保持一致 */
    .stApp {
        background-color: #0E1117;
        color: white;
    }
    /* 调整主内容区域 */
    .main .block-container {
        background-color: #0E1117;
    }
    /* 聊天消息样式 */
    .chat-message {
        padding: 10px 20px;
        border-radius: 10px;
        margin-bottom: 10px;
        max-width: 80%;
    }
    /* 输入框样式 */
    .stChatInputContainer {
        margin-bottom: 20px;
    }
    /* 自定义聊天输入框 */
    .stChatInput {
        background-color: #262730 !important;
        border-color: #4D4D4D !important;
    }
    /* 自定义聊天消息样式 */
    .stChatMessage {
        background-color: #262730 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 创建一个主容器
    main_container = st.container()
    
    with main_container:
        # 1. 聊天历史区域
        chat_container = st.container()
        with chat_container:
            # 显示聊天历史
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
        
        # 2. 显示正在输入状态
        if "is_processing" in st.session_state and st.session_state.is_processing:
            with st.chat_message("assistant"):
                st.write("思考中...")
    
    # 3. 聊天输入框
    prompt = st.chat_input("向 AI 提问......", disabled=st.session_state.get("is_processing", False))
    if prompt:
        ask_question(prompt)
    
    # 不在这里添加页脚，因为app.py中已经有了页脚
    # 主应用中的页脚会自然显示在输入框下方

def ask_question(prompt: str):
    """处理用户问题并获取回答
    
    Args:
        prompt: 用户输入的问题
    """
    # 添加用户消息到聊天历史
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 标记处理状态
    st.session_state.is_processing = True
    
    # 重新渲染页面以显示用户消息
    st.rerun()
    
    # 处理用户输入并获取回答
    response_text = process_user_input(prompt)
    
    # 添加助手响应到聊天历史
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text
    })
    
    # 重置处理状态
    st.session_state.is_processing = False
    
    # 重新渲染页面以显示新消息
    st.rerun()

def process_user_input(prompt: str) -> str:
    """处理用户输入并获取智能体响应
    
    Args:
        prompt: 用户输入的文本
        
    Returns:
        智能体的响应文本
    """
    try:
        # 准备请求参数
        api_url = st.session_state.get("api_url", "http://localhost:8000")
        api_type = st.session_state.get("api_type", "HTTP")
        model_id = st.session_state.get("model_id", "gpt-4")
        enable_streaming = st.session_state.get("enable_streaming", True)
        
        # 获取认证上下文
        auth_context = session_state.get_auth_context()
        
        # 创建会话ID
        if "session_id" not in st.session_state or not st.session_state.session_id:
            st.session_state.session_id = str(uuid.uuid4())
        
        # 获取历史消息
        messages = [
            {"role": msg["role"], "content": msg["content"]} 
            for msg in st.session_state.messages
        ]
        
        # 模拟延迟
        time.sleep(0.8)
        
        # 模拟响应
        return simulate_api_response(prompt)
    
    except Exception as e:
        # 返回错误消息
        return f"处理请求时出错: {str(e)}"

def simulate_api_response(prompt: str) -> str:
    """模拟API响应
    
    Args:
        prompt: 用户输入的文本
        
    Returns:
        模拟的响应文本
    """
    # 简单的关键词响应逻辑
    if "github" in prompt.lower():
        return f"我看到您要分析的是GitHub项目。Eagle可以深入分析这个代码库并提供详细解读。实际使用中，我会连接到后端分析引擎，对整个项目进行扫描和理解。请问您对这个项目有什么具体问题？"
    
    elif "wordpress" in prompt.lower():
        return "WordPress 5.0和6.0版本之间编辑器功能的主要升级包括:\n\n1. Gutenberg编辑器的完善和性能优化\n2. 添加了更多区块类型和模板选项\n3. 改进了编辑器的用户界面和可访问性\n4. 增强了全站编辑功能\n5. 提供了更多样化的区块模式和样式选项"
    
    elif "分析" in prompt or "理解" in prompt:
        return f"关于\"{prompt}\"，我需要先分析相关代码库的结构和实现。Eagle会扫描整个项目代码，理解其架构设计、关键组件和实现方式。在实际使用中，我会提供详细的代码分析报告和解释。"
    
    else:
        return f"我收到了您的问题：\"{prompt}\"。作为代码分析AI，Eagle可以帮助您理解项目代码、解释实现细节、分析架构设计等。您可以提供GitHub链接或上传代码压缩包，我将为您深入分析。" 