"""
增强型上下文管理 - 为单/多智能体系统设计

本模块提供一个强大的上下文管理类，用于高效管理会话状态、元数据和历史记录。
设计支持单智能体使用和多智能体协作场景，确保上下文信息可靠传递。
"""

import os
import copy
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Union, Tuple

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class SimpleContext:
    """
    增强型上下文管理类 - 支持单/多智能体协作
    
    特性:
    1. 确保系统消息永不丢失
    2. 智能上下文压缩与管理
    3. 周期性元数据提醒
    4. 支持多智能体协作的上下文序列化/反序列化
    5. 自动识别和处理重要信息
    """
    # 用户基本信息
    user_id: str = "anonymous"
    user_name: str = "用户"
    
    # 消息历史 - 使用OpenAI兼容格式
    messages: List[Dict[str, str]] = field(default_factory=list)
    
    # 元数据 - 结构化存储各类信息
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 内部计数器和状态跟踪
    _turn_count: int = 0
    _reminder_frequency: int = 5  # 每N轮对话提醒一次关键元数据
    _max_messages: Optional[int] = None  # 动态加载自环境变量
    _max_content_length: Optional[int] = None  # 动态加载自环境变量
    
    def __post_init__(self):
        """初始化后处理 - 设置元数据并加载环境配置"""
        # 确保元数据包含用户基本信息
        if "user_id" not in self.metadata:
            self.metadata["user_id"] = self.user_id
        if "user_name" not in self.metadata:
            self.metadata["user_name"] = self.user_name
            
        # 从环境变量加载配置
        self._max_messages = int(os.getenv("CONTEXT_MAX_MESSAGES", "20"))
        self._max_content_length = int(os.getenv("CONTEXT_MAX_CONTENT_LENGTH", "10000"))
        
        # 初始化系统消息跟踪
        self._original_system_messages = []
        self._extract_and_save_system_messages()
    
    def _extract_and_save_system_messages(self):
        """提取并保存原始系统消息，确保它们不会丢失"""
        self._original_system_messages = [
            copy.deepcopy(msg) for msg in self.messages 
            if msg.get("role") == "system"
        ]
    
    # 字典兼容接口实现
    def __getitem__(self, key):
        """支持字典访问语法"""
        if key == "messages":
            return self.messages
        elif key == "user_id":
            return self.user_id
        elif key == "user_name":
            return self.user_name
        elif key == "metadata":
            return self.metadata
        raise KeyError(key)
    
    def __contains__(self, key):
        """支持'in'操作符"""
        return key in ["messages", "user_id", "user_name", "metadata"]
    
    def get(self, key, default=None):
        """兼容字典的get方法"""
        try:
            return self[key]
        except KeyError:
            return default
    
    def keys(self):
        """返回所有键"""
        return ["messages", "user_id", "user_name", "metadata"]
    
    def items(self):
        """返回所有键值对"""
        result = []
        for key in self.keys():
            try:
                result.append((key, self[key]))
            except KeyError:
                pass
        return result
    
    # 核心消息管理功能
    def add_message(self, role: str, content: str) -> None:
        """
        添加消息到历史记录，智能处理上下文长度
        
        Args:
            role: 角色(user/assistant/system)
            content: 消息内容
        """
        # 增加对话轮次计数
        if role in ["user", "assistant"]:
            self._turn_count += 0.5  # 用户+助手=1轮
            
        # 添加新消息
        self.messages.append({
            "role": role,
            "content": content
        })
        
        # 保存新的系统消息
        if role == "system":
            self._original_system_messages.append({
                "role": "system",
                "content": content
            })
        
        # 检查是否需要插入元数据提醒
        self._check_metadata_reminder()
        
        # 智能管理上下文长度
        self._manage_context_length()
    
    def add_system_message(self, content: str) -> None:
        """
        添加系统消息 - 永久保存并确保在首位
        
        Args:
            content: 系统消息内容
        """
        # 保存原始系统消息
        system_message = {"role": "system", "content": content}
        self._original_system_messages.append(copy.deepcopy(system_message))
        
        # 更新当前消息列表
        self._restore_system_messages()
        
        # 添加新的系统消息到首位(如果不存在)
        if not any(msg.get("content") == content for msg in self.messages if msg.get("role") == "system"):
            self.messages.insert(0, system_message)
    
    def _restore_system_messages(self):
        """恢复所有系统消息，确保它们始终存在"""
        # 移除当前的系统消息
        non_system_messages = [msg for msg in self.messages if msg.get("role") != "system"]
        
        # 重新添加所有原始系统消息
        self.messages = copy.deepcopy(self._original_system_messages) + non_system_messages
    
    def _manage_context_length(self):
        """智能管理上下文长度，确保不超过限制同时保留关键信息"""
        # 检查消息数量是否超过限制
        if len(self.messages) <= self._max_messages:
            return
            
        # 提取系统消息和非系统消息
        system_messages = copy.deepcopy(self._original_system_messages)
        non_system_messages = [msg for msg in self.messages if msg.get("role") != "system"]
        
        # 保留最新的非系统消息
        keep_count = self._max_messages - len(system_messages)
        if keep_count < 4:  # 至少保留2轮对话(4条消息)
            keep_count = 4
            # 如果系统消息过多，只保留最重要的几条
            if len(system_messages) > self._max_messages - keep_count:
                logger.warning(f"系统消息过多({len(system_messages)}条)，只保留前{self._max_messages - keep_count}条")
                system_messages = system_messages[:self._max_messages - keep_count]
        
        recent_messages = non_system_messages[-keep_count:]
        
        # 重建消息列表
        self.messages = system_messages + recent_messages
        logger.debug(f"上下文长度管理: 保留{len(system_messages)}条系统消息和{len(recent_messages)}条最新消息")
    
    def _check_metadata_reminder(self):
        """检查是否需要插入元数据提醒"""
        # 每N轮对话提醒一次关键元数据
        if int(self._turn_count) > 0 and int(self._turn_count) % self._reminder_frequency == 0:
            # 只有当上一条消息是助手消息，且当前轮次刚好是整数时才提醒
            if self.messages and self.messages[-1].get("role") == "assistant" and self._turn_count.is_integer():
                self._insert_metadata_reminder()
    
    def _insert_metadata_reminder(self):
        """插入关键元数据提醒"""
        # 构建提醒消息
        reminder = "提醒：当前用户信息 - "
        
        # 添加关键元数据
        important_fields = ["user_name", "role", "permission_level"]
        added = False
        
        for field in important_fields:
            if field in self.metadata and self.metadata[field]:
                reminder += f"{field}: {self.metadata[field]}, "
                added = True
        
        if added:
            reminder = reminder[:-2]  # 移除最后的逗号和空格
            # 作为系统消息插入
            self.add_system_message(reminder)
            logger.debug(f"已插入元数据提醒: {reminder}")
    
    def get_last_n_messages(self, n: int) -> List[Dict[str, str]]:
        """
        获取最近的n条消息，始终包含系统消息
        
        Args:
            n: 需要的非系统消息数量
            
        Returns:
            包含系统消息和最近n条非系统消息的列表
        """
        # 确保系统消息存在
        self._restore_system_messages()
        
        # 分离系统消息和非系统消息
        system_messages = [msg for msg in self.messages if msg.get("role") == "system"]
        non_system_messages = [msg for msg in self.messages if msg.get("role") != "system"]
        
        # 取最近的n条非系统消息
        recent = non_system_messages[-n:] if len(non_system_messages) > n else non_system_messages
        
        # 合并系统消息和最近消息
        return system_messages + recent
    
    # 多智能体协作支持方法
    def serialize(self) -> str:
        """
        序列化上下文，用于传递给其他智能体
        
        Returns:
            序列化后的JSON字符串
        """
        # 确保系统消息存在
        self._restore_system_messages()
        
        # 构建可序列化对象
        serializable = {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "metadata": self.metadata,
            "messages": self.messages,
            "_turn_count": self._turn_count,
            "_reminder_frequency": self._reminder_frequency,
            "_original_system_messages": self._original_system_messages
        }
        
        # 序列化为JSON
        return json.dumps(serializable, ensure_ascii=False)
    
    @classmethod
    def deserialize(cls, serialized_context: str) -> 'SimpleContext':
        """
        从序列化字符串创建上下文对象
        
        Args:
            serialized_context: 序列化的上下文字符串
            
        Returns:
            新的SimpleContext实例
        """
        try:
            data = json.loads(serialized_context)
            
            # 创建基本实例
            context = cls(
                user_id=data.get("user_id", "anonymous"),
                user_name=data.get("user_name", "用户"),
                metadata=data.get("metadata", {}),
                messages=data.get("messages", [])
            )
            
            # 恢复内部状态
            context._turn_count = data.get("_turn_count", 0)
            context._reminder_frequency = data.get("_reminder_frequency", 5)
            context._original_system_messages = data.get("_original_system_messages", [])
            
            # 恢复系统消息
            context._restore_system_messages()
            
            return context
        except Exception as e:
            logger.error(f"反序列化上下文失败: {e}")
            # 返回默认实例
            return cls()
    
    def clone(self) -> 'SimpleContext':
        """
        创建当前上下文的深拷贝
        
        Returns:
            当前上下文的完整副本
        """
        serialized = self.serialize()
        return self.deserialize(serialized)
    
    # 元数据管理增强方法
    def update_metadata(self, new_metadata: Dict[str, Any]) -> None:
        """
        更新元数据，保持关键字段
        
        Args:
            new_metadata: 新的元数据字典
        """
        # 合并元数据，保留原有键
        self.metadata.update(new_metadata)
        
        # 更新用户基本信息
        if "user_id" in new_metadata:
            self.user_id = new_metadata["user_id"]
        if "user_name" in new_metadata:
            self.user_name = new_metadata["user_name"]
            
        # 检查是否需要立即提醒新元数据
        important_fields = ["role", "permission_level", "user_name"]
        if any(field in new_metadata for field in important_fields):
            self._insert_metadata_reminder()
    
    def get_metadata_value(self, key: str, default: Any = None) -> Any:
        """
        安全获取元数据值
        
        Args:
            key: 元数据键
            default: 默认值
            
        Returns:
            元数据值或默认值
        """
        return self.metadata.get(key, default)
    
    def set_reminder_frequency(self, frequency: int) -> None:
        """
        设置元数据提醒频率
        
        Args:
            frequency: 提醒频率(对话轮数)
        """
        if frequency < 1:
            logger.warning(f"提醒频率不能小于1，设置为默认值5")
            self._reminder_frequency = 5
        else:
            self._reminder_frequency = frequency
    
    # 辅助方法
    def get_turn_count(self) -> int:
        """获取当前对话轮数"""
        return int(self._turn_count)
    
    def get_context_summary(self) -> Dict[str, Any]:
        """
        获取上下文摘要信息
        
        Returns:
            包含关键统计信息的字典
        """
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "total_messages": len(self.messages),
            "system_messages": len([m for m in self.messages if m.get("role") == "system"]),
            "user_messages": len([m for m in self.messages if m.get("role") == "user"]),
            "assistant_messages": len([m for m in self.messages if m.get("role") == "assistant"]),
            "turn_count": int(self._turn_count),
            "metadata_keys": list(self.metadata.keys()),
        }
    
    def clear_messages(self, preserve_system: bool = True) -> None:
        """
        清除消息历史
        
        Args:
            preserve_system: 是否保留系统消息
        """
        if preserve_system:
            # 只保留系统消息
            self.messages = copy.deepcopy(self._original_system_messages)
        else:
            # 清空所有消息
            self.messages = []
            self._original_system_messages = []
        
        # 重置对话轮数
        self._turn_count = 0 