#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
内容安全与操作限制模块 (Guardrails)

提供对代理操作的安全检查和限制，确保代理的行为符合预期和安全标准。
包括敏感内容检测、操作频率限制、资源使用限制等功能。
"""

import re
import json
import time
import logging
from enum import Enum
from typing import List, Dict, Set, Optional, Any, Union, Tuple, Callable
from dataclasses import dataclass

# 配置日志
logger = logging.getLogger(__name__)


class ContentFlag(Enum):
    """内容标记类型"""
    UNSAFE = "unsafe"  # 不安全内容
    PII = "pii"  # 个人身份信息
    TOXIC = "toxic"  # 有毒/有害内容
    JAILBREAK = "jailbreak"  # 越狱尝试
    POLITICAL = "political"  # 政治内容
    FINANCIAL = "financial"  # 财务/投资建议
    HEALTH = "health"  # 健康/医疗建议
    LEGAL = "legal"  # 法律建议
    HATE = "hate"  # 仇恨言论
    SEXUAL = "sexual"  # 性相关内容
    VIOLENCE = "violence"  # 暴力内容
    SELF_HARM = "self_harm"  # 自我伤害
    PROPRIETARY = "proprietary"  # 专有信息/商业机密


@dataclass
class ContentFlagResult:
    """内容标记结果"""
    flag_type: ContentFlag  # 标记类型
    confidence: float  # 置信度 (0-1)
    text_span: Optional[Tuple[int, int]] = None  # 文本中的起始和结束位置
    metadata: Dict[str, Any] = None  # 额外元数据


@dataclass
class ContentCheckResult:
    """内容检查结果"""
    is_flagged: bool  # 是否被标记
    flags: List[ContentFlagResult]  # 标记列表
    safe_to_use: bool  # 是否安全使用
    filtered_content: Optional[str] = None  # 过滤后的内容
    original_content: Optional[str] = None  # 原始内容
    metadata: Dict[str, Any] = None  # 额外元数据


class RateLimiter:
    """请求频率限制器"""
    
    def __init__(self, max_requests: int, time_window: int):
        """
        初始化频率限制器

        Args:
            max_requests: 时间窗口内允许的最大请求数
            time_window: 时间窗口，单位为秒
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.request_timestamps: Dict[str, List[float]] = {}
    
    def is_allowed(self, key: str) -> bool:
        """
        检查是否允许请求

        Args:
            key: 请求标识，例如用户ID或API密钥

        Returns:
            是否允许请求
        """
        current_time = time.time()
        
        # 获取该标识的请求时间戳列表
        if key not in self.request_timestamps:
            self.request_timestamps[key] = []
        
        timestamps = self.request_timestamps[key]
        
        # 移除时间窗口外的时间戳
        while timestamps and timestamps[0] < current_time - self.time_window:
            timestamps.pop(0)
        
        # 检查是否超过限制
        if len(timestamps) >= self.max_requests:
            return False
        
        # 添加当前时间戳
        timestamps.append(current_time)
        return True
    
    def reset(self, key: str):
        """
        重置特定标识的请求记录

        Args:
            key: 请求标识
        """
        if key in self.request_timestamps:
            self.request_timestamps[key] = []


