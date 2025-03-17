"""
模板管理器模块 - 负责加载、缓存和管理代理模板

实现延迟加载模式和容错机制，确保模板注册的可靠性。
"""
import os
import json
import logging
import sys
import importlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 代理配置目录
AGENT_CONFIG_DIR = os.path.join(project_root, "agent_configs", "agents")

# 确保目录存在
os.makedirs(AGENT_CONFIG_DIR, exist_ok=True)

# 导入OpenAI Agent SDK
from agents import Agent, ModelSettings,OpenAIChatCompletionsModel,AsyncOpenAI
from agents.models import _openai_shared

# 避免循环导入，将导入移到方法内部
# from agent_cores.tools.tool_manager import ToolManager

logger = logging.getLogger(__name__)

class TemplateManager:
    """
    模板管理器 - 负责加载、缓存和管理代理模板
    
    实现了延迟加载模式，避免启动时的初始化问题，
    并提供了多重错误恢复机制。
    """
    
    def __init__(self):
        self.templates: Dict[str, Agent] = {}
        self.template_configs: Dict[str, Dict[str, Any]] = {}
        self.template_paths: Dict[str, str] = {}
        self.available_templates: List[str] = []
        self._discover_templates()

        # 模型提供者配置 - 延迟初始化
        self.model_providers = None
        
    def _get_model_providers(self):
        """获取模型提供者配置，确保环境变量已加载"""
        if self.model_providers is None:
            self.model_providers = {
                "zhipu": {
                    "base_url": os.getenv("ZHIPU_BASE_URL", "https://api.zhipuai.cn/v1"),
                    "api_key": os.getenv("ZHIPU_API_KEY", ""),
                    "models": ["glm-3-turbo", "glm-4", "glm-4v"]
                },
                "doubao": {
                    "base_url": os.getenv("DOUBAO_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
                    "api_key": os.getenv("DOUBAO_API_KEY", ""),
                    "models": [
                        "doubao-1.5-pro-32k",
                        "Doubao-1.5-vision-pro",
                        "doubao-1.5", 
                        "doubao"  # 通用前缀
                    ],
                    "session_id_prefix": ["e-", "ep-"]  # 同时支持e-和ep-前缀的会话ID
                },
                "baidu": {
                    "base_url": os.getenv("BAIDU_BASE_URL", "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat"),
                    "api_key": os.getenv("BAIDU_API_KEY", ""),
                    "models": ["ernie-bot", "ernie-bot-4", "ernie-bot-8k"]
                },
                # 可以添加更多提供者
            }
        return self.model_providers
    
    def _discover_templates(self):
        """
        发现可用的代理模板 - 扫描代理配置目录中的JSON文件
        """
        if not os.path.exists(AGENT_CONFIG_DIR):
            logger.warning(f"代理配置目录不存在: {AGENT_CONFIG_DIR}")
            return
            
        try:
            for file in os.listdir(AGENT_CONFIG_DIR):
                if file.endswith(".json"):
                    template_name = file[:-5]  # 去除.json后缀
                    template_path = os.path.join(AGENT_CONFIG_DIR, file)
                    self.template_paths[template_name] = template_path
                    self.available_templates.append(template_name)
                    
            logger.info(f"发现 {len(self.available_templates)} 个模板: {', '.join(self.available_templates)}")
        except Exception as e:
            logger.error(f"扫描模板目录时出错: {e}")
    
    def _load_template_config(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        加载模板配置
        
        Args:
            template_name: 模板名称
            
        Returns:
            模板配置字典或None
        """
        if template_name not in self.template_paths:
            logger.warning(f"模板不存在: {template_name}")
            return None
            
        template_path = self.template_paths[template_name]
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.template_configs[template_name] = config
            logger.info(f"成功加载模板配置: {template_name}")
            return config
        except Exception as e:
            logger.error(f"加载模板配置失败 {template_name}: {e}")
            return None
            
    def _identify_model_provider(self, model_name: str) -> Optional[str]:
        """
        识别模型所属的提供者
        
        Args:
            model_name: 模型名称
            
        Returns:
            提供者名称或None
        """
        # 先检查是否配置了默认提供者
        default_provider = os.getenv("DEFAULT_MODEL_PROVIDER")
        
        # 检查模型是否为特定提供者的格式
        for provider_name, provider_config in self._get_model_providers().items():
            # 检查会话ID前缀
            if "session_id_prefix" in provider_config:
                for prefix in provider_config["session_id_prefix"]:
                    if isinstance(model_name, str) and model_name.startswith(prefix):
                        logger.info(f"根据会话ID前缀 '{prefix}' 识别模型 '{model_name}' 为 {provider_name} 提供者")
                        return provider_name
                        
            # 精确匹配模型名称
            if model_name in provider_config["models"]:
                logger.info(f"精确匹配模型 '{model_name}' 为 {provider_name} 提供者")
                return provider_name
                
            # 更宽松的匹配，检查模型名称前缀
            for provider_model in provider_config["models"]:
                if isinstance(model_name, str) and isinstance(provider_model, str) and model_name.startswith(provider_model.split("-")[0]):
                    logger.info(f"根据前缀匹配模型 '{model_name}' 为 {provider_name} 提供者")
                    return provider_name
        
        # 如果无法识别，则使用默认提供者或返回None
        if default_provider:
            logger.info(f"无法识别模型 '{model_name}' 的提供者，使用默认提供者: {default_provider}")
            return default_provider
            
        logger.warning(f"无法识别模型 '{model_name}' 的提供者，默认使用OpenAI")
        return None
    
    def _create_agent_from_config(self, config: Dict[str, Any]) -> Optional[Agent]:
        """
        从配置创建代理实例
        
        Args:
            config: 模板配置字典
            
        Returns:
            Agent实例或None
        """
        try:
            # 处理model字段，可能是字符串或字典
            model_config = config.get("model", "gpt-3.5-turbo")
            logger.debug(f"解析模型配置: {model_config}")
            
            # 提取模型名称
            if isinstance(model_config, dict):
                model_name = model_config.get("name", "gpt-3.5-turbo")
                # 提取模型设置
                model_settings_dict = {k: v for k, v in model_config.items() 
                                     if k in ["temperature", "top_p", "presence_penalty", "frequency_penalty"]}
            else:
                # 如果model是字符串，直接使用
                model_name = model_config
                model_settings_dict = {}
                
            logger.info(f"从配置中提取的模型名称: {model_name}")
            
            # 识别模型提供者
            model_provider = self._identify_model_provider(model_name)
            
            # 创建模型实例
            model_instance = None
            
            # 如果是国产模型，使用对应的提供者
            if model_provider:
                provider_config = self._get_model_providers()[model_provider]
                api_key = provider_config["api_key"]
                base_url = provider_config["base_url"]
                
                if not api_key:
                    logger.error(f"未找到{model_provider}的API密钥，请设置环境变量{model_provider.upper()}_API_KEY")
                    return None
                
                logger.info(f"使用{model_provider}提供的模型: {model_name}")
                
                # 优先使用模型提供者工厂
                try:
                    from agent_cores.model_providers import get_provider
                    
                    # 创建模型提供者实例 - 传递配置文件中的模型名称
                    provider = get_provider(model_provider, model_name=model_name)
                    
                    # 设置客户端
                    provider.setup_client(api_key=api_key, base_url=base_url)
                    
                    # 获取模型对象
                    model_instance = provider.get_model_object()
                    
                    logger.info(f"成功使用{model_provider}模型提供者创建模型对象")
                except Exception as e:
                    logger.warning(f"使用模型提供者工厂失败: {e}，回退到直接创建模型")
                    
                    # 回退到直接创建模型
                    external_client = AsyncOpenAI(
                        api_key=api_key,
                        base_url=base_url
                    )
                    _openai_shared.set_default_openai_client(external_client)
                    # 使用OpenAIChatCompletionsModel包装模型
                    model_instance = OpenAIChatCompletionsModel(model=model_name, openai_client=external_client)
            else:
                # 使用标准OpenAI模型
                model_instance = model_name
            
            # 合并模型设置
            model_settings_from_config = config.get("model_settings", {})
            # 优先使用model_settings字段，如果为空则使用model字典中的设置
            if not model_settings_from_config and model_settings_dict:
                model_settings_from_config = model_settings_dict
                
            model_settings = None
            if model_settings_from_config:
                model_settings = ModelSettings(**model_settings_from_config)
            
            # 处理工具配置 - 将字典形式的工具转换为FunctionTool对象
            tools_config = config.get("tools", [])
            processed_tools = []
            
            if tools_config:
                from agents import FunctionTool
                
                logger.info(f"处理工具配置: 发现 {len(tools_config)} 个工具")
                
                for tool_dict in tools_config:
                    if isinstance(tool_dict, dict):
                        try:
                            # 创建一个FunctionTool对象
                            tool_name = tool_dict.get("name", "")
                            tool_description = tool_dict.get("description", "")
                            
                            logger.debug(f"处理工具: {tool_name}")
                            
                            # 获取参数模式
                            params_schema = {}
                            if "config" in tool_dict and "parameters" in tool_dict["config"]:
                                params_schema = {
                                    "type": "object",
                                    "properties": tool_dict["config"]["parameters"],
                                    "required": tool_dict["config"].get("required", [])
                                }
                            
                            # 创建一个闭包来捕获当前工具名称
                            def create_tool_function(tool_name):
                                async def on_invoke_tool(ctx, input_str):
                                    # 这里只是一个占位符，实际上工具调用会由代理处理
                                    return f"工具 {tool_name} 被调用"
                                return on_invoke_tool
                            
                            # 创建FunctionTool对象
                            function_tool = FunctionTool(
                                name=tool_name,
                                description=tool_description,
                                params_json_schema=params_schema,
                                on_invoke_tool=create_tool_function(tool_name)
                            )
                            
                            processed_tools.append(function_tool)
                            logger.debug(f"成功转换工具: {tool_name}")
                        except Exception as e:
                            logger.warning(f"处理工具配置失败: {e}")
                    else:
                        # 如果已经是Tool对象，直接使用
                        processed_tools.append(tool_dict)
                
                logger.info(f"工具处理完成: 成功转换 {len(processed_tools)} 个工具")
            
            # 创建代理实例
            agent = Agent(
                name=config.get("name", "未命名代理"),
                instructions=config.get("instructions", ""),
                model=model_instance,  # 使用模型实例，可能是字符串或OpenAIChatCompletionsModel
                model_settings=model_settings,
                tools=processed_tools,  # 使用处理后的工具
                handoffs=config.get("handoffs", []),
                input_guardrails=config.get("input_guardrails", []),
                output_guardrails=config.get("output_guardrails", []),
            )
            
            logger.info(f"成功创建代理实例: {agent.name}")
            return agent
        except Exception as e:
            logger.error(f"创建代理实例失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def get_template(self, template_name: str, system_message: str = None) -> Optional[Agent]:
        """
        获取指定模板，如果未找到则尝试直接从文件加载
        
        Args:
            template_name: 模板名称
            system_message: 可选的系统消息，如果提供则替换模板中的默认指令
            
        Returns:
            Agent实例或None
        """
        # 如果模板已加载，直接返回
        if template_name in self.templates:
            agent = self.templates[template_name]
            # 如果提供了系统消息，克隆代理并设置新指令
            if system_message:
                logger.info(f"使用自定义系统消息替换代理指令: {system_message[:50]}...")
                return agent.clone(instructions=system_message)
            return agent
            
        # 加载模板配置
        config = None
        if template_name in self.template_configs:
            config = self.template_configs[template_name]
        else:
            config = self._load_template_config(template_name)
            
        if not config:
            logger.warning(f"找不到模板: {template_name}")
            return None
        
        # 如果提供了系统消息，替换配置中的指令
        if system_message:
            config_copy = config.copy()  # 创建配置副本避免修改原始配置
            config_copy["instructions"] = system_message
            logger.info(f"使用自定义系统消息替换配置指令: {system_message[:50]}...")
            # 创建代理但不缓存
            agent = self._create_agent_from_config(config_copy)
            if agent:
                logger.info(f"成功创建带自定义系统消息的代理模板: {template_name}")
                return agent
            else:
                logger.error(f"创建带自定义系统消息的代理模板失败: {template_name}")
                return None
            
        # 创建代理
        print(f"代理config配置{config}")
        agent = self._create_agent_from_config(config)
        if agent:
            self.templates[template_name] = agent
            logger.info(f"成功创建代理模板: {template_name}")
            return agent
        
        logger.error(f"创建代理模板失败: {template_name}")
        return None
        
    def list_templates(self) -> List[str]:
        """
        列出所有可用的模板
        
        Returns:
            模板名称列表
        """
        return self.available_templates
        
    def reload_template(self, template_name: str) -> Optional[Agent]:
        """
        重新加载指定模板
        
        Args:
            template_name: 模板名称
            
        Returns:
            更新后的Agent实例或None
        """
        # 从缓存中删除模板
        if template_name in self.templates:
            del self.templates[template_name]
            
        if template_name in self.template_configs:
            del self.template_configs[template_name]
            
        # 重新加载模板
        return self.get_template(template_name)
        
    def reload_all_templates(self) -> Dict[str, Union[Agent, None]]:
        """
        重新加载所有模板
        
        Returns:
            模板名称和Agent实例的字典
        """
        # 清空缓存
        self.templates = {}
        self.template_configs = {}
        
        # 重新发现模板
        self._discover_templates()
        
        # 加载所有模板
        results = {}
        for template_name in self.available_templates:
            results[template_name] = self.get_template(template_name)
            
        return results
    
    def create_default_template(self, name: str = "assistant_agent") -> Optional[Agent]:
        """
        创建默认的助手代理模板
        
        Args:
            name: 模板名称
            
        Returns:
            创建的Agent实例或None
        """
        default_config = {
            "name": "通用助手",
            "instructions": "你是一个有用、专业、礼貌的智能助手。帮助用户解决问题，回答询问，并提供有价值的建议。尽可能提供有帮助的回答，同时注意保持对话的专业性。",
            "model": "gpt-3.5-turbo",
            "model_settings": {
                "temperature": 0.7,
                "top_p": 1.0
            }
        }
        
        # 保存默认配置到文件
        template_path = os.path.join(AGENT_CONFIG_DIR, f"{name}.json")
        try:
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
                
            # 添加到模板路径
            self.template_paths[name] = template_path
            if name not in self.available_templates:
                self.available_templates.append(name)
                
            # 加载模板
            self.template_configs[name] = default_config
            
            # 创建代理
            agent = self._create_agent_from_config(default_config)
            if agent:
                self.templates[name] = agent
                logger.info(f"成功创建默认代理模板: {name}")
                return agent
                
            logger.error(f"创建默认代理模板失败: {name}")
            return None
        except Exception as e:
            logger.error(f"创建默认模板失败: {e}")
            return None
            
    def get_or_create_default(self, template_name: str = "assistant_agent") -> Optional[Agent]:
        """
        获取指定模板，如果不存在则创建默认模板
        
        Args:
            template_name: 模板名称
            
        Returns:
            Agent实例或None
        """
        template = self.get_template(template_name)
        if template:
            return template
            
        # 创建默认模板
        logger.info(f"模板 '{template_name}' 不存在，创建默认模板")
        return self.create_default_template(template_name)
        
    def get_template_names(self) -> List[str]:
        """
        获取所有可用模板名称(兼容性方法，同list_templates)
        
        Returns:
            模板名称列表
        """
        logger.warning("get_template_names() 已弃用，请使用 list_templates()")
        return self.list_templates()
        
    def ensure_loaded(self) -> bool:
        """
        确保至少有一个模板已加载，如果没有则创建默认模板
        
        Returns:
            是否至少有一个模板可用
        """
        # 如果没有发现模板，重新扫描
        if not self.available_templates:
            self._discover_templates()
            
        # 如果仍然没有模板，创建默认模板
        if not self.available_templates:
            logger.info("未发现模板，创建默认模板")
            self.create_default_template("assistant_agent")
            
        return len(self.available_templates) > 0 and len(self.templates) > 0

# 创建全局模板管理器实例
template_manager = TemplateManager() 