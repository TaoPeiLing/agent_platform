"""
速率限制器模块 - 实现基于用户和服务计划的请求频率限制
"""
import time
import logging
import json
import os
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from collections import defaultdict
import threading
import schedule

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """速率限制配置"""
    limit: int  # 单位时间内允许的请求数
    window: int = 60  # 时间窗口（秒）
    cost_function: Optional[callable] = None  # 计算消耗的函数

@dataclass
class RateLimitCounter:
    """速率限制计数器"""
    count: int = 0
    window_start: float = field(default_factory=time.time)
    last_reset: float = field(default_factory=time.time)

class RateLimiter:
    """速率限制器 - 实现令牌桶和滑动窗口限流算法"""
    
    def __init__(self, storage_dir: Optional[str] = None, save_interval: int = 300):
        """
        初始化速率限制器
        
        Args:
            storage_dir: 存储目录路径，如果为None则使用默认路径
            save_interval: 保存间隔（秒）
        """
        # 线程锁，确保线程安全
        self.lock = Lock()
        
        # 存储速率限制计数
        self.counters: Dict[str, Dict[str, RateLimitCounter]] = defaultdict(dict)
        
        # 存储速率限制配置
        self.configs: Dict[str, RateLimitConfig] = {}
        
        # 确定存储目录
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            # 默认存储在项目根目录下的data/security/rate_limit目录
            project_root = Path(__file__).parent.parent.parent.parent
            self.storage_dir = project_root / "data" / "security" / "rate_limit"
        
        # 确保目录存在
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # 存储文件路径
        self.storage_file = self.storage_dir / "rate_limit_data.json"
        
        # 保存间隔
        self.save_interval = save_interval
        
        # 加载数据
        self._load_data()
        
        # 初始化默认配置
        self._initialize_default_configs()
        
        # 启动定期保存和清理任务
        self._start_background_tasks()
        
        logger.info(f"速率限制器初始化，已加载 {len(self.configs)} 个限流配置")
    
    def _initialize_default_configs(self):
        """初始化默认速率限制配置"""
        # 模型调用限制 - 每分钟
        self.set_limit("model", 60, 60)
        
        # API调用限制 - 每分钟
        self.set_limit("api", 120, 60)
        
        # 搜索限制 - 每分钟
        self.set_limit("search", 30, 60)
        
        # 文件操作限制 - 每分钟
        self.set_limit("file", 60, 60)
        
        # 管理操作限制 - 每分钟
        self.set_limit("admin", 20, 60)
    
    def _get_counter_key(self, resource_type: str, user_id: str) -> str:
        """
        生成计数器键
        
        Args:
            resource_type: 资源类型
            user_id: 用户ID
            
        Returns:
            计数器键
        """
        return f"{resource_type}:{user_id}"
    
    def _load_data(self):
        """从文件加载数据"""
        if not self.storage_file.exists():
            return
        
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 加载速率限制配置
                if "configs" in data:
                    for resource_type, config in data["configs"].items():
                        self.configs[resource_type] = RateLimitConfig(
                            limit=config["limit"],
                            window=config["window"]
                        )
                
                # 加载计数器数据
                if "counters" in data:
                    for key, counter_data in data["counters"].items():
                        parts = key.split(":")
                        if len(parts) == 2:
                            resource_type, user_id = parts
                            self.counters[resource_type][user_id] = RateLimitCounter(
                                count=counter_data["count"],
                                window_start=counter_data["window_start"],
                                last_reset=counter_data["last_reset"]
                            )
                
                logger.info(f"从 {self.storage_file} 加载了 {len(self.configs)} 个限流配置和 {sum(len(v) for v in self.counters.values())} 个计数器")
        except Exception as e:
            logger.error(f"加载速率限制数据失败: {e}")
    
    def _save_data(self):
        """保存数据到文件"""
        try:
            with self.lock:
                # 准备配置数据
                config_data = {}
                for resource_type, config in self.configs.items():
                    config_data[resource_type] = {
                        "limit": config.limit,
                        "window": config.window
                    }
                
                # 准备计数器数据
                counter_data = {}
                for resource_type, users in self.counters.items():
                    for user_id, counter in users.items():
                        key = self._get_counter_key(resource_type, user_id)
                        counter_data[key] = {
                            "count": counter.count,
                            "window_start": counter.window_start,
                            "last_reset": counter.last_reset
                        }
                
                # 组合数据
                data = {
                    "configs": config_data,
                    "counters": counter_data,
                    "updated_at": time.time()
                }
                
                # 保存到文件
                with open(self.storage_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"已保存速率限制数据到 {self.storage_file}")
        except Exception as e:
            logger.error(f"保存速率限制数据失败: {e}")
    
    def _clean_expired_counters(self):
        """清理过期的计数器"""
        with self.lock:
            now = time.time()
            cleaned = 0
            
            for resource_type, users in list(self.counters.items()):
                for user_id, counter in list(users.items()):
                    # 获取配置的窗口时间
                    window = self.configs.get(resource_type, RateLimitConfig(60, 60)).window
                    
                    # 如果上次重置时间超过窗口时间的两倍，且计数为0，则删除计数器
                    if now - counter.last_reset > window * 2 and counter.count == 0:
                        del self.counters[resource_type][user_id]
                        cleaned += 1
            
            if cleaned > 0:
                logger.info(f"已清理 {cleaned} 个过期计数器")
    
    def _start_background_tasks(self):
        """启动后台任务"""
        def run_tasks():
            while True:
                try:
                    self._save_data()
                    self._clean_expired_counters()
                except Exception as e:
                    logger.error(f"执行后台任务时发生错误: {e}")
                
                # 等待下一个间隔
                time.sleep(self.save_interval)
        
        # 创建并启动后台线程
        thread = threading.Thread(target=run_tasks, daemon=True)
        thread.start()
        logger.info(f"已启动限流器后台任务，保存间隔: {self.save_interval}秒")
    
    def set_limit(self, resource_type: str, limit: int, window: int = 60) -> None:
        """
        设置速率限制
        
        Args:
            resource_type: 资源类型
            limit: 限制次数
            window: 时间窗口（秒）
        """
        with self.lock:
            self.configs[resource_type] = RateLimitConfig(limit=limit, window=window)
            logger.info(f"设置 {resource_type} 的速率限制: {limit}/{window}秒")
    
    def get_limit(self, resource_type: str) -> Optional[RateLimitConfig]:
        """
        获取速率限制配置
        
        Args:
            resource_type: 资源类型
            
        Returns:
            速率限制配置，如果不存在则返回None
        """
        return self.configs.get(resource_type)
    
    def check_limit(self, resource_type: str, user_id: str, custom_limit: Optional[int] = None) -> bool:
        """
        检查是否超过速率限制
        
        Args:
            resource_type: 资源类型
            user_id: 用户ID
            custom_limit: 自定义限制，如果提供则覆盖默认配置
            
        Returns:
            是否允许请求
        """
        with self.lock:
            # 获取配置
            config = self.configs.get(resource_type)
            if not config:
                logger.warning(f"未找到 {resource_type} 的速率限制配置，默认允许请求")
                return True
            
            # 使用自定义限制（如果提供）
            limit = custom_limit if custom_limit is not None else config.limit
            
            # 获取计数器
            if user_id not in self.counters[resource_type]:
                self.counters[resource_type][user_id] = RateLimitCounter()
            
            counter = self.counters[resource_type][user_id]
            
            # 当前时间
            now = time.time()
            
            # 如果超过窗口时间，重置计数器
            if now - counter.window_start >= config.window:
                counter.count = 0
                counter.window_start = now
                counter.last_reset = now
            
            # 检查是否超过限制
            if counter.count >= limit:
                logger.warning(f"用户 {user_id} 对 {resource_type} 的请求超过速率限制 {limit}/{config.window}秒")
                return False
            
            # 请求未超限，计数加1
            counter.count += 1
            logger.debug(f"用户 {user_id} 对 {resource_type} 的请求计数: {counter.count}/{limit}")
            return True
    
    def increment(self, resource_type: str, user_id: str, cost: int = 1) -> bool:
        """
        增加计数（不检查限制）
        
        Args:
            resource_type: 资源类型
            user_id: 用户ID
            cost: 消耗量
            
        Returns:
            是否成功增加计数
        """
        with self.lock:
            # 获取配置
            config = self.configs.get(resource_type)
            if not config:
                logger.warning(f"未找到 {resource_type} 的速率限制配置，无法增加计数")
                return False
            
            # 获取计数器
            if user_id not in self.counters[resource_type]:
                self.counters[resource_type][user_id] = RateLimitCounter()
            
            counter = self.counters[resource_type][user_id]
            
            # 当前时间
            now = time.time()
            
            # 如果超过窗口时间，重置计数器
            if now - counter.window_start >= config.window:
                counter.count = 0
                counter.window_start = now
                counter.last_reset = now
            
            # 增加计数
            counter.count += cost
            logger.debug(f"用户 {user_id} 对 {resource_type} 的请求计数增加 {cost}，当前: {counter.count}")
            return True
    
    def get_remaining(self, resource_type: str, user_id: str, custom_limit: Optional[int] = None) -> Tuple[int, int]:
        """
        获取剩余请求次数和重置时间
        
        Args:
            resource_type: 资源类型
            user_id: 用户ID
            custom_limit: 自定义限制，如果提供则覆盖默认配置
            
        Returns:
            元组(剩余次数, 距离重置的秒数)
        """
        with self.lock:
            # 获取配置
            config = self.configs.get(resource_type)
            if not config:
                logger.warning(f"未找到 {resource_type} 的速率限制配置")
                return (0, 0)
            
            # 使用自定义限制（如果提供）
            limit = custom_limit if custom_limit is not None else config.limit
            
            # 如果用户没有计数器记录，表示尚未使用
            if user_id not in self.counters[resource_type]:
                return (limit, 0)
            
            counter = self.counters[resource_type][user_id]
            
            # 当前时间
            now = time.time()
            
            # 如果超过窗口时间，剩余次数为限制值
            if now - counter.window_start >= config.window:
                return (limit, 0)
            
            # 计算剩余次数和重置时间
            remaining = max(0, limit - counter.count)
            reset_in = int(config.window - (now - counter.window_start))
            
            return (remaining, reset_in)
    
    def reset(self, resource_type: Optional[str] = None, user_id: Optional[str] = None) -> bool:
        """
        重置计数器
        
        Args:
            resource_type: 资源类型，如果为None则重置所有类型
            user_id: 用户ID，如果为None则重置所有用户
            
        Returns:
            是否成功重置
        """
        with self.lock:
            now = time.time()
            
            if resource_type is None:
                # 重置所有资源类型
                if user_id is None:
                    # 重置所有用户
                    self.counters = defaultdict(dict)
                else:
                    # 重置特定用户的所有资源类型
                    for resource_counters in self.counters.values():
                        if user_id in resource_counters:
                            del resource_counters[user_id]
            else:
                # 重置特定资源类型
                if resource_type not in self.counters:
                    return True
                
                if user_id is None:
                    # 重置该资源类型的所有用户
                    self.counters[resource_type] = {}
                else:
                    # 重置特定用户的特定资源类型
                    if user_id in self.counters[resource_type]:
                        del self.counters[resource_type][user_id]
            
            logger.info(f"重置速率限制计数器: resource_type={resource_type or 'all'}, user_id={user_id or 'all'}")
            return True

# 创建全局速率限制器实例
rate_limiter = RateLimiter() 