class ResourceQuota:
    """资源配额管理"""
    
    def __init__(self, quota_limits: Dict[str, int]):
        """
        初始化资源配额管理器

        Args:
            quota_limits: 资源配额限制，格式为 {资源类型: 限制值}
        """
        self.quota_limits = quota_limits
        self.usage: Dict[str, Dict[str, int]] = {}  # {用户ID: {资源类型: 使用量}}
    
    def check_quota(self, user_id: str, resource_type: str, amount: int = 1) -> bool:
        """
        检查用户是否有足够的资源配额

        Args:
            user_id: 用户ID
            resource_type: 资源类型
            amount: 需要使用的资源量

        Returns:
            是否有足够的配额
        """
        # 初始化用户的资源使用记录
        if user_id not in self.usage:
            self.usage[user_id] = {}
        
        # 初始化资源类型的使用量
        if resource_type not in self.usage[user_id]:
            self.usage[user_id][resource_type] = 0
        
        # 获取资源限制
        limit = self.quota_limits.get(resource_type, 0)
        
        # 无限制
        if limit == -1:
            return True
        
        # 检查是否超过限制
        current_usage = self.usage[user_id][resource_type]
        return current_usage + amount <= limit
    
    def use_quota(self, user_id: str, resource_type: str, amount: int = 1) -> bool:
        """
        使用资源配额

        Args:
            user_id: 用户ID
            resource_type: 资源类型
            amount: 使用的资源量

        Returns:
            是否成功使用配额
        """
        if not self.check_quota(user_id, resource_type, amount):
            return False
        
        # 增加使用量
        self.usage[user_id][resource_type] += amount
        return True
    
    def reset_quota(self, user_id: str, resource_type: Optional[str] = None):
        """
        重置用户的资源使用量

        Args:
            user_id: 用户ID
            resource_type: 资源类型，如果为None则重置所有资源类型
        """
        if user_id not in self.usage:
            return
        
        if resource_type is None:
            self.usage[user_id] = {}
        elif resource_type in self.usage[user_id]:
            self.usage[user_id][resource_type] = 0
    
    def get_usage(self, user_id: str, resource_type: Optional[str] = None) -> Union[int, Dict[str, int]]:
        """
        获取用户的资源使用量

        Args:
            user_id: 用户ID
            resource_type: 资源类型，如果为None则返回所有资源类型的使用量

        Returns:
            资源使用量或使用量字典
        """
        if user_id not in self.usage:
            return 0 if resource_type else {}
        
        if resource_type is None:
            return self.usage[user_id]
        
        return self.usage[user_id].get(resource_type, 0)


