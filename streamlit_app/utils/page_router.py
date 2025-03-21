"""
页面路由模块

处理Streamlit应用的页面路由，管理不同页面的导航和渲染。
"""

import streamlit as st
from typing import Dict, Any, List, Optional, Callable
import sys
import os

# 确保可以导入相关模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from pages import agent_page, workflow_page, auth_page, config_page
from components import dashboard

class PageRouter:
    """页面路由器，管理页面间的导航"""
    
    def __init__(self):
        """初始化路由器"""
        self.pages = {
            "dashboard": {
                "title": "仪表盘",
                "render_func": dashboard.render_dashboard,
                "icon": "📊"
            },
            "agent": {
                "title": "智能体调用",
                "render_func": agent_page.render_agent_page,
                "icon": "🤖"
            },
            "workflow": {
                "title": "工作流调用",
                "render_func": workflow_page.render_workflow_page,
                "icon": "🔄"
            },
            "auth": {
                "title": "认证管理",
                "render_func": auth_page.render_auth_page,
                "icon": "🔐"
            },
            "config": {
                "title": "高级配置",
                "render_func": config_page.render_config_page,
                "icon": "⚙️"
            }
        }
    
    def get_page_ids(self) -> List[str]:
        """获取所有页面ID
        
        Returns:
            页面ID列表
        """
        return list(self.pages.keys())
    
    def get_page_titles(self) -> Dict[str, str]:
        """获取所有页面标题
        
        Returns:
            页面ID到标题的映射字典
        """
        return {page_id: page_info["title"] for page_id, page_info in self.pages.items()}
    
    def render_current_page(self):
        """渲染当前选中的页面"""
        # 获取当前页面ID
        current_page_id = st.session_state.get("current_page", "dashboard")
        
        # 如果页面ID无效，默认使用仪表盘
        if current_page_id not in self.pages:
            current_page_id = "dashboard"
            st.session_state.current_page = current_page_id
        
        # 获取页面信息
        page_info = self.pages[current_page_id]
        
        # 调用渲染函数
        page_info["render_func"]()
    
    def navigate_to(self, page_id: str):
        """导航到指定页面
        
        Args:
            page_id: 目标页面ID
        
        Returns:
            是否导航成功
        """
        if page_id not in self.pages:
            return False
        
        st.session_state.current_page = page_id
        return True

# 创建全局路由器实例
router = PageRouter() 