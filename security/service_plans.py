"""
服务计划管理模块 - 定义和管理不同级别的服务计划
"""
import time
import logging
import json
import os
from typing import Dict, List, Optional, Set, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class ResourceLimits:
    """资源限制配置"""
    max_requests_per_day: int = 100  # 每日最大请求数
    max_tokens_per_request: int = 4000  # 每次请求最大Token数
    max_tokens_per_day: int = 100000  # 每日最大Token数
    max_files_storage: int = 10  # 最大存储文件数
    max_file_size_mb: float = 5.0  # 最大文件大小（MB）
    max_concurrent_requests: int = 2  # 最大并发请求数
    priority_queue: bool = False  # 是否使用优先队列

@dataclass
class FeatureAccess:
    """功能访问配置"""
    allowed_models: List[str] = field(default_factory=list)  # 允许使用的模型
    allowed_tools: List[str] = field(default_factory=list)  # 允许使用的工具
    fine_tuning_allowed: bool = False  # 是否允许微调
    custom_prompts_allowed: bool = False  # 是否允许自定义提示词
    team_collaboration: bool = False  # 是否允许团队协作
    api_access: bool = False  # 是否允许API访问
    webhook_support: bool = False  # 是否支持Webhook
    advanced_analytics: bool = False  # 是否支持高级分析

@dataclass
class ServicePlan:
    """服务计划定义"""
    plan_id: str  # 计划ID
    name: str  # 计划名称
    description: str = ""  # 计划描述
    is_active: bool = True  # 是否激活
    is_public: bool = True  # 是否公开可用
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)  # 资源限制
    feature_access: FeatureAccess = field(default_factory=FeatureAccess)  # 功能访问
    base_permissions: List[str] = field(default_factory=list)  # 基础权限
    price_monthly: float = 0.0  # 月度价格
    price_yearly: float = 0.0  # 年度价格
    trial_days: int = 0  # 试用天数
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

@dataclass
class UserPlanSubscription:
    """用户计划订阅"""
    subscription_id: str  # 订阅ID
    user_id: str  # 用户ID
    plan_id: str  # 计划ID
    is_active: bool = True  # 是否激活
    is_trial: bool = False  # 是否试用
    start_date: float = field(default_factory=time.time)  # 开始日期
    end_date: Optional[float] = None  # 结束日期(None表示永不过期)
    payment_id: Optional[str] = None  # 支付ID
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

