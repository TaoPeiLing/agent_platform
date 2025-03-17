"""
系统检查工具

这个脚本演示如何使用系统诊断工具检查和修复代理系统的配置问题。
使用方法: python system_check.py [选项]
"""
import sys
import json
import logging
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
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

# 导入其他组件
from agent_cores.core import template_manager
from agent_cores.tools import tool_manager


def check_system(fix=True, verbose=False):
    """
    检查系统配置并显示诊断结果
    
    Args:
        fix: 是否自动修复问题
        verbose: 是否显示详细信息
    """
    logger.info("开始系统检查...")
    
    # 运行完整诊断
    report = diagnostics.run_all_diagnostics()
    
    # 输出系统状态
    print("\n" + "="*60)
    print(f"系统状态: {report['system_status'].upper()}")
    print("="*60)
    
    # 输出系统摘要
    print(f"\n可用模板: {report['templates_available']} | 注册工具: {report['tools_registered']} | 修复的问题: {report['total_problems_fixed']}")
    
    # 输出模板诊断
    template_report = report['template_diagnostics']
    print("\n[模板配置]")
    print(f"✓ 找到模板配置目录: {'是' if template_report['config_dir_exists'] else '否'}")
    print(f"✓ 找到模板文件: {template_report['templates_found']}个")
    print(f"✓ 成功加载: {template_report['templates_loaded']}个")
    
    if template_report['templates_failed'] > 0:
        print(f"✗ 加载失败: {template_report['templates_failed']}个")
        
        if verbose:
            for failed in template_report['failed_templates']:
                print(f"  - {failed}")
    
    # 输出SSL诊断
    ssl_report = report['ssl_diagnostics']
    print("\n[SSL配置]")
    print(f"✓ SSL模块可用: {'是' if ssl_report['ssl_available'] else '否'}")
    print(f"✓ SSL默认上下文: {'正常' if ssl_report['default_context_works'] else '异常'}")
    print(f"✓ 证书文件: {'已找到' if ssl_report['cert_file_exists'] else '未找到'}")
    
    if verbose and ssl_report['cert_path']:
        print(f"  - 证书路径: {ssl_report['cert_path']}")
    
    # 输出API诊断
    api_report = report['api_diagnostics']
    print("\n[API连接]")
    print(f"✓ API密钥: {'已设置' if api_report['openai_api_key'] else '未设置'}")
    print(f"✓ 连接测试: {'成功' if api_report['connection_works'] else '失败'}")
    
    if not api_report['connection_works'] and api_report['error_message']:
        print(f"  - 错误: {api_report['error_message']}")
    
    # 显示可用的代理模板
    if report['templates_available'] > 0:
        print("\n[可用代理模板]")
        templates = template_manager.list_templates()
        for template in templates:
            print(f"  - {template}")
    
    # 显示可用的工具
    if report['tools_registered'] > 0:
        print("\n[可用工具]")
        tools = tool_manager.list_tools()
        for tool in tools:
            print(f"  - {tool}")
    
    # 输出报告详情
    if verbose:
        print("\n" + "="*60)
        print("详细诊断报告")
        print("="*60)
        print(json.dumps(report, indent=2, ensure_ascii=False))
    
    # 返回报告结果
    return report


def check_templates(create_default=False, verbose=False):
    """
    检查并显示模板配置信息
    
    Args:
        create_default: 是否创建默认模板
        verbose: 是否显示详细信息
    """
    logger.info("检查模板配置...")
    
    # 运行模板诊断
    report = diagnostics.diagnose_templates()
    
    # 输出摘要
    print("\n" + "="*60)
    print("模板配置检查")
    print("="*60)
    
    # 检查配置目录
    print(f"\n✓ 模板配置目录: {'存在' if report['config_dir_exists'] else '不存在'}")
    
    # 检查配置文件
    print(f"✓ 找到模板文件: {report['templates_found']}个")
    print(f"✓ 成功加载: {report['templates_loaded']}个")
    
    if report['templates_failed'] > 0:
        print(f"✗ 加载失败: {report['templates_failed']}个")
        for failed in report['failed_templates']:
            print(f"  - {failed}")
    
    # 列出模板文件
    if verbose and report['config_files']:
        print("\n模板配置文件:")
        for config_file in report['config_files']:
            print(f"  - {config_file}")
    
    # 如果没有模板并且需要创建默认模板
    if report['templates_loaded'] == 0 and create_default:
        print("\n创建默认模板...")
        
        # 再次运行诊断，这次会创建默认模板
        updated_report = diagnostics.diagnose_templates()
        
        if updated_report['templates_loaded'] > 0:
            print(f"✓ 已创建并加载默认模板: {updated_report['templates_loaded']}个")
        else:
            print("✗ 创建默认模板失败")
    
    # 列出可用模板
    templates = template_manager.list_templates()
    if templates:
        print("\n可用模板:")
        for template in templates:
            print(f"  - {template}")
    
    return report


