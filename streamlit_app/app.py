#!/usr/bin/env python
"""
SSS Agent Platform - 企业连接器

这是一个基于Streamlit的应用，提供与各种智能体交互的界面。
该应用支持多种连接器类型，并提供了一个统一的用户界面进行交互。
"""

import streamlit as st
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径，确保可以导入相关模块
ROOT_DIR = Path(__file__).parent.absolute()
sys.path.append(str(ROOT_DIR))

# 导入组件和工具
from components.sidebar import render_sidebar
from components.chat_interface import render_chat_interface
from utils.session_state import init_session_state, load_settings_from_file

def init_app():
    """初始化应用，创建必要的目录和配置"""
    # 创建必要的目录
    directories = ["images", "config", "data", "temp"]
    for directory in directories:
        os.makedirs(os.path.join(ROOT_DIR, directory), exist_ok=True)
    
    # 检查logo是否存在，不存在则尝试生成
    logo_path = os.path.join(ROOT_DIR, "images", "logo.png")
    if not os.path.exists(logo_path):
        try:
            from utils.create_logo import create_simple_logo
            create_simple_logo()
            print(f"已生成logo: {logo_path}")
        except Exception as e:
            print(f"生成logo失败: {str(e)}")
    
    # 尝试加载用户设置
    settings_path = os.path.join(ROOT_DIR, "config", "user_settings.json")
    if os.path.exists(settings_path):
        load_settings_from_file(settings_path)

def configure_page():
    """配置页面标题、图标和布局"""
    # 尝试使用自定义logo
    logo_path = os.path.join(ROOT_DIR, "images", "logo.png")
    if os.path.exists(logo_path):
        st.set_page_config(
            page_title="SSS Agent Platform",
            page_icon=logo_path,
            layout="wide",
            initial_sidebar_state="expanded"
        )
    else:
        # 使用默认图标
        st.set_page_config(
            page_title="SSS Agent Platform",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )

def main():
    """主函数，应用程序入口点"""
    # 配置页面
    configure_page()
    
    # 初始化应用
    init_app()
    
    # 初始化会话状态
    init_session_state()
    
    # 渲染侧边栏
    render_sidebar()
    
    # 渲染聊天界面
    render_chat_interface()

if __name__ == "__main__":
    main() 