#!/usr/bin/env python
"""
系统诊断命令行工具

这个脚本提供了命令行界面来运行系统诊断，检查系统配置问题，
并尝试自动修复发现的问题。

使用方法:
    python -m agent_cores.diagnose [--verbose] [--no-fix]
"""
import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# 导入诊断工具
from agent_cores.tools.example.diagnostics import diagnostics


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="SSS Agent Platform 系统诊断工具")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细诊断信息")
    parser.add_argument("--no-fix", "-n", action="store_true", help="不自动修复发现的问题")
    parser.add_argument("--templates", "-t", action="store_true", help="只检查模板配置")
    parser.add_argument("--ssl", "-s", action="store_true", help="只检查SSL配置")
    parser.add_argument("--api", "-a", action="store_true", help="只检查API连接")
    parser.add_argument("--create-default", "-c", action="store_true", help="创建默认模板")
    
    args = parser.parse_args()
    
    # 设置是否自动修复
    fix = not args.no_fix
    
    try:
        # 欢迎信息
        print("\n" + "="*60)
        print("SSS Agent Platform 系统诊断工具")
        print("="*60)
        
        # 如果指定了特定检查
        if args.templates or args.ssl or args.api:
            if args.templates:
                print("\n执行模板配置检查...")
                template_report = diagnostics.diagnose_templates()
                print(f"找到 {template_report['templates_found']} 个模板配置")
                print(f"成功加载 {template_report['templates_loaded']} 个模板")
                
                if template_report['templates_failed'] > 0:
                    print(f"加载失败 {template_report['templates_failed']} 个模板")
                
                if args.verbose and template_report['config_files']:
                    print("\n模板配置文件:")
                    for config_file in template_report['config_files']:
                        print(f"  - {config_file}")
                
                if args.create_default and template_report['templates_loaded'] == 0:
                    print("\n创建默认模板...")
                    diagnostics.diagnose_templates()  # 再次运行会创建默认模板
            
            if args.ssl:
                print("\n执行SSL配置检查...")
                ssl_report = diagnostics.diagnose_ssl()
                print(f"SSL模块: {'可用' if ssl_report['ssl_available'] else '不可用'}")
                print(f"SSL默认上下文: {'正常' if ssl_report['default_context_works'] else '异常'}")
                print(f"证书文件: {'已找到' if ssl_report['cert_file_exists'] else '未找到'}")
                
                if ssl_report['cert_path']:
                    print(f"证书路径: {ssl_report['cert_path']}")
            
            if args.api:
                print("\n执行API连接检查...")
                api_report = diagnostics.diagnose_api_connection()
                print(f"OpenAI API密钥: {'已设置' if api_report['openai_api_key'] else '未设置'}")
                print(f"API连接测试: {'成功' if api_report['connection_works'] else '失败'}")
                
                if not api_report['connection_works'] and api_report['error_message']:
                    print(f"错误信息: {api_report['error_message']}")
        else:
            # 执行完整诊断
            print("\n执行完整系统诊断...")
            report = diagnostics.run_all_diagnostics()
            
            # 输出系统状态
            status_emoji = "✅" if report['system_status'] == "ok" else "⚠️" if report['system_status'] == "warning" else "❌"
            print(f"\n系统状态: {status_emoji} {report['system_status'].upper()}")
            print(f"已修复问题: {report['total_problems_fixed']} 个")
            print(f"可用模板: {report['templates_available']} 个")
            print(f"注册工具: {report['tools_registered']} 个")
            
            # 输出模板诊断结果
            template_report = report['template_diagnostics']
            print("\n[模板配置]")
            print(f"配置目录: {'✅ 存在' if template_report['config_dir_exists'] else '❌ 不存在'}")
            print(f"找到模板: {template_report['templates_found']} 个")
            print(f"加载成功: {template_report['templates_loaded']} 个")
            
            if template_report['templates_failed'] > 0:
                print(f"加载失败: {template_report['templates_failed']} 个")
            
            # 输出SSL诊断结果
            ssl_report = report['ssl_diagnostics']
            print("\n[SSL配置]")
            print(f"SSL模块: {'✅ 可用' if ssl_report['ssl_available'] else '❌ 不可用'}")
            print(f"SSL上下文: {'✅ 正常' if ssl_report['default_context_works'] else '❌ 异常'}")
            print(f"证书文件: {'✅ 已找到' if ssl_report['cert_file_exists'] else '❌ 未找到'}")
            
            # 输出API诊断结果
            api_report = report['api_diagnostics']
            print("\n[API连接]")
            print(f"API密钥: {'✅ 已设置' if api_report['openai_api_key'] else '❌ 未设置'}")
            print(f"连接测试: {'✅ 成功' if api_report['connection_works'] else '❌ 失败'}")
            
            if not api_report['connection_works'] and api_report['error_message']:
                print(f"错误信息: {api_report['error_message']}")
            
            # 输出详细信息
            if args.verbose:
                import json
                print("\n" + "="*60)
                print("详细诊断报告")
                print("="*60)
                print(json.dumps(report, indent=2, ensure_ascii=False))
        
        # 结束信息
        print("\n诊断完成，如需更详细的信息，请使用 --verbose 参数。")
        
    except Exception as e:
        logger.error(f"诊断过程中出错: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 