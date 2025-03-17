"""
RBAC权限控制示例脚本

演示如何使用RBAC系统控制代理工具的访问权限
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入所需模块
from agent_cores.core.runtime import RuntimeService
from agent_cores.models.rbac import Role


async def test_rbac_permissions():
    """测试不同角色的权限控制"""
    
    # 创建运行时服务
    runtime = RuntimeService()
    
    print("\n==== RBAC权限控制示例 ====\n")
    
    # 创建不同权限的会话
    guest_session = runtime.create_session(
        user_id="guest_user",
        roles=[Role.GUEST.value],
        metadata={"description": "访客会话"}
    )
    
    user_session = runtime.create_session(
        user_id="normal_user", 
        roles=[Role.USER.value],
        metadata={"description": "普通用户会话"}
    )
    
    admin_session = runtime.create_session(
        user_id="admin_user",
        roles=[Role.ADMIN.value],
        metadata={"description": "管理员会话"}
    )
    
    # 测试访客权限 - 只能使用基本工具
    print("\n===== 访客权限测试 =====")
    guest_result = await runtime.run_agent(
        session_id=guest_session,
        input_text="查询北京的天气，然后执行3+4的计算，再尝试搜索数据库",
        template_name="user_agent"  
    )
    
    print(f"访客输出:\n{guest_result.get('output', 'No output')}")
    
    # 测试普通用户权限 - 可以使用所有常规工具
    print("\n===== 普通用户权限测试 =====")
    user_result = await runtime.run_agent(
        session_id=user_session,
        input_text="查询北京的天气，执行3+4的计算，然后搜索数据库的用户表，最后列出我的权限",
        template_name="user_agent"
    )
    
    print(f"普通用户输出:\n{user_result.get('output', 'No output')}")
    
    # 测试管理员权限 - 可以使用所有工具
    print("\n===== 管理员权限测试 =====")
    admin_result = await runtime.run_agent(
        session_id=admin_session,
        input_text="列出我的角色和权限，然后检查我是否有权限在system/config上执行update操作",
        template_name="admin_agent"
    )
    
    print(f"管理员输出:\n{admin_result.get('output', 'No output')}")
    
    # 测试权限更新
    print("\n===== 权限更新测试 =====")
    # 将普通用户升级为高级用户
    runtime.update_session_roles(user_session, [Role.POWER_USER.value])
    
    # 再次测试
    power_user_result = await runtime.run_agent(
        session_id=user_session,
        input_text="检查我当前的角色和权限",
        template_name="admin_agent"  # 尝试使用管理员代理
    )
    
    print(f"高级用户输出:\n{power_user_result.get('output', 'No output')}")
    
    print("\n==== RBAC权限控制示例结束 ====\n")


if __name__ == "__main__":
    asyncio.run(test_rbac_permissions()) 