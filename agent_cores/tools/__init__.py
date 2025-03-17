"""
工具模块包 - 包含各种工具实现
"""

from agent_cores.tools.web.weather import search_weather
from agent_cores.tools.data.database import DatabaseManager
from agent_cores.tools.data.file import FileManager
from agent_cores.tools.media.audio import text_to_speech, speech_to_text, play_audio, audio_info
from agent_cores.tools.web.network import http_request, download_file, check_url, ping
from agent_cores.tools.core.tool_manager import ToolManager
from agent_cores.tools.system.rbac_tools import (
    PermissionContext,
    check_permission,
    get_current_roles,
    list_allowed_tools,
    permission_guardrail
)

# 导入工具注册模块，确保工具被注册到工具管理器
import agent_cores.tools.register_tools

import logging

# 配置日志
logger = logging.getLogger(__name__)

# 创建工具管理器实例
tool_manager = ToolManager()

# 导入各种工具
from agent_cores.tools.math.calculator import calculator_tool, converter_tool
from agent_cores.tools.web.weather import weather_tool
from agent_cores.tools.example.diagnostics import diagnose_system

__all__ = [
    'search_weather',  # 天气查询工具
    'calculate',  # 基本计算工具
    'scientific_calculate',  # 科学计算工具
    'DatabaseManager',  # 数据库管理工具类
    'FileManager',  # 文件管理工具类
    'text_to_speech',  # 文本转语音工具
    'speech_to_text',  # 语音转文本工具
    'play_audio',  # 音频播放工具
    'audio_info',  # 音频信息工具
    'http_request',  # HTTP请求工具
    'download_file',  # 文件下载工具
    'check_url',  # URL检查工具
    'ping',  # Ping工具
    'ToolManager',  # 工具管理器类
    'tool_manager',  # 全局工具管理器实例

    # RBAC相关工具
    'PermissionContext',  # 权限上下文
    'check_permission',  # 权限检查工具
    'get_current_roles',  # 获取当前角色工具
    'list_allowed_tools',  # 列出允许工具的工具
    'permission_guardrail',  # 权限验证围栏

    'calculator_tool',
    'converter_tool',
    'weather_tool',
    'diagnose_system'
]


# 注册工具
def register_all_tools():
    """注册所有工具"""
    logger.info("正在注册所有工具...")

    # 注册计算器工具
    tool_manager.register_tool(calculator_tool)

    # 注册单位转换工具
    tool_manager.register_tool(converter_tool)

    # 注册天气工具
    tool_manager.register_tool(weather_tool)

    # 注册系统诊断工具
    tool_manager.register_tool(diagnose_system)

    # 注册文件操作工具
    file_manager = FileManager()
    tool_manager.register_tool(file_manager.read_file)
    tool_manager.register_tool(file_manager.write_file)
    tool_manager.register_tool(file_manager.list_files)

    # 注册音频处理工具
    tool_manager.register_tool(text_to_speech)
    tool_manager.register_tool(speech_to_text)
    tool_manager.register_tool(play_audio)
    tool_manager.register_tool(audio_info)

    # 注册网络工具
    tool_manager.register_tool(http_request)
    tool_manager.register_tool(download_file)
    tool_manager.register_tool(check_url)
    tool_manager.register_tool(ping)

    logger.info(f"已成功注册 {len(tool_manager.tools)} 个工具")


# 自动注册所有工具
register_all_tools()