class ServicePlanManager:
    """服务计划管理器"""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        初始化服务计划管理器
        
        Args:
            storage_dir: 存储目录路径，如果为None则使用默认路径
        """
        # 线程锁，确保线程安全
        self.lock = Lock()
        
        # 存储计划定义
        self.plans: Dict[str, ServicePlan] = {}
        
        # 存储用户订阅
        self.subscriptions: Dict[str, UserPlanSubscription] = {}
        
        # 确定存储目录
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            # 默认存储在项目根目录下的data/security/plans目录
            project_root = Path(__file__).parent.parent.parent.parent
            self.storage_dir = project_root / "data" / "security" / "plans"
        
        # 确保目录存在
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # 存储文件路径
        self.plans_file = self.storage_dir / "service_plans.json"
        self.subscriptions_file = self.storage_dir / "user_subscriptions.json"
        
        # 加载数据
        self._load_data()
        
        # 如果没有计划，初始化默认计划
        if not self.plans:
            self._initialize_default_plans()
        
        logger.info(f"服务计划管理器初始化，已加载 {len(self.plans)} 个计划和 {len(self.subscriptions)} 个订阅")
    
    def _initialize_default_plans(self):
        """初始化默认服务计划"""
        default_plans = [
            # 免费计划
            ServicePlan(
                plan_id="free",
                name="免费版",
                description="适用于个人用户的基础功能",
                resource_limits=ResourceLimits(
                    max_requests_per_day=20,
                    max_tokens_per_request=2000,
                    max_tokens_per_day=10000,
                    max_files_storage=3,
                    max_file_size_mb=2.0,
                    max_concurrent_requests=1
                ),
                feature_access=FeatureAccess(
                    allowed_models=["gpt-3.5-turbo"],
                    allowed_tools=["text-generation", "summarization"],
                    custom_prompts_allowed=True
                ),
                base_permissions=[
                    "agent.execute.basic",
                    "agent.read",
                    "content.read",
                    "content.write.basic"
                ],
                price_monthly=0.0,
                price_yearly=0.0,
                trial_days=0
            ),
            
            # 基础计划
            ServicePlan(
                plan_id="basic",
                name="基础版",
                description="适用于初级用户的增强功能",
                resource_limits=ResourceLimits(
                    max_requests_per_day=100,
                    max_tokens_per_request=4000,
                    max_tokens_per_day=50000,
                    max_files_storage=10,
                    max_file_size_mb=5.0,
                    max_concurrent_requests=2
                ),
                feature_access=FeatureAccess(
                    allowed_models=["gpt-3.5-turbo", "gpt-4"],
                    allowed_tools=[
                        "text-generation", 
                        "summarization", 
                        "question-answering",
                        "image-generation"
                    ],
                    custom_prompts_allowed=True,
                    api_access=True
                ),
                base_permissions=[
                    "agent.execute.basic",
                    "agent.execute.advanced",
                    "agent.read",
                    "agent.create.basic",
                    "content.read",
                    "content.write.basic",
                    "content.write.advanced",
                    "api.access.basic"
                ],
                price_monthly=9.99,
                price_yearly=99.99,
                trial_days=7
            ),
            
            # 专业计划
            ServicePlan(
                plan_id="pro",
                name="专业版",
                description="适用于专业用户的完整功能",
                resource_limits=ResourceLimits(
                    max_requests_per_day=500,
                    max_tokens_per_request=8000,
                    max_tokens_per_day=200000,
                    max_files_storage=50,
                    max_file_size_mb=20.0,
                    max_concurrent_requests=5,
                    priority_queue=True
                ),
                feature_access=FeatureAccess(
                    allowed_models=["gpt-3.5-turbo", "gpt-4", "gpt-4-32k", "claude-3"],
                    allowed_tools=[
                        "text-generation", 
                        "summarization", 
                        "question-answering",
                        "image-generation",
                        "code-generation",
                        "data-analysis",
                        "file-processing"
                    ],
                    custom_prompts_allowed=True,
                    fine_tuning_allowed=True,
                    team_collaboration=True,
                    api_access=True,
                    webhook_support=True,
                    advanced_analytics=True
                ),
                base_permissions=[
                    "agent.execute.*",
                    "agent.read",
                    "agent.create.*",
                    "agent.edit.*",
                    "content.read",
                    "content.write.*",
                    "content.publish",
                    "api.access.*",
                    "team.*"
                ],
                price_monthly=29.99,
                price_yearly=299.99,
                trial_days=14
            ),
            
            # 企业计划
            ServicePlan(
                plan_id="enterprise",
                name="企业版",
                description="适用于企业用户的定制功能",
                resource_limits=ResourceLimits(
                    max_requests_per_day=2000,
                    max_tokens_per_request=16000,
                    max_tokens_per_day=1000000,
                    max_files_storage=500,
                    max_file_size_mb=100.0,
                    max_concurrent_requests=20,
                    priority_queue=True
                ),
                feature_access=FeatureAccess(
                    allowed_models=[
                        "gpt-3.5-turbo", 
                        "gpt-4", 
                        "gpt-4-32k", 
                        "claude-3", 
                        "custom-models"
                    ],
                    allowed_tools=["*"],  # 允许所有工具
                    custom_prompts_allowed=True,
                    fine_tuning_allowed=True,
                    team_collaboration=True,
                    api_access=True,
                    webhook_support=True,
                    advanced_analytics=True
                ),
                base_permissions=["*"],  # 允许所有权限
                price_monthly=99.99,
                price_yearly=999.99,
                trial_days=30,
                is_public=False  # 企业版需要联系销售
            )
        ]
        
        # 添加默认计划
        for plan in default_plans:
            self.plans[plan.plan_id] = plan
        
        # 保存到文件
        self._save_plans()
    
    def _load_data(self):
        """从文件加载数据"""
        # 加载计划定义
        if self.plans_file.exists():
            try:
                with open(self.plans_file, 'r', encoding='utf-8') as f:
                    plans_data = json.load(f)
                    for plan_data in plans_data:
                        resource_limits = ResourceLimits(**plan_data.get("resource_limits", {}))
                        feature_access = FeatureAccess(**plan_data.get("feature_access", {}))
                        
                        plan = ServicePlan(
                            plan_id=plan_data["plan_id"],
                            name=plan_data["name"],
                            description=plan_data.get("description", ""),
                            is_active=plan_data.get("is_active", True),
                            is_public=plan_data.get("is_public", True),
                            resource_limits=resource_limits,
                            feature_access=feature_access,
                            base_permissions=plan_data.get("base_permissions", []),
                            price_monthly=plan_data.get("price_monthly", 0.0),
                            price_yearly=plan_data.get("price_yearly", 0.0),
                            trial_days=plan_data.get("trial_days", 0),
                            created_at=plan_data.get("created_at", time.time()),
                            updated_at=plan_data.get("updated_at", time.time())
                        )
                        self.plans[plan.plan_id] = plan
                logger.info(f"从 {self.plans_file} 加载了 {len(self.plans)} 个服务计划")
            except Exception as e:
                logger.error(f"加载服务计划失败: {e}")
        
        # 加载用户订阅
        if self.subscriptions_file.exists():
            try:
                with open(self.subscriptions_file, 'r', encoding='utf-8') as f:
                    subscriptions_data = json.load(f)
                    for sub_data in subscriptions_data:
                        sub = UserPlanSubscription(
                            subscription_id=sub_data["subscription_id"],
                            user_id=sub_data["user_id"],
                            plan_id=sub_data["plan_id"],
                            is_active=sub_data.get("is_active", True),
                            is_trial=sub_data.get("is_trial", False),
                            start_date=sub_data.get("start_date", time.time()),
                            end_date=sub_data.get("end_date"),
                            payment_id=sub_data.get("payment_id"),
                            created_at=sub_data.get("created_at", time.time()),
                            updated_at=sub_data.get("updated_at", time.time())
                        )
                        self.subscriptions[sub.subscription_id] = sub
                logger.info(f"从 {self.subscriptions_file} 加载了 {len(self.subscriptions)} 个用户订阅")
            except Exception as e:
                logger.error(f"加载用户订阅失败: {e}")
    
    def _save_plans(self):
        """保存服务计划到文件"""
        try:
            with self.lock:
                plans_data = []
                for plan in self.plans.values():
                    plans_data.append({
                        "plan_id": plan.plan_id,
                        "name": plan.name,
                        "description": plan.description,
                        "is_active": plan.is_active,
                        "is_public": plan.is_public,
                        "resource_limits": {
                            "max_requests_per_day": plan.resource_limits.max_requests_per_day,
                            "max_tokens_per_request": plan.resource_limits.max_tokens_per_request,
                            "max_tokens_per_day": plan.resource_limits.max_tokens_per_day,
                            "max_files_storage": plan.resource_limits.max_files_storage,
                            "max_file_size_mb": plan.resource_limits.max_file_size_mb,
                            "max_concurrent_requests": plan.resource_limits.max_concurrent_requests,
                            "priority_queue": plan.resource_limits.priority_queue
                        },
                        "feature_access": {
                            "allowed_models": plan.feature_access.allowed_models,
                            "allowed_tools": plan.feature_access.allowed_tools,
                            "fine_tuning_allowed": plan.feature_access.fine_tuning_allowed,
                            "custom_prompts_allowed": plan.feature_access.custom_prompts_allowed,
                            "team_collaboration": plan.feature_access.team_collaboration,
                            "api_access": plan.feature_access.api_access,
                            "webhook_support": plan.feature_access.webhook_support,
                            "advanced_analytics": plan.feature_access.advanced_analytics
                        },
                        "base_permissions": plan.base_permissions,
                        "price_monthly": plan.price_monthly,
                        "price_yearly": plan.price_yearly,
                        "trial_days": plan.trial_days,
                        "created_at": plan.created_at,
                        "updated_at": plan.updated_at
                    })
                
                with open(self.plans_file, 'w', encoding='utf-8') as f:
                    json.dump(plans_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"已保存 {len(self.plans)} 个服务计划到 {self.plans_file}")
        except Exception as e:
            logger.error(f"保存服务计划失败: {e}")
    
    def _save_subscriptions(self):
        """保存用户订阅到文件"""
        try:
            with self.lock:
                subscriptions_data = []
                for sub in self.subscriptions.values():
                    subscriptions_data.append({
                        "subscription_id": sub.subscription_id,
                        "user_id": sub.user_id,
                        "plan_id": sub.plan_id,
                        "is_active": sub.is_active,
                        "is_trial": sub.is_trial,
                        "start_date": sub.start_date,
                        "end_date": sub.end_date,
                        "payment_id": sub.payment_id,
                        "created_at": sub.created_at,
                        "updated_at": sub.updated_at
                    })
                
                with open(self.subscriptions_file, 'w', encoding='utf-8') as f:
                    json.dump(subscriptions_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"已保存 {len(self.subscriptions)} 个用户订阅到 {self.subscriptions_file}")
        except Exception as e:
            logger.error(f"保存用户订阅失败: {e}")
    
    def create_plan(self, 
                  plan_id: str,
                  name: str,
                  description: str = "",
                  is_active: bool = True,
                  is_public: bool = True,
                  resource_limits: Optional[ResourceLimits] = None,
                  feature_access: Optional[FeatureAccess] = None,
                  base_permissions: Optional[List[str]] = None,
                  price_monthly: float = 0.0,
                  price_yearly: float = 0.0,
                  trial_days: int = 0) -> bool:
        """
        创建服务计划
        
        Args:
            plan_id: 计划ID
            name: 计划名称
            description: 计划描述
            is_active: 是否激活
            is_public: 是否公开可用
            resource_limits: 资源限制
            feature_access: 功能访问
            base_permissions: 基础权限
            price_monthly: 月度价格
            price_yearly: 年度价格
            trial_days: 试用天数
            
        Returns:
            是否成功创建
        """
        with self.lock:
            # 检查ID是否已存在
            if plan_id in self.plans:
                logger.warning(f"计划ID已存在: {plan_id}")
                return False
            
            # 创建计划
            plan = ServicePlan(
                plan_id=plan_id,
                name=name,
                description=description,
                is_active=is_active,
                is_public=is_public,
                resource_limits=resource_limits or ResourceLimits(),
                feature_access=feature_access or FeatureAccess(),
                base_permissions=base_permissions or [],
                price_monthly=price_monthly,
                price_yearly=price_yearly,
                trial_days=trial_days
            )
            
            self.plans[plan_id] = plan
            
            # 保存到文件
            self._save_plans()
            
            logger.info(f"创建服务计划: {plan_id}")
            return True
    
    def update_plan(self,
                   plan_id: str,
                   name: Optional[str] = None,
                   description: Optional[str] = None,
                   is_active: Optional[bool] = None,
                   is_public: Optional[bool] = None,
                   resource_limits: Optional[ResourceLimits] = None,
                   feature_access: Optional[FeatureAccess] = None,
                   base_permissions: Optional[List[str]] = None,
                   price_monthly: Optional[float] = None,
                   price_yearly: Optional[float] = None,
                   trial_days: Optional[int] = None) -> bool:
        """
        更新服务计划
        
        Args:
            plan_id: 计划ID
            name: 计划名称
            description: 计划描述
            is_active: 是否激活
            is_public: 是否公开可用
            resource_limits: 资源限制
            feature_access: 功能访问
            base_permissions: 基础权限
            price_monthly: 月度价格
            price_yearly: 年度价格
            trial_days: 试用天数
            
        Returns:
            是否成功更新
        """
        with self.lock:
            # 检查计划是否存在
            if plan_id not in self.plans:
                logger.warning(f"计划不存在: {plan_id}")
                return False
            
            plan = self.plans[plan_id]
            
            # 更新属性
            if name is not None:
                plan.name = name
            
            if description is not None:
                plan.description = description
            
            if is_active is not None:
                plan.is_active = is_active
            
            if is_public is not None:
                plan.is_public = is_public
            
            if resource_limits is not None:
                plan.resource_limits = resource_limits
            
            if feature_access is not None:
                plan.feature_access = feature_access
            
            if base_permissions is not None:
                plan.base_permissions = base_permissions
            
            if price_monthly is not None:
                plan.price_monthly = price_monthly
            
            if price_yearly is not None:
                plan.price_yearly = price_yearly
            
            if trial_days is not None:
                plan.trial_days = trial_days
            
            plan.updated_at = time.time()
            
            # 保存到文件
            self._save_plans()
            
            logger.info(f"更新服务计划: {plan_id}")
            return True
    
    def delete_plan(self, plan_id: str) -> bool:
        """
        删除服务计划
        
        Args:
            plan_id: 计划ID
            
        Returns:
            是否成功删除
        """
        with self.lock:
            # 检查计划是否存在
            if plan_id not in self.plans:
                logger.warning(f"计划不存在: {plan_id}")
                return False
            
            # 检查是否有用户使用该计划
            for sub in self.subscriptions.values():
                if sub.plan_id == plan_id and sub.is_active:
                    logger.warning(f"无法删除计划 {plan_id}，仍有活跃用户订阅")
                    return False
            
            # 删除计划
            del self.plans[plan_id]
            
            # 保存到文件
            self._save_plans()
            
            logger.info(f"删除服务计划: {plan_id}")
            return True
    
    def get_plan(self, plan_id: str) -> Optional[ServicePlan]:
        """
        获取服务计划
        
        Args:
            plan_id: 计划ID
            
        Returns:
            服务计划，如果不存在则返回None
        """
        return self.plans.get(plan_id)
    
    def list_plans(self, active_only: bool = True, public_only: bool = False) -> List[ServicePlan]:
        """
        列出服务计划
        
        Args:
            active_only: 是否只返回激活的计划
            public_only: 是否只返回公开的计划
            
        Returns:
            服务计划列表
        """
        result = []
        
        for plan in self.plans.values():
            if active_only and not plan.is_active:
                continue
            
            if public_only and not plan.is_public:
                continue
            
            result.append(plan)
        
        return result
    
    def subscribe_user(self,
                      user_id: str,
                      plan_id: str,
                      is_trial: bool = False,
                      subscription_months: Optional[int] = None,
                      payment_id: Optional[str] = None) -> Optional[str]:
        """
        为用户订阅服务计划
        
        Args:
            user_id: 用户ID
            plan_id: 计划ID
            is_trial: 是否为试用
            subscription_months: 订阅月数（如果为None则永不过期）
            payment_id: 支付ID
            
        Returns:
            订阅ID，如果订阅失败则返回None
        """
        with self.lock:
            # 检查计划是否存在
            if plan_id not in self.plans:
                logger.warning(f"计划不存在: {plan_id}")
                return None
            
            plan = self.plans[plan_id]
            
            # 检查计划是否激活
            if not plan.is_active:
                logger.warning(f"计划未激活: {plan_id}")
                return None
            
            # 检查用户当前是否有活跃订阅
            current_subscription = self.get_user_subscription(user_id)
            if current_subscription:
                # 取消当前订阅
                self.cancel_subscription(current_subscription.subscription_id)
            
            # 生成订阅ID
            import uuid
            subscription_id = f"sub_{uuid.uuid4().hex[:8]}"
            
            # 计算结束日期
            end_date = None
            
            if is_trial:
                if plan.trial_days > 0:
                    end_date = time.time() + plan.trial_days * 86400
                else:
                    logger.warning(f"计划不支持试用: {plan_id}")
                    return None
            elif subscription_months is not None:
                end_date = time.time() + subscription_months * 30 * 86400
            
            # 创建订阅
            subscription = UserPlanSubscription(
                subscription_id=subscription_id,
                user_id=user_id,
                plan_id=plan_id,
                is_active=True,
                is_trial=is_trial,
                start_date=time.time(),
                end_date=end_date,
                payment_id=payment_id
            )
            
            self.subscriptions[subscription_id] = subscription
            
            # 保存到文件
            self._save_subscriptions()
            
            logger.info(f"用户 {user_id} 订阅计划 {plan_id}")
            return subscription_id
    
    def cancel_subscription(self, subscription_id: str) -> bool:
        """
        取消订阅
        
        Args:
            subscription_id: 订阅ID
            
        Returns:
            是否成功取消
        """
        with self.lock:
            # 检查订阅是否存在
            if subscription_id not in self.subscriptions:
                logger.warning(f"订阅不存在: {subscription_id}")
                return False
            
            # 更新订阅状态
            self.subscriptions[subscription_id].is_active = False
            self.subscriptions[subscription_id].updated_at = time.time()
            
            # 保存到文件
            self._save_subscriptions()
            
            logger.info(f"取消订阅: {subscription_id}")
            return True
    
    def get_user_subscription(self, user_id: str) -> Optional[UserPlanSubscription]:
        """
        获取用户当前的活跃订阅
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户订阅，如果不存在则返回None
        """
        now = time.time()
        
        for sub in self.subscriptions.values():
            if sub.user_id == user_id and sub.is_active:
                # 检查是否过期
                if sub.end_date and sub.end_date < now:
                    # 自动处理过期
                    sub.is_active = False
                    sub.updated_at = now
                    self._save_subscriptions()
                    logger.info(f"订阅已过期: {sub.subscription_id}, 用户: {user_id}")
                    continue
                
                return sub
        
        return None
    
    def get_user_plan(self, user_id: str) -> Optional[ServicePlan]:
        """
        获取用户当前的计划
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户计划，如果不存在则返回默认的免费计划
        """
        # 获取用户订阅
        subscription = self.get_user_subscription(user_id)
        
        if subscription and subscription.is_active:
            plan = self.get_plan(subscription.plan_id)
            if plan and plan.is_active:
                return plan
        
        # 如果没有活跃订阅，返回免费计划
        return self.get_plan("free")
    
    def get_user_permissions(self, user_id: str) -> List[str]:
        """
        获取用户计划的基础权限
        
        Args:
            user_id: 用户ID
            
        Returns:
            权限列表
        """
        plan = self.get_user_plan(user_id)
        return plan.base_permissions if plan else []
    
    def get_user_resource_limits(self, user_id: str) -> ResourceLimits:
        """
        获取用户的资源限制
        
        Args:
            user_id: 用户ID
            
        Returns:
            资源限制
        """
        plan = self.get_user_plan(user_id)
        return plan.resource_limits if plan else ResourceLimits()
    
    def is_feature_allowed(self, user_id: str, feature_name: str) -> bool:
        """
        检查用户是否有权限使用指定功能
        
        Args:
            user_id: 用户ID
            feature_name: 功能名称 (如 "model:gpt-4", "tool:data-analysis", "fine-tuning" 等)
            
        Returns:
            是否允许
        """
        plan = self.get_user_plan(user_id)
        if not plan:
            return False
        
        feature_access = plan.feature_access
        
        # 检查模型
        if feature_name.startswith("model:"):
            model_name = feature_name[6:]
            if "*" in feature_access.allowed_models:
                return True
            return model_name in feature_access.allowed_models
        
        # 检查工具
        elif feature_name.startswith("tool:"):
            tool_name = feature_name[5:]
            if "*" in feature_access.allowed_tools:
                return True
            return tool_name in feature_access.allowed_tools
        
        # 检查其他功能
        elif feature_name == "fine-tuning":
            return feature_access.fine_tuning_allowed
        elif feature_name == "custom-prompts":
            return feature_access.custom_prompts_allowed
        elif feature_name == "team-collaboration":
            return feature_access.team_collaboration
        elif feature_name == "api-access":
            return feature_access.api_access
        elif feature_name == "webhook":
            return feature_access.webhook_support
        elif feature_name == "advanced-analytics":
            return feature_access.advanced_analytics
        
        return False
    
    def clean_expired_subscriptions(self) -> int:
        """
        清理过期的订阅
        
        Returns:
            清理的订阅数量
        """
        with self.lock:
            count = 0
            now = time.time()
            
            for sub_id, sub in list(self.subscriptions.items()):
                if sub.is_active and sub.end_date and sub.end_date < now:
                    sub.is_active = False
                    sub.updated_at = now
                    count += 1
                    logger.info(f"订阅已过期: {sub_id}, 用户: {sub.user_id}")
            
            if count > 0:
                self._save_subscriptions()
            
            return count

# 创建全局服务计划管理器实例
service_plan_manager = ServicePlanManager() 