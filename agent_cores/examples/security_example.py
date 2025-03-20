#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
安全模块使用示例

该示例展示如何使用安全模块的API密钥管理和JWT认证功能。
"""

import os
import sys
import logging
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入安全服务
from agent_cores.security import security_service, api_key_manager, jwt_auth_service
from agent_cores.models.rbac import Role


def run_api_key_example():
    """运行API密钥管理示例"""
    logger.info("====== API密钥管理示例 ======")
    
    # 创建服务账户
    service_account = api_key_manager.create_service_account(
        name="测试服务账户",
        description="用于测试的服务账户",
        roles=[Role.USER.value],
        permissions=["api.read", "api.write"],
        metadata={"env": "development"}
    )
    
    logger.info(f"创建服务账户: {service_account.name} (ID: {service_account.id})")
    
    # 创建API密钥
    api_key_response = api_key_manager.create_api_key(
        service_account_id=service_account.id,
        description="测试密钥",
        expires_in_days=90,
        permissions=["api.read"]  # 只有读权限
    )
    
    if api_key_response:
        logger.info(f"创建API密钥: {api_key_response.prefix}*** (完整密钥仅显示一次: {api_key_response.full_key})")
        
        # 验证API密钥
        auth_result = api_key_manager.verify_api_key(api_key_response.full_key)
        
        if auth_result.success:
            logger.info(f"API密钥验证成功: 主题 {auth_result.subject_id}")
            logger.info(f"角色: {auth_result.roles}")
            logger.info(f"权限: {auth_result.permissions}")
        else:
            logger.error(f"API密钥验证失败: {auth_result.error}")
        
        # 列出所有API密钥
        all_keys = api_key_manager.list_api_keys()
        logger.info(f"当前API密钥数量: {len(all_keys)}")
        
        # 轮换API密钥
        new_key_response = api_key_manager.rotate_api_key(
            old_key_prefix=api_key_response.prefix,
            new_description="轮换后的测试密钥",
            expires_in_days=180
        )
        
        if new_key_response:
            logger.info(f"密钥轮换成功: 新密钥 {new_key_response.prefix}*** (完整密钥: {new_key_response.full_key})")
            
            # 验证旧密钥是否已失效
            old_auth = api_key_manager.verify_api_key(api_key_response.full_key)
            if not old_auth.success:
                logger.info(f"旧密钥已失效: {old_auth.error}")
            
            # 生成使用报告
            usage_report = api_key_manager.get_usage_report()
            logger.info(f"使用报告: 活跃密钥 {usage_report['active_keys']}, 过期密钥 {usage_report['expired_keys']}, 撤销密钥 {usage_report['revoked_keys']}")
    else:
        logger.error("创建API密钥失败")


def run_jwt_example():
    """运行JWT认证示例"""
    logger.info("====== JWT认证示例 ======")
    
    # 创建JWT令牌对
    token_pair = jwt_auth_service.create_token_pair(
        subject="user123",
        roles=[Role.USER.value],
        permissions=["api.read", "api.write"],
        metadata={"username": "测试用户", "email": "test@example.com"}
    )
    
    access_token = token_pair["access_token"]
    refresh_token = token_pair["refresh_token"]
    
    logger.info(f"创建访问令牌: {access_token[:20]}...")
    logger.info(f"创建刷新令牌: {refresh_token[:20]}...")
    
    # 验证访问令牌
    auth_result = jwt_auth_service.verify_token(access_token)
    
    if auth_result.success:
        logger.info(f"JWT令牌验证成功: 主题 {auth_result.subject_id}")
        logger.info(f"角色: {auth_result.roles}")
        logger.info(f"权限: {auth_result.permissions}")
        logger.info(f"元数据: {auth_result.metadata}")
    else:
        logger.error(f"JWT令牌验证失败: {auth_result.error}")
    
    # 从Authorization头部提取令牌
    auth_header = f"Bearer {access_token}"
    extracted_token = jwt_auth_service.extract_token_from_header(auth_header)
    
    if extracted_token == access_token:
        logger.info("从Authorization头部提取令牌成功")
    
    # 刷新访问令牌
    new_token_dict = jwt_auth_service.refresh_access_token(refresh_token)
    
    if new_token_dict:
        new_access_token = new_token_dict["access_token"]
        logger.info(f"刷新访问令牌成功: {new_access_token[:20]}...")
        
        # 验证新令牌
        new_auth_result = jwt_auth_service.verify_token(new_access_token)
        if new_auth_result.success:
            logger.info("新访问令牌验证成功")
    else:
        logger.error("刷新访问令牌失败")


def run_security_service_example():
    """运行安全服务示例"""
    logger.info("====== 安全服务综合示例 ======")
    
    # 创建服务账户
    service_account = security_service.create_service_account(
        name="综合测试账户",
        description="用于综合测试的服务账户",
        roles=[Role.USER.value, Role.DEVELOPER.value],
        permissions=["api.read", "api.write", "api.admin"]
    )
    
    logger.info(f"创建服务账户: {service_account.name} (ID: {service_account.id})")
    
    # 创建API密钥
    api_key_response = security_service.create_api_key(
        service_account_id=service_account.id,
        description="综合测试密钥",
        permissions=["api.read", "api.write"]
    )
    
    if not api_key_response:
        logger.error("创建API密钥失败")
        return
        
    api_key = api_key_response.full_key
    logger.info(f"创建API密钥: {api_key[:10]}...")
    
    # 创建JWT令牌对
    token_pair = security_service.create_jwt_token_pair(
        subject="user456",
        roles=[Role.USER.value],
        permissions=["api.read"]
    )
    
    jwt_token = token_pair["access_token"]
    logger.info(f"创建JWT令牌: {jwt_token[:20]}...")
    
    # 使用API密钥认证
    api_key_auth = security_service.authenticate(api_key=api_key)
    
    if api_key_auth.success:
        logger.info(f"API密钥认证成功: 类型 {api_key_auth.auth_type}")
        logger.info(f"权限: {api_key_auth.permissions}")
    else:
        logger.error(f"API密钥认证失败: {api_key_auth.error}")
    
    # 使用JWT令牌认证
    jwt_auth = security_service.authenticate(jwt_token=jwt_token)
    
    if jwt_auth.success:
        logger.info(f"JWT令牌认证成功: 类型 {jwt_auth.auth_type}")
        logger.info(f"权限: {jwt_auth.permissions}")
    else:
        logger.error(f"JWT令牌认证失败: {jwt_auth.error}")
    
    # 同时提供两种认证，API密钥优先
    both_auth = security_service.authenticate(api_key=api_key, jwt_token=jwt_token)
    logger.info(f"综合认证结果: 类型 {both_auth.auth_type}")
    
    # 撤销API密钥
    revoked = security_service.revoke_api_key(api_key_response.prefix)
    if revoked:
        logger.info("API密钥撤销成功")
        
        # 验证撤销后的密钥
        revoked_auth = security_service.authenticate(api_key=api_key)
        if not revoked_auth.success:
            logger.info(f"撤销后认证失败: {revoked_auth.error}")
    
    # 列出所有服务账户
    accounts = security_service.list_service_accounts()
    logger.info(f"服务账户数量: {len(accounts)}")
    
    # 列出所有API密钥（包括已撤销的）
    keys = security_service.list_api_keys(include_revoked=True)
    logger.info(f"API密钥数量: {len(keys)}")


def main():
    """主函数"""
    logger.info("开始安全模块示例")
    
    # 运行API密钥示例
    run_api_key_example()
    
    # 运行JWT示例
    run_jwt_example()
    
    # 运行安全服务综合示例
    run_security_service_example()
    
    logger.info("安全模块示例完成")


if __name__ == "__main__":
    main() 