def check_ssl(fix=True, verbose=False):
    """
    检查SSL配置并显示诊断结果
    
    Args:
        fix: 是否自动修复问题
        verbose: 是否显示详细信息
    """
    logger.info("检查SSL配置...")
    
    # 运行SSL诊断
    report = diagnostics.diagnose_ssl()
    
    # 输出摘要
    print("\n" + "="*60)
    print("SSL配置检查")
    print("="*60)
    
    # 检查SSL模块
    print(f"\n✓ SSL模块: {'可用' if report['ssl_available'] else '不可用'}")
    
    # 检查SSL上下文
    print(f"✓ SSL默认上下文: {'正常' if report['default_context_works'] else '异常'}")
    
    # 检查证书文件
    print(f"✓ 证书文件: {'已找到' if report['cert_file_exists'] else '未找到'}")
    
    if report['cert_file_exists'] and report['cert_path']:
        print(f"  - 证书路径: {report['cert_path']}")
    
    # 如果有问题且需要修复
    if fix and not report['cert_file_exists']:
        print("\n尝试修复SSL证书问题...")
        
        # 再次运行诊断，这次会尝试修复
        updated_report = diagnostics.diagnose_ssl()
        
        if updated_report['cert_file_exists']:
            print(f"✓ 已找到并设置证书: {updated_report['cert_path']}")
        else:
            print("✗ 修复SSL证书问题失败")
            print("  建议安装certifi包: pip install certifi")
    
    return report


def check_api(verbose=False):
    """
    检查API连接并显示诊断结果
    
    Args:
        verbose: 是否显示详细信息
    """
    logger.info("检查API连接...")
    
    # 运行API连接诊断
    report = diagnostics.diagnose_api_connection()
    
    # 输出摘要
    print("\n" + "="*60)
    print("API连接检查")
    print("="*60)
    
    # 检查API密钥
    print(f"\n✓ OpenAI API密钥: {'已设置' if report['openai_api_key'] else '未设置'}")
    
    # 检查API连接
    print(f"✓ API连接测试: {'成功' if report['connection_works'] else '失败'}")
    
    if not report['connection_works'] and report['error_message']:
        print(f"  - 错误信息: {report['error_message']}")
    
    # 如果API密钥未设置，给出提示
    if not report['openai_api_key']:
        print("\n要使用OpenAI API，请设置OPENAI_API_KEY环境变量:")
        print("  - Windows: set OPENAI_API_KEY=你的密钥")
        print("  - Linux/Mac: export OPENAI_API_KEY=你的密钥")
        print("  - 或在项目根目录创建.env文件并添加: OPENAI_API_KEY=你的密钥")
    
    return report


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="系统检查工具")
    parser.add_argument("--all", action="store_true", help="执行所有检查")
    parser.add_argument("--templates", action="store_true", help="检查模板配置")
    parser.add_argument("--ssl", action="store_true", help="检查SSL配置")
    parser.add_argument("--api", action="store_true", help="检查API连接")
    parser.add_argument("--create-default", action="store_true", help="创建默认模板")
    parser.add_argument("--no-fix", action="store_true", help="不自动修复问题")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    
    args = parser.parse_args()
    
    # 如果没有指定任何选项，默认执行所有检查
    if not (args.all or args.templates or args.ssl or args.api):
        args.all = True
    
    # 是否自动修复问题
    fix = not args.no_fix
    
    # 执行系统检查
    if args.all:
        check_system(fix=fix, verbose=args.verbose)
    else:
        if args.templates:
            check_templates(create_default=args.create_default, verbose=args.verbose)
        
        if args.ssl:
            check_ssl(fix=fix, verbose=args.verbose)
        
        if args.api:
            check_api(verbose=args.verbose)
    
    # 结束提示
    print("\n系统检查完成。")


if __name__ == "__main__":
    main() 