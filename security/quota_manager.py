"""
资源配额管理模块 - 实现基于服务计划的资源使用量控制
"""
import time
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from collections import defaultdict
import threading

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class QuotaConfig:
    """配额配置"""
    limit: int  # 限制值
    period: str = "day"  # 周期：day, month, year
    reset_day: Optional[int] = None  # 重置日（月、年配额时有效）

@dataclass
class QuotaUsage:
    """配额使用情况"""
    used: int = 0
    period_start: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)

class QuotaManager:
    """资源配额管理器 - 跟踪和限制用户资源使用"""
    
    def __init__(self, storage_dir: Optional[str] = None, save_interval: int = 300):
        """
        初始化资源配额管理器
        
        Args:
            storage_dir: 存储目录路径，如果为None则使用默认路径
            save_interval: 保存间隔（秒）
        """
        # 线程锁，确保线程安全
        self.lock = Lock()
        
        # 存储配额使用情况
        self.usage: Dict[str, Dict[str, QuotaUsage]] = defaultdict(dict)
        
        # 存储配额配置
        self.configs: Dict[str, QuotaConfig] = {}
        
        # 确定存储目录
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            # 默认存储在项目根目录下的data/security/quota目录
            project_root = Path(__file__).parent.parent.parent.parent
            self.storage_dir = project_root / "data" / "security" / "quota"
        
        # 确保目录存在
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # 存储文件路径
        self.storage_file = self.storage_dir / "quota_data.json"
        
        # 保存间隔
        self.save_interval = save_interval
        
        # 加载数据
        self._load_data()
        
        # 初始化默认配置
        self._initialize_default_configs()
        
        # 启动定期保存和重置任务
        self._start_background_tasks()
        
        logger.info(f"资源配额管理器初始化，已加载 {len(self.configs)} 个配额配置")
    
    def _initialize_default_configs(self):
        """初始化默认配额配置"""
        # 模型Token配额 - 每天
        self.set_quota("model_tokens", 100000, "day")
        
        # API调用配额 - 每天
        self.set_quota("api_calls", 10000, "day")
        
        # 文件存储配额 - 持续有效
        self.set_quota("storage_mb", 1000, "infinite")
        
        # 搜索查询配额 - 每天
        self.set_quota("search_queries", 200, "day")
        
        # 文件处理配额 - 每天
        self.set_quota("file_operations", 100, "day")
    
    def _get_usage_key(self, resource_type: str, user_id: str) -> str:
        """
        生成使用情况键
        
        Args:
            resource_type: 资源类型
            user_id: 用户ID
            
        Returns:
            使用情况键
        """
        return f"{resource_type}:{user_id}"
    
    def _load_data(self):
        """从文件加载数据"""
        if not self.storage_file.exists():
            return
        
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 加载配额配置
                if "configs" in data:
                    for resource_type, config in data["configs"].items():
                        self.configs[resource_type] = QuotaConfig(
                            limit=config["limit"],
                            period=config["period"],
                            reset_day=config.get("reset_day")
                        )
                
                # 加载使用情况数据
                if "usage" in data:
                    for key, usage_data in data["usage"].items():
                        parts = key.split(":")
                        if len(parts) == 2:
                            resource_type, user_id = parts
                            self.usage[resource_type][user_id] = QuotaUsage(
                                used=usage_data["used"],
                                period_start=usage_data["period_start"],
                                last_updated=usage_data["last_updated"]
                            )
                
                logger.info(f"从 {self.storage_file} 加载了 {len(self.configs)} 个配额配置和 {sum(len(v) for v in self.usage.values())} 个使用记录")
        except Exception as e:
            logger.error(f"加载资源配额数据失败: {e}")
    
    def _save_data(self):
        """保存数据到文件"""
        try:
            with self.lock:
                # 准备配置数据
                config_data = {}
                for resource_type, config in self.configs.items():
                    config_data[resource_type] = {
                        "limit": config.limit,
                        "period": config.period,
                        "reset_day": config.reset_day
                    }
                
                # 准备使用情况数据
                usage_data = {}
                for resource_type, users in self.usage.items():
                    for user_id, usage in users.items():
                        key = self._get_usage_key(resource_type, user_id)
                        usage_data[key] = {
                            "used": usage.used,
                            "period_start": usage.period_start,
                            "last_updated": usage.last_updated
                        }
                
                # 组合数据
                data = {
                    "configs": config_data,
                    "usage": usage_data,
                    "updated_at": time.time()
                }
                
                # 保存到文件
                with open(self.storage_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"已保存资源配额数据到 {self.storage_file}")
        except Exception as e:
            logger.error(f"保存资源配额数据失败: {e}")
    
    def _check_reset_needed(self, resource_type: str, user_id: str) -> bool:
        """
        检查是否需要重置配额
        
        Args:
            resource_type: 资源类型
            user_id: 用户ID
            
        Returns:
            是否需要重置
        """
        if resource_type not in self.configs:
            return False
        
        if user_id not in self.usage[resource_type]:
            return False
        
        config = self.configs[resource_type]
        usage = self.usage[resource_type][user_id]
        
        # 当前时间
        now = time.time()
        
        # 永久配额不需要重置
        if config.period == "infinite":
            return False
        
        # 根据周期判断是否需要重置
        if config.period == "day":
            # 获取开始时间和当前时间的日期
            start_date = datetime.fromtimestamp(usage.period_start).date()
            current_date = datetime.fromtimestamp(now).date()
            # 如果日期不同，需要重置
            return start_date != current_date
        
        elif config.period == "month":
            start_date = datetime.fromtimestamp(usage.period_start)
            current_date = datetime.fromtimestamp(now)
            
            # 如果是特定重置日
            if config.reset_day:
                # 当前日期是重置日，且上次重置不是今天
                if current_date.day == config.reset_day and start_date.day != config.reset_day:
                    return True
                # 上月最后一天且重置日大于当月天数
                last_day_of_month = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                if current_date.day == last_day_of_month.day and config.reset_day > last_day_of_month.day:
                    return True
            else:
                # 否则，在月份变化时重置
                return start_date.month != current_date.month or start_date.year != current_date.year
        
        elif config.period == "year":
            start_date = datetime.fromtimestamp(usage.period_start)
            current_date = datetime.fromtimestamp(now)
            
            # 如果是特定重置日
            if config.reset_day:
                # 在指定的日期重置（例如每年1月1日）
                month = 1  # 默认1月
                day = config.reset_day
                if current_date.month == month and current_date.day == day and (start_date.month != month or start_date.day != day):
                    return True
            else:
                # 否则，在年份变化时重置
                return start_date.year != current_date.year
        
        return False
    
    def _reset_usage(self, resource_type: str, user_id: str):
        """
        重置用户特定资源的使用量
        
        Args:
            resource_type: 资源类型
            user_id: 用户ID
        """
        with self.lock:
            if resource_type in self.usage and user_id in self.usage[resource_type]:
                # 对于存储类配额，不重置使用量
                if resource_type == "storage_mb" or (resource_type in self.configs and self.configs[resource_type].period == "infinite"):
                    logger.debug(f"资源 {resource_type} 是持久配额，不重置使用量")
                    return
                
                # 重置使用量
                self.usage[resource_type][user_id].used = 0
                self.usage[resource_type][user_id].period_start = time.time()
                self.usage[resource_type][user_id].last_updated = time.time()
                logger.info(f"已重置用户 {user_id} 的 {resource_type} 使用量")
    
    def _check_and_reset_all(self):
        """检查并重置所有需要重置的配额"""
        with self.lock:
            reset_count = 0
            for resource_type, users in self.usage.items():
                for user_id in list(users.keys()):
                    if self._check_reset_needed(resource_type, user_id):
                        self._reset_usage(resource_type, user_id)
                        reset_count += 1
            
            if reset_count > 0:
                logger.info(f"已自动重置 {reset_count} 个资源配额")
    
    def _start_background_tasks(self):
        """启动后台任务"""
        def run_tasks():
            while True:
                try:
                    self._save_data()
                    self._check_and_reset_all()
                except Exception as e:
                    logger.error(f"执行后台任务时发生错误: {e}")
                
                # 等待下一个间隔
                time.sleep(self.save_interval)
        
        # 创建并启动后台线程
        thread = threading.Thread(target=run_tasks, daemon=True)
        thread.start()
        logger.info(f"已启动配额管理器后台任务，保存间隔: {self.save_interval}秒")
    
    def set_quota(self, resource_type: str, limit: int, period: str = "day", reset_day: Optional[int] = None) -> None:
        """
        设置资源配额
        
        Args:
            resource_type: 资源类型
            limit: 限制值
            period: 周期（day, month, year, infinite）
            reset_day: 重置日（月、年配额时有效）
        """
        with self.lock:
            self.configs[resource_type] = QuotaConfig(limit=limit, period=period, reset_day=reset_day)
            logger.info(f"设置 {resource_type} 的资源配额: {limit}/{period}" + (f", 重置日: {reset_day}" if reset_day else ""))
    
    def get_quota(self, resource_type: str) -> Optional[QuotaConfig]:
        """
        获取资源配额配置
        
        Args:
            resource_type: 资源类型
            
        Returns:
            配额配置，如果不存在则返回None
        """
        return self.configs.get(resource_type)
    
    def get_usage(self, resource_type: str, user_id: str) -> int:
        """
        获取用户的资源使用量
        
        Args:
            resource_type: 资源类型
            user_id: 用户ID
            
        Returns:
            已使用的资源量
        """
        with self.lock:
            # 检查是否需要重置
            if self._check_reset_needed(resource_type, user_id):
                self._reset_usage(resource_type, user_id)
            
            # 返回使用量
            if resource_type in self.usage and user_id in self.usage[resource_type]:
                return self.usage[resource_type][user_id].used
            
            return 0
    
    def increase_usage(self, resource_type: str, user_id: str, amount: int = 1) -> bool:
        """
        增加资源使用量
        
        Args:
            resource_type: 资源类型
            user_id: 用户ID
            amount: 增加的量
            
        Returns:
            是否成功增加
        """
        with self.lock:
            # 检查是否需要重置
            if self._check_reset_needed(resource_type, user_id):
                self._reset_usage(resource_type, user_id)
            
            # 获取使用记录
            if user_id not in self.usage[resource_type]:
                self.usage[resource_type][user_id] = QuotaUsage()
            
            usage = self.usage[resource_type][user_id]
            
            # 增加使用量
            usage.used += amount
            usage.last_updated = time.time()
            
            logger.debug(f"用户 {user_id} 的 {resource_type} 使用量增加 {amount}，当前: {usage.used}")
            return True
    
    def decrease_usage(self, resource_type: str, user_id: str, amount: int = 1) -> bool:
        """
        减少资源使用量
        
        Args:
            resource_type: 资源类型
            user_id: 用户ID
            amount: 减少的量
            
        Returns:
            是否成功减少
        """
        with self.lock:
            # 检查是否需要重置
            if self._check_reset_needed(resource_type, user_id):
                self._reset_usage(resource_type, user_id)
                return True
            
            # 获取使用记录
            if user_id not in self.usage[resource_type]:
                return True
            
            usage = self.usage[resource_type][user_id]
            
            # 减少使用量，不低于0
            usage.used = max(0, usage.used - amount)
            usage.last_updated = time.time()
            
            logger.debug(f"用户 {user_id} 的 {resource_type} 使用量减少 {amount}，当前: {usage.used}")
            return True
    
    def check_quota(self, resource_type: str, user_id: str, additional: int = 0, custom_limit: Optional[int] = None) -> bool:
        """
        检查是否超过配额
        
        Args:
            resource_type: 资源类型
            user_id: 用户ID
            additional: 额外需要的量
            custom_limit: 自定义限制，覆盖默认配置
            
        Returns:
            是否允许使用
        """
        with self.lock:
            # 获取配置
            config = self.configs.get(resource_type)
            if not config:
                logger.warning(f"未找到 {resource_type} 的配额配置，默认允许使用")
                return True
            
            # 使用自定义限制（如果提供）
            limit = custom_limit if custom_limit is not None else config.limit
            
            # 检查是否需要重置
            if self._check_reset_needed(resource_type, user_id):
                self._reset_usage(resource_type, user_id)
            
            # 获取当前使用量
            current_usage = 0
            if resource_type in self.usage and user_id in self.usage[resource_type]:
                current_usage = self.usage[resource_type][user_id].used
            
            # 检查是否超过限制
            if current_usage + additional > limit:
                logger.warning(f"用户 {user_id} 的 {resource_type} 使用量 ({current_usage} + {additional}) 超过配额 {limit}")
                return False
            
            logger.debug(f"用户 {user_id} 的 {resource_type} 使用量 ({current_usage} + {additional}) 未超过配额 {limit}")
            return True
    
    def reset_quota(self, resource_type: Optional[str] = None, user_id: Optional[str] = None) -> bool:
        """
        重置配额使用记录
        
        Args:
            resource_type: 资源类型，如果为None则重置所有类型
            user_id: 用户ID，如果为None则重置所有用户
            
        Returns:
            是否成功重置
        """
        with self.lock:
            if resource_type is None:
                # 重置所有资源类型
                if user_id is None:
                    # 重置所有用户
                    for res_type in self.usage.keys():
                        # 跳过永久配额
                        if res_type in self.configs and self.configs[res_type].period == "infinite":
                            continue
                        self.usage[res_type] = {}
                else:
                    # 重置特定用户的所有资源类型
                    for res_type in self.usage.keys():
                        # 跳过永久配额
                        if res_type in self.configs and self.configs[res_type].period == "infinite":
                            continue
                        if user_id in self.usage[res_type]:
                            self.usage[res_type][user_id].used = 0
                            self.usage[res_type][user_id].period_start = time.time()
                            self.usage[res_type][user_id].last_updated = time.time()
            else:
                # 跳过永久配额
                if resource_type in self.configs and self.configs[resource_type].period == "infinite":
                    logger.info(f"资源 {resource_type} 是持久配额，不重置使用量")
                    return True
                
                # 重置特定资源类型
                if resource_type not in self.usage:
                    return True
                
                if user_id is None:
                    # 重置该资源类型的所有用户
                    self.usage[resource_type] = {}
                else:
                    # 重置特定用户的特定资源类型
                    if user_id in self.usage[resource_type]:
                        self.usage[resource_type][user_id].used = 0
                        self.usage[resource_type][user_id].period_start = time.time()
                        self.usage[resource_type][user_id].last_updated = time.time()
            
            logger.info(f"重置资源配额: resource_type={resource_type or 'all'}, user_id={user_id or 'all'}")
            return True
    
    def get_quota_status(self, resource_type: str, user_id: str, custom_limit: Optional[int] = None) -> Dict[str, Any]:
        """
        获取配额状态
        
        Args:
            resource_type: 资源类型
            user_id: 用户ID
            custom_limit: 自定义限制，覆盖默认配置
            
        Returns:
            配额状态，包括已用量、限制、剩余量、使用百分比等
        """
        with self.lock:
            # 获取配置
            config = self.configs.get(resource_type)
            if not config:
                return {
                    "resource_type": resource_type,
                    "user_id": user_id,
                    "has_quota": False
                }
            
            # 使用自定义限制（如果提供）
            limit = custom_limit if custom_limit is not None else config.limit
            
            # 检查是否需要重置
            if self._check_reset_needed(resource_type, user_id):
                self._reset_usage(resource_type, user_id)
            
            # 获取当前使用量
            current_usage = 0
            period_start = time.time()
            if resource_type in self.usage and user_id in self.usage[resource_type]:
                current_usage = self.usage[resource_type][user_id].used
                period_start = self.usage[resource_type][user_id].period_start
            
            # 计算剩余量
            remaining = max(0, limit - current_usage)
            
            # 计算使用百分比
            percentage = (current_usage / limit * 100) if limit > 0 else 100
            
            # 计算下次重置时间
            next_reset = None
            if config.period == "day":
                # 下一天的同一时间点
                next_day = datetime.fromtimestamp(period_start) + timedelta(days=1)
                next_reset = next_day.timestamp()
            elif config.period == "month":
                # 下个月的重置日
                current_date = datetime.fromtimestamp(period_start)
                if config.reset_day:
                    # 指定了重置日
                    next_month = current_date.replace(day=1) + timedelta(days=32)
                    try:
                        next_reset_date = next_month.replace(day=config.reset_day)
                    except ValueError:
                        # 处理2月份等特殊情况
                        last_day = (next_month.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                        next_reset_date = last_day
                    next_reset = next_reset_date.timestamp()
                else:
                    # 下个月同一天
                    next_month = current_date.replace(day=1) + timedelta(days=32)
                    day = min(current_date.day, (next_month.replace(day=1) + timedelta(days=32)).replace(day=1).day - 1)
                    next_reset_date = next_month.replace(day=day)
                    next_reset = next_reset_date.timestamp()
            elif config.period == "year":
                # 下一年的重置日
                current_date = datetime.fromtimestamp(period_start)
                if config.reset_day:
                    # 指定了重置日（例如，每年1月1日）
                    next_year = current_date.year + 1
                    month = 1  # 默认1月
                    day = min(config.reset_day, 31)  # 不超过31天
                    next_reset = datetime(next_year, month, day).timestamp()
                else:
                    # 下一年同一天
                    next_reset = datetime(current_date.year + 1, current_date.month, current_date.day).timestamp()
            
            return {
                "resource_type": resource_type,
                "user_id": user_id,
                "has_quota": True,
                "limit": limit,
                "used": current_usage,
                "remaining": remaining,
                "percentage": percentage,
                "period": config.period,
                "period_start": period_start,
                "next_reset": next_reset,
                "reset_day": config.reset_day
            }

# 创建全局资源配额管理器实例
quota_manager = QuotaManager() 