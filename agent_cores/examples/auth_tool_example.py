#!/usr/bin/env python
"""
认证工具示例

演示如何创建需要外部系统认证的工具，以及如何在智能体系统中处理认证流程。
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, Optional, List, Tuple

from agent_cores.auth import (
    auth_service, 
    permission_service, 
    AuthContext, 
    SessionExtension, 
    ExternalSystemConfig, 
    Permission, 
    Role,
    ResourceType,
    ResourcePolicy
)
from agent_cores.core.runtime import runtime_service

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PropertyFundSystem:
    """模拟物业维修资金系统"""
    
    def __init__(self):
        self.system_id = "property_fund"
        self.auth_type = "api_key"  # 可以是 'oauth2', 'api_key', 'jwt', 'basic'
        self.users = {
            "user1": {
                "name": "张三",
                "properties": [
                    {"id": "prop001", "address": "海淀区某小区1号楼1单元101", "fund_balance": 5000.0},
                    {"id": "prop002", "address": "朝阳区某小区2号楼2单元202", "fund_balance": 3500.0}
                ]
            },
            "user2": {
                "name": "李四",
                "properties": [
                    {"id": "prop003", "address": "西城区某小区3号楼1单元303", "fund_balance": 6000.0}
                ]
            }
        }
        
    def register_to_auth_service(self):
        """注册到认证服务"""
        config = ExternalSystemConfig(
            system_id=self.system_id,
            auth_type=self.auth_type,
            auth_header_name="X-Property-Fund-API-Key",
            additional_params={
                "service_url": "http://property-fund-api.example.com"
            }
        )
        
        # 注册到认证服务
        auth_service.register_external_system(config)
        logger.info(f"已注册物业维修资金系统到认证服务: {self.system_id}")
        
        # 添加资源访问策略
        policy = ResourcePolicy(
            resource_id=self.system_id,
            resource_type=ResourceType.EXTERNAL_SYSTEM,
            allowed_roles=[Role.ADMIN, Role.USER],
            allowed_operations=[Permission.ACCESS]
        )
        permission_service.add_resource_policy(policy)
        
        # 添加数据访问策略
        data_policy = ResourcePolicy(
            resource_id="fund_data",
            resource_type=ResourceType.EXTERNAL_DATA,
            allowed_roles=[Role.ADMIN, Role.USER],
            allowed_operations=[Permission.READ]
        )
        permission_service.add_resource_policy(data_policy)
        
    def get_properties(self, user_id: str, auth_token: str) -> List[Dict[str, Any]]:
        """获取用户的物业列表"""
        # 模拟认证检查
        if not auth_token or auth_token != f"VALID_TOKEN_FOR_{user_id}":
            raise PermissionError("无效的认证令牌")
            
        # 获取用户数据
        user_data = self.users.get(user_id)
        if not user_data:
            return []
            
        return user_data["properties"]
        
    def get_fund_balance(self, property_id: str, user_id: str, auth_token: str) -> float:
        """获取特定物业的维修资金余额"""
        # 模拟认证检查
        if not auth_token or auth_token != f"VALID_TOKEN_FOR_{user_id}":
            raise PermissionError("无效的认证令牌")
            
        # 获取用户数据
        user_data = self.users.get(user_id)
        if not user_data:
            return 0.0
            
        # 查找物业
        for prop in user_data["properties"]:
            if prop["id"] == property_id:
                return prop["fund_balance"]
                
        return 0.0
        
    def generate_auth_token(self, user_id: str) -> Tuple[str, int]:
        """为用户生成认证令牌"""
        # 模拟令牌生成
        token = f"VALID_TOKEN_FOR_{user_id}"
        # 有效期1小时
        expiry = int(time.time()) + 3600
        
        return token, expiry


class FundQueryTool:
    """物业维修资金查询工具"""
    
    def __init__(self, property_system: PropertyFundSystem):
        self.property_system = property_system
        self.tool_id = "fund_query_tool"
        
        # 注册工具访问策略
        policy = ResourcePolicy(
            resource_id=self.tool_id,
            resource_type=ResourceType.TOOL,
            allowed_roles=[Role.ADMIN, Role.USER],
            allowed_operations=[Permission.EXECUTE]
        )
        permission_service.add_resource_policy(policy)
        
    async def execute(self, session_id: str, user_id: str, property_id: Optional[str] = None) -> Dict[str, Any]:
        """执行工具调用"""
        try:
            # 获取会话
            session = runtime_service.get_session(session_id)
            if not session:
                return {
                    "error": "会话不存在",
                    "status": "failed"
                }
                
            # 获取角色
            roles = getattr(session, "roles", [Role.USER])
            
            # 检查工具访问权限
            if not permission_service.check_tool_permission(roles, self.tool_id):
                return {
                    "error": "没有权限使用此工具",
                    "status": "failed"
                }
                
            # 检查外部系统访问权限
            if not permission_service.check_external_system_permission(roles, self.property_system.system_id):
                return {
                    "error": "没有权限访问物业维修资金系统",
                    "status": "failed"
                }
                
            # 检查外部数据访问权限
            if not permission_service.check_external_data_permission(roles, "fund_data", Permission.READ):
                return {
                    "error": "没有权限读取维修资金数据",
                    "status": "failed"
                }
                
            # 创建会话扩展
            session_extension = SessionExtension.from_session(session)
            auth_context = session_extension.auth_context
            
            # 检查令牌
            system_id = self.property_system.system_id
            if not auth_context.is_token_valid(system_id):
                # 生成新令牌（在真实环境中，这里应该重定向到登录页面）
                token, expiry = self.property_system.generate_auth_token(user_id)
                
                # 保存令牌
                auth_context.set_token(system_id, token, expiry)
                
                # 更新会话
                session_extension.update_session(session)
                
                return {
                    "status": "auth_updated",
                    "message": "已更新认证信息，请重试"
                }
                
            # 获取令牌
            token = auth_context.get_token(system_id)
            
            # 如果指定了物业ID，查询特定物业的资金余额
            if property_id:
                try:
                    balance = self.property_system.get_fund_balance(property_id, user_id, token)
                    return {
                        "status": "success",
                        "property_id": property_id,
                        "fund_balance": balance
                    }
                except PermissionError:
                    # 令牌可能已经失效，但尚未过期
                    # 重新生成令牌
                    token, expiry = self.property_system.generate_auth_token(user_id)
                    auth_context.set_token(system_id, token, expiry)
                    session_extension.update_session(session)
                    
                    # 重试查询
                    balance = self.property_system.get_fund_balance(property_id, user_id, token)
                    return {
                        "status": "success",
                        "property_id": property_id,
                        "fund_balance": balance
                    }
            else:
                # 查询所有物业
                try:
                    properties = self.property_system.get_properties(user_id, token)
                    return {
                        "status": "success",
                        "properties": properties
                    }
                except PermissionError:
                    # 令牌可能已经失效，但尚未过期
                    # 重新生成令牌
                    token, expiry = self.property_system.generate_auth_token(user_id)
                    auth_context.set_token(system_id, token, expiry)
                    session_extension.update_session(session)
                    
                    # 重试查询
                    properties = self.property_system.get_properties(user_id, token)
                    return {
                        "status": "success",
                        "properties": properties
                    }
                    
        except Exception as e:
            logger.error(f"执行查询工具时出错: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }


async def run_example():
    """运行示例"""
    logger.info("开始运行认证工具示例")
    
    # 创建物业维修资金系统
    property_system = PropertyFundSystem()
    
    # 注册到认证服务
    property_system.register_to_auth_service()
    
    # 创建查询工具
    fund_query_tool = FundQueryTool(property_system)
    
    # 创建会话
    user_id = "user1"
    session_id = runtime_service.create_session(
        user_id=user_id,
        roles=[Role.USER],
        metadata={"source": "auth_tool_example"}
    )
    
    logger.info(f"创建会话: {session_id}")
    
    # 第一次调用工具（无认证信息）
    logger.info("第一次调用工具（无认证信息）...")
    result = await fund_query_tool.execute(session_id, user_id)
    logger.info(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # 第二次调用工具（应该有认证信息了）
    logger.info("第二次调用工具（应该有认证信息了）...")
    result = await fund_query_tool.execute(session_id, user_id)
    logger.info(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # 查询特定物业
    if result["status"] == "success" and result.get("properties"):
        property_id = result["properties"][0]["id"]
        logger.info(f"查询特定物业 {property_id}...")
        result = await fund_query_tool.execute(session_id, user_id, property_id)
        logger.info(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # 测试角色权限
    logger.info("测试没有权限的用户...")
    
    # 创建一个访客会话
    guest_session_id = runtime_service.create_session(
        user_id="guest_user",
        roles=[Role.GUEST],  # 访客角色，应该没有访问权限
        metadata={"source": "auth_tool_example"}
    )
    
    # 尝试调用工具
    result = await fund_query_tool.execute(guest_session_id, "guest_user")
    logger.info(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # 模拟令牌过期
    logger.info("模拟令牌过期...")
    
    # 获取会话
    session = runtime_service.get_session(session_id)
    
    # 创建会话扩展
    session_extension = SessionExtension.from_session(session)
    
    # 设置过期的令牌
    session_extension.auth_context.auth_expiry[property_system.system_id] = int(time.time()) - 100  # 已过期
    
    # 更新会话
    session_extension.update_session(session)
    
    # 再次调用工具
    logger.info("调用工具（令牌已过期）...")
    result = await fund_query_tool.execute(session_id, user_id)
    logger.info(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    logger.info("示例运行完成")


if __name__ == "__main__":
    # 运行异步示例
    asyncio.run(run_example()) 