class GuardrailsService:
    """内容安全与操作限制服务"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化内容安全与操作限制服务

        Args:
            config: 配置信息
        """
        self.config = config or {}
        
        # 默认敏感词列表
        self.sensitive_patterns = self.config.get("sensitive_patterns", [
            r'(password|密码)\s*[:=]\s*\S+',
            r'(api[\s-]?key|apikey|token|secret|access[\s-]?key)\s*[:=]\s*\S+',
            r'\b\d{16,19}\b',  # 信用卡号
            r'\b\d{3}-\d{2}-\d{4}\b',  # 社会安全号 (SSN)
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # 邮箱
        ])
        
        self.sensitive_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.sensitive_patterns]
        
        # 初始化频率限制器
        self.rate_limiters = {
            "default": RateLimiter(
                max_requests=self.config.get("default_rate_limit", 10),
                time_window=self.config.get("default_time_window", 60)
            ),
            "api": RateLimiter(
                max_requests=self.config.get("api_rate_limit", 100),
                time_window=self.config.get("api_time_window", 60)
            ),
            "model": RateLimiter(
                max_requests=self.config.get("model_rate_limit", 20),
                time_window=self.config.get("model_time_window", 60)
            )
        }
        
        # 初始化资源配额管理器
        self.resource_quota = ResourceQuota({
            "model_tokens": self.config.get("model_token_limit", 100000),
            "model_calls": self.config.get("model_call_limit", 1000),
            "api_calls": self.config.get("api_call_limit", 5000),
            "storage_mb": self.config.get("storage_limit_mb", 100)
        })
        
        # 内容检查回调
        self.content_check_callbacks: Dict[str, Callable[[str], ContentCheckResult]] = {}
        
        # 初始化自定义内容检查回调
        if "content_check_callbacks" in self.config:
            self.content_check_callbacks = self.config["content_check_callbacks"]
    
    def check_content(self, content: str, context: Optional[Dict[str, Any]] = None) -> ContentCheckResult:
        """
        检查内容是否安全

        Args:
            content: 要检查的内容
            context: 上下文信息

        Returns:
            内容检查结果
        """
        if not content:
            return ContentCheckResult(is_flagged=False, flags=[], safe_to_use=True)
        
        flags = []
        context = context or {}
        check_type = context.get("check_type", "default")
        
        # 使用自定义回调检查
        if check_type in self.content_check_callbacks:
            return self.content_check_callbacks[check_type](content)
        
        # 默认敏感内容检查
        for i, pattern in enumerate(self.sensitive_regex):
            for match in pattern.finditer(content):
                flags.append(ContentFlagResult(
                    flag_type=ContentFlag.PII,
                    confidence=0.9,
                    text_span=(match.start(), match.end()),
                    metadata={"pattern_index": i, "matched_text": match.group()}
                ))
        
        # 根据应用内容的不同规则调整
        is_flagged = len(flags) > 0
        
        # 是否允许使用 (可以根据 context 定制)
        safe_to_use = not is_flagged or context.get("allow_flagged", False)
        
        # 过滤敏感内容
        filtered_content = content
        if is_flagged and not context.get("keep_original", False):
            filtered_content = self._filter_sensitive_content(content, flags)
        
        return ContentCheckResult(
            is_flagged=is_flagged,
            flags=flags,
            safe_to_use=safe_to_use,
            filtered_content=filtered_content,
            original_content=content,
            metadata={"context": context}
        )
    
    def _filter_sensitive_content(self, content: str, flags: List[ContentFlagResult]) -> str:
        """
        过滤敏感内容

        Args:
            content: 原始内容
            flags: 内容标记列表

        Returns:
            过滤后的内容
        """
        if not flags:
            return content
        
        # 按文本位置降序排序，从后向前替换，避免位置变化
        flags_with_span = [f for f in flags if f.text_span]
        flags_with_span.sort(key=lambda x: x.text_span[0], reverse=True)
        
        result = content
        for flag in flags_with_span:
            start, end = flag.text_span
            # 将敏感内容替换为 [REDACTED]
            result = result[:start] + "[REDACTED]" + result[end:]
        
        return result
    
    def check_rate_limit(self, key: str, limit_type: str = "default") -> bool:
        """
        检查请求是否超过频率限制

        Args:
            key: 请求标识
            limit_type: 限制类型

        Returns:
            是否允许请求
        """
        limiter = self.rate_limiters.get(limit_type)
        if not limiter:
            limiter = self.rate_limiters["default"]
        
        return limiter.is_allowed(key)
    
    def reset_rate_limit(self, key: str, limit_type: Optional[str] = None):
        """
        重置频率限制

        Args:
            key: 请求标识
            limit_type: 限制类型，如果为None则重置所有类型
        """
        if limit_type:
            if limit_type in self.rate_limiters:
                self.rate_limiters[limit_type].reset(key)
        else:
            for limiter in self.rate_limiters.values():
                limiter.reset(key)
    
    def check_resource_quota(self, 
                           user_id: str, 
                           resource_type: str, 
                           amount: int = 1) -> bool:
        """
        检查资源配额

        Args:
            user_id: 用户ID
            resource_type: 资源类型
            amount: 资源量

        Returns:
            是否有足够的配额
        """
        return self.resource_quota.check_quota(user_id, resource_type, amount)
    
    def use_resource_quota(self, 
                          user_id: str, 
                          resource_type: str, 
                          amount: int = 1) -> bool:
        """
        使用资源配额

        Args:
            user_id: 用户ID
            resource_type: 资源类型
            amount: 资源量

        Returns:
            是否成功使用配额
        """
        return self.resource_quota.use_quota(user_id, resource_type, amount)
    
    def get_resource_usage(self, 
                         user_id: str, 
                         resource_type: Optional[str] = None) -> Union[int, Dict[str, int]]:
        """
        获取资源使用量

        Args:
            user_id: 用户ID
            resource_type: 资源类型

        Returns:
            资源使用量
        """
        return self.resource_quota.get_usage(user_id, resource_type)
    
    def reset_resource_quota(self, user_id: str, resource_type: Optional[str] = None):
        """
        重置资源配额

        Args:
            user_id: 用户ID
            resource_type: 资源类型
        """
        self.resource_quota.reset_quota(user_id, resource_type)
    
    def register_content_check_callback(self, check_type: str, callback: Callable[[str], ContentCheckResult]):
        """
        注册内容检查回调函数

        Args:
            check_type: 检查类型
            callback: 回调函数
        """
        self.content_check_callbacks[check_type] = callback
    
    def add_sensitive_pattern(self, pattern: str):
        """
        添加敏感词模式

        Args:
            pattern: 正则表达式模式
        """
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            self.sensitive_patterns.append(pattern)
            self.sensitive_regex.append(regex)
            return True
        except re.error:
            logger.error(f"添加敏感词模式失败: 无效的正则表达式 {pattern}")
            return False 