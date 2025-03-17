"""
文件工具模块 - 提供文件操作功能

包含一个文件管理器类，用于操作文件系统。
"""
import os
import logging
import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

# 工作目录设置
DEFAULT_WORK_DIR = os.path.join(Path(__file__).parent.parent.parent, "workspace")


class FileManager:
    """
    文件管理器 - 提供文件操作功能
    
    该类提供了安全的文件读写功能，限制在指定工作目录内操作。
    """
    
    def __init__(self, work_dir: str = DEFAULT_WORK_DIR):
        """
        初始化文件管理器
        
        Args:
            work_dir: 工作目录路径
        """
        self.work_dir = work_dir
        
        # 确保工作目录存在
        os.makedirs(self.work_dir, exist_ok=True)
        
        # 创建测试数据
        self._create_test_files()
        
        logger.info(f"文件管理器初始化，工作目录: {self.work_dir}")
    
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """
        读取文件内容
        
        Args:
            file_path: 文件路径，相对于工作目录
            
        Returns:
            包含文件内容的字典
        """
        logger.info(f"读取文件: {file_path}")
        
        try:
            # 处理路径
            abs_path = self._get_abs_path(file_path)
            
            # 安全检查
            if not self._is_safe_path(abs_path):
                return {
                    "error": True,
                    "message": f"安全限制：不允许访问工作目录外的文件",
                    "file_path": file_path
                }
            
            # 检查文件是否存在
            if not os.path.exists(abs_path):
                return {
                    "error": True,
                    "message": f"文件不存在: {file_path}",
                    "file_path": file_path
                }
                
            # 检查是否是文件
            if not os.path.isfile(abs_path):
                return {
                    "error": True,
                    "message": f"路径不是文件: {file_path}",
                    "file_path": file_path
                }
            
            # 读取文件内容
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 获取文件信息
            file_info = self._get_file_info(abs_path)
            
            return {
                "error": False,
                "content": content,
                "file_path": file_path,
                "file_info": file_info
            }
            
        except Exception as e:
            logger.error(f"读取文件失败: {str(e)}")
            return {
                "error": True,
                "message": f"读取文件失败: {str(e)}",
                "file_path": file_path
            }
    
    def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        写入文件内容
        
        Args:
            file_path: 文件路径，相对于工作目录
            content: 要写入的内容
            
        Returns:
            写入结果
        """
        logger.info(f"写入文件: {file_path}")
        
        try:
            # 处理路径
            abs_path = self._get_abs_path(file_path)
            
            # 安全检查
            if not self._is_safe_path(abs_path):
                return {
                    "error": True,
                    "message": f"安全限制：不允许访问工作目录外的文件",
                    "file_path": file_path
                }
            
            # 确保目录存在
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            
            # 写入文件
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 获取文件信息
            file_info = self._get_file_info(abs_path)
            
            return {
                "error": False,
                "message": "文件写入成功",
                "file_path": file_path,
                "file_info": file_info
            }
            
        except Exception as e:
            logger.error(f"写入文件失败: {str(e)}")
            return {
                "error": True,
                "message": f"写入文件失败: {str(e)}",
                "file_path": file_path
            }
    
    def list_files(self, directory: str = "") -> Dict[str, Any]:
        """
        列出目录中的文件
        
        Args:
            directory: 目录路径，相对于工作目录，默认为根目录
            
        Returns:
            目录内容列表
        """
        logger.info(f"列出目录: {directory}")
        
        try:
            # 处理路径
            abs_path = self._get_abs_path(directory)
            
            # 安全检查
            if not self._is_safe_path(abs_path):
                return {
                    "error": True,
                    "message": f"安全限制：不允许访问工作目录外的目录",
                    "directory": directory
                }
            
            # 检查目录是否存在
            if not os.path.exists(abs_path):
                return {
                    "error": True,
                    "message": f"目录不存在: {directory}",
                    "directory": directory
                }
                
            # 检查是否是目录
            if not os.path.isdir(abs_path):
                return {
                    "error": True,
                    "message": f"路径不是目录: {directory}",
                    "directory": directory
                }
            
            # 获取目录内容
            items = []
            for item in os.listdir(abs_path):
                item_path = os.path.join(abs_path, item)
                item_type = "file" if os.path.isfile(item_path) else "directory"
                item_info = self._get_file_info(item_path) if item_type == "file" else {
                    "size": 0,
                    "created": os.path.getctime(item_path),
                    "modified": os.path.getmtime(item_path)
                }
                
                items.append({
                    "name": item,
                    "type": item_type,
                    "info": item_info
                })
            
            return {
                "error": False,
                "directory": directory,
                "items": items,
                "count": len(items)
            }
            
        except Exception as e:
            logger.error(f"列出目录失败: {str(e)}")
            return {
                "error": True,
                "message": f"列出目录失败: {str(e)}",
                "directory": directory
            }
    
    def _get_abs_path(self, rel_path: str) -> str:
        """
        获取绝对路径
        
        Args:
            rel_path: 相对路径
            
        Returns:
            绝对路径
        """
        # 如果是绝对路径，需要确保它在工作目录下
        if os.path.isabs(rel_path):
            if rel_path.startswith(self.work_dir):
                return rel_path
            else:
                # 尝试转换为相对路径再处理
                try:
                    rel_path = os.path.relpath(rel_path, start=self.work_dir)
                except:
                    # 如果无法转换，使用basename
                    rel_path = os.path.basename(rel_path)
        
        # 确保路径规范化
        rel_path = os.path.normpath(rel_path)
        
        # 删除开头的斜杠或点号
        rel_path = rel_path.lstrip('/\\.')
        
        # 返回绝对路径
        return os.path.join(self.work_dir, rel_path)
    
    def _is_safe_path(self, path: str) -> bool:
        """
        检查路径是否安全（在工作目录内）
        
        Args:
            path: 路径
            
        Returns:
            是否安全
        """
        # 规范化路径
        norm_path = os.path.normpath(path)
        norm_work_dir = os.path.normpath(self.work_dir)
        
        # 检查路径是否在工作目录内
        return norm_path.startswith(norm_work_dir)
    
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息字典
        """
        stats = os.stat(file_path)
        
        return {
            "size": stats.st_size,
            "created": stats.st_ctime,
            "modified": stats.st_mtime,
            "extension": os.path.splitext(file_path)[1].lstrip('.') if os.path.splitext(file_path)[1] else "",
            "is_executable": os.access(file_path, os.X_OK)
        }
    
    def _create_test_files(self):
        """创建测试文件和目录"""
        # 创建示例文件目录
        examples_dir = os.path.join(self.work_dir, "examples")
        os.makedirs(examples_dir, exist_ok=True)
        
        # 创建示例文本文件
        hello_file = os.path.join(examples_dir, "hello.txt")
        if not os.path.exists(hello_file):
            with open(hello_file, 'w', encoding='utf-8') as f:
                f.write("Hello, World!\n这是一个示例文本文件。\n")
        
        # 创建示例JSON文件
        data_file = os.path.join(examples_dir, "data.json")
        if not os.path.exists(data_file):
            sample_data = {
                "name": "示例数据",
                "items": [
                    {"id": 1, "value": "第一项"},
                    {"id": 2, "value": "第二项"},
                    {"id": 3, "value": "第三项"}
                ],
                "created_at": time.time()
            }
            
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(sample_data, f, ensure_ascii=False, indent=2)
        
        # 创建示例配置目录
        config_dir = os.path.join(self.work_dir, "config")
        os.makedirs(config_dir, exist_ok=True)
        
        # 创建示例配置文件
        config_file = os.path.join(config_dir, "settings.conf")
        if not os.path.exists(config_file):
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write("[general]\n")
                f.write("debug = true\n")
                f.write("language = zh-CN\n\n")
                f.write("[api]\n")
                f.write("endpoint = https://api.example.com\n")
                f.write("timeout = 30\n")
        
        logger.info("测试文件创建完成") 