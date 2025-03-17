"""
系统诊断工具 - 用于检查和修复系统配置问题

提供了一系列工具函数，用于诊断模板配置、SSL证书和API连接等问题。
"""
import os
import sys
import json
import logging
import ssl
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# 配置日志
logger = logging.getLogger(__name__)

# 导入核心组件
# 注释掉导致循环导入的import
# from agent_cores.core.template_manager import template_manager
from agent_cores.tools import tool_manager

class SystemDiagnostics:
    """系统诊断工具类"""
    
    @staticmethod
    def diagnose_templates() -> Dict[str, Any]:
        """
        诊断模板配置并尝试修复问题
        
        Returns:
            诊断结果报告
        """
        # 延迟导入template_manager，避免循环导入
        from agent_cores.core.template_manager import template_manager
        
        report = {
            "templates_found": 0,
            "templates_loaded": 0,
            "templates_failed": 0,
            "failed_templates": [],
            "fixed_problems": 0,
            "config_dir_exists": False,
            "config_files": []
        }
        
        # 检查配置目录
        project_root = Path(__file__).parent.parent.parent
        config_dir = os.path.join(project_root, "agent_configs", "agents")
        report["config_dir_exists"] = os.path.exists(config_dir)
        
        if not report["config_dir_exists"]:
            logger.error(f"代理配置目录不存在: {config_dir}")
            # 尝试创建目录
            try:
                os.makedirs(config_dir, exist_ok=True)
                report["fixed_problems"] += 1
                report["config_dir_exists"] = True
                logger.info(f"已创建代理配置目录: {config_dir}")
            except Exception as e:
                logger.error(f"创建配置目录失败: {e}")
            return report
            
        # 检查配置文件
        json_files = list(Path(config_dir).glob("*.json"))
        report["templates_found"] = len(json_files)
        report["config_files"] = [str(f) for f in json_files]
        
        # 验证每个配置文件
        for json_file in json_files:
            try:
                # 尝试加载JSON
                with open(json_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                # 检查必要字段
                valid = True
                if "name" not in config:
                    logger.warning(f"配置文件缺少name字段: {json_file}")
                    valid = False
                    
                if "instructions" not in config:
                    logger.warning(f"配置文件缺少instructions字段: {json_file}")
                    valid = False
                
                # 如果有效，则尝试加载模板
                if valid:
                    template_name = json_file.stem
                    agent = template_manager._load_template_from_file(str(json_file))
                    if agent:
                        report["templates_loaded"] += 1
                    else:
                        report["templates_failed"] += 1
                        report["failed_templates"].append(str(json_file))
                else:
                    report["templates_failed"] += 1
                    report["failed_templates"].append(str(json_file))
                    
            except json.JSONDecodeError as e:
                logger.error(f"无效的JSON格式 {json_file}: {e}")
                report["templates_failed"] += 1
                report["failed_templates"].append(str(json_file))
            except Exception as e:
                logger.error(f"检查模板失败 {json_file}: {e}")
                report["templates_failed"] += 1
                report["failed_templates"].append(str(json_file))
                
        # 如果没有可用模板，创建默认模板
        if report["templates_loaded"] == 0:
            logger.warning("未发现有效模板，创建默认模板")
            try:
                # 创建默认模板配置
                default_template = {
                    "name": "默认助手",
                    "instructions": "你是一个友好、乐于助人的AI助手。认真回答问题，提供有用的信息。",
                    "model": "gpt-3.5-turbo-0125",  # 直接使用字符串而不是字典
                    "model_settings": {
                        "temperature": 0.7,
                        "top_p": 1.0
                    }
                }
                
                # 保存到文件
                default_file = os.path.join(config_dir, "assistant_agent.json")
                with open(default_file, 'w', encoding='utf-8') as f:
                    json.dump(default_template, f, ensure_ascii=False, indent=4)
                    
                report["fixed_problems"] += 1
                report["templates_found"] += 1
                report["config_files"].append(default_file)
                logger.info(f"已创建默认模板配置: {default_file}")
                
                # 加载新创建的模板
                template_manager._load_template_from_file(default_file)
                report["templates_loaded"] += 1
                
            except Exception as e:
                logger.error(f"创建默认模板失败: {e}")
                
        return report
        
    @staticmethod
    def diagnose_ssl() -> Dict[str, Any]:
        """
        诊断SSL证书问题
        
        Returns:
            诊断结果报告
        """
        report = {
            "ssl_available": False,
            "default_context_works": False,
            "fixed_problems": 0,
            "cert_file_exists": False,
            "cert_path": None
        }
        
        try:
            # 检查SSL模块
            import ssl
            report["ssl_available"] = True
            
            # 尝试创建默认上下文
            try:
                context = ssl.create_default_context()
                report["default_context_works"] = True
            except Exception as e:
                logger.error(f"创建SSL上下文失败: {e}")
                
            # 检查证书文件
            cert_file = ssl.get_default_verify_paths().cafile
            if cert_file and os.path.exists(cert_file):
                report["cert_file_exists"] = True
                report["cert_path"] = cert_file
            else:
                logger.warning(f"找不到SSL证书文件: {cert_file}")
                
                # 尝试修复证书问题
                try:
                    import certifi
                    cert_file = certifi.where()
                    if os.path.exists(cert_file):
                        report["cert_file_exists"] = True
                        report["cert_path"] = cert_file
                        report["fixed_problems"] += 1
                        logger.info(f"使用certifi提供的证书: {cert_file}")
                        
                        # 设置环境变量
                        os.environ['SSL_CERT_FILE'] = cert_file
                        os.environ['REQUESTS_CA_BUNDLE'] = cert_file
                except ImportError:
                    logger.error("无法导入certifi库，请安装: pip install certifi")
                except Exception as e:
                    logger.error(f"修复证书问题失败: {e}")
            
        except ImportError:
            logger.error("无法导入ssl模块")
            
        return report
        
    @staticmethod
    def diagnose_api_connection() -> Dict[str, Any]:
        """
        诊断API连接问题
        
        Returns:
            诊断结果报告
        """
        report = {
            "openai_api_key": False,
            "connection_works": False,
            "error_message": None,
            "fixed_problems": 0
        }
        
        # 检查API密钥
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            report["openai_api_key"] = True
        else:
            logger.warning("未设置OPENAI_API_KEY环境变量")
            
            # 尝试从.env文件加载
            try:
                from dotenv import load_dotenv
                load_dotenv()
                
                api_key = os.environ.get("OPENAI_API_KEY")
                if api_key:
                    report["openai_api_key"] = True
                    report["fixed_problems"] += 1
                    logger.info("已从.env文件加载OPENAI_API_KEY")
            except ImportError:
                logger.error("无法导入dotenv库，请安装: pip install python-dotenv")
            except Exception as e:
                logger.error(f"加载.env文件失败: {e}")
                
        # 测试API连接
        if report["openai_api_key"]:
            try:
                import httpx
                
                # 使用httpx发送测试请求
                client = httpx.Client(timeout=10.0)
                response = client.get("https://api.openai.com/v1/models")
                
                if response.status_code == 200:
                    report["connection_works"] = True
                    logger.info("API连接测试成功")
                else:
                    report["error_message"] = f"HTTP错误: {response.status_code}"
                    logger.error(f"API连接测试失败: {response.status_code}")
            except Exception as e:
                report["error_message"] = str(e)
                logger.error(f"API连接测试异常: {e}")
                
        return report
        
    @staticmethod
    def run_all_diagnostics() -> Dict[str, Any]:
        """
        运行所有诊断工具
        
        Returns:
            完整诊断报告
        """
        # 延迟导入template_manager，避免循环导入
        from agent_cores.core.template_manager import template_manager
        
        logger.info("开始系统诊断...")
        
        # 运行所有诊断
        template_report = SystemDiagnostics.diagnose_templates()
        ssl_report = SystemDiagnostics.diagnose_ssl()
        api_report = SystemDiagnostics.diagnose_api_connection()
        
        # 汇总结果
        report = {
            "template_diagnostics": template_report,
            "ssl_diagnostics": ssl_report,
            "api_diagnostics": api_report,
            "total_problems_fixed": (
                template_report["fixed_problems"] + 
                ssl_report["fixed_problems"] + 
                api_report["fixed_problems"]
            ),
            "system_status": "ok",
            "tools_registered": len(tool_manager.tools),  # 使用tools属性而不是list_tools方法
            "templates_available": len(template_manager.list_templates())
        }
        
        # 确定系统状态
        if (template_report["templates_loaded"] == 0 or 
            not ssl_report["default_context_works"] or 
            not api_report["connection_works"]):
            report["system_status"] = "warning"
            
        if (not report["template_diagnostics"]["config_dir_exists"] or
            not report["ssl_diagnostics"]["ssl_available"] or
            not report["api_diagnostics"]["openai_api_key"]):
            report["system_status"] = "error"
            
        logger.info(f"系统诊断完成，状态: {report['system_status']}")
        return report


# 创建诊断工具实例
diagnostics = SystemDiagnostics()

# 对外公开的诊断函数
def diagnose_system() -> Dict[str, Any]:
    """
    运行系统诊断并返回报告
    
    Returns:
        诊断报告
    """
    return diagnostics.run_all_diagnostics() 