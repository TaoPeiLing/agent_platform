"""
基础连接器接口

定义了所有连接器都应该实现的方法和属性。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, AsyncGenerator


class ConnectorResponse:
    """连接器响应对象"""
    
    def __init__(
        self, 
        execution_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
        auth_status: Optional[Dict[str, Any]] = None
    ):
        self.execution_id = execution_id
        self.status = status  # "completed", "failed", "running", "auth_required"
        self.result = result
        self.error = error
        self.metrics = metrics or {}
        self.auth_status = auth_status  # 认证状态信息
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        result = {
            "execution_id": self.execution_id,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "metrics": self.metrics
        }
        
        # 如果需要认证，添加认证状态
        if self.auth_status:
            result["auth_status"] = self.auth_status
            
        return result
        
    @staticmethod
    def auth_required(execution_id: str, system_id: str, auth_url: str) -> 'ConnectorResponse':
        """创建需要认证的响应"""
        return ConnectorResponse(
            execution_id=execution_id,
            status="auth_required",
            auth_status={
                "system_id": system_id,
                "auth_url": auth_url,
                "message": "需要认证才能访问此资源"
            }
        )


class BaseConnector(ABC):
    """所有连接器的基类"""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        初始化连接器
        
        Args:
            config: 连接器配置
            
        Returns:
            初始化是否成功
        """
        pass
        
    @abstractmethod
    def invoke_agent(
        self, 
        agent_id: str, 
        input_data: Union[str, Dict[str, Any]], 
        options: Optional[Dict[str, Any]] = None,
        auth_context: Optional[Dict[str, Any]] = None
    ) -> ConnectorResponse:
        """
        同步调用单个智能体
        
        Args:
            agent_id: 智能体ID或模板名称
            input_data: 输入数据，可以是文本字符串或结构化数据
            options: 可选参数，如温度、最大令牌数等
            auth_context: 认证上下文，包含用户身份和授权信息
            
        Returns:
            智能体执行结果
        """
        pass
    
    @abstractmethod
    async def ainvoke_agent(
        self, 
        agent_id: str, 
        input_data: Union[str, Dict[str, Any]], 
        options: Optional[Dict[str, Any]] = None,
        auth_context: Optional[Dict[str, Any]] = None
    ) -> ConnectorResponse:
        """
        异步调用单个智能体
        
        Args:
            agent_id: 智能体ID或模板名称
            input_data: 输入数据，可以是文本字符串或结构化数据
            options: 可选参数，如温度、最大令牌数等
            auth_context: 认证上下文，包含用户身份和授权信息
            
        Returns:
            智能体执行结果
        """
        pass
    
    @abstractmethod
    async def stream_agent(
        self, 
        agent_id: str, 
        input_data: Union[str, Dict[str, Any]], 
        options: Optional[Dict[str, Any]] = None,
        auth_context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式调用单个智能体
        
        Args:
            agent_id: 智能体ID或模板名称
            input_data: 输入数据，可以是文本字符串或结构化数据
            options: 可选参数，如温度、最大令牌数等
            auth_context: 认证上下文，包含用户身份和授权信息
            
        Yields:
            智能体执行的各个事件和内容片段
        """
        pass
        
    @abstractmethod
    def invoke_workflow(
        self, 
        workflow_id: str, 
        input_data: Union[str, Dict[str, Any]], 
        options: Optional[Dict[str, Any]] = None,
        auth_context: Optional[Dict[str, Any]] = None
    ) -> ConnectorResponse:
        """
        同步调用多智能体协作工作流
        
        Args:
            workflow_id: 工作流ID或名称
            input_data: 输入数据，可以是文本字符串或结构化数据
            options: 可选参数，如工作流配置等
            auth_context: 认证上下文，包含用户身份和授权信息
            
        Returns:
            工作流执行结果
        """
        pass
    
    @abstractmethod
    async def ainvoke_workflow(
        self, 
        workflow_id: str, 
        input_data: Union[str, Dict[str, Any]], 
        options: Optional[Dict[str, Any]] = None,
        auth_context: Optional[Dict[str, Any]] = None
    ) -> ConnectorResponse:
        """
        异步调用多智能体协作工作流
        
        Args:
            workflow_id: 工作流ID或名称
            input_data: 输入数据，可以是文本字符串或结构化数据
            options: 可选参数，如工作流配置等
            auth_context: 认证上下文，包含用户身份和授权信息
            
        Returns:
            工作流执行结果
        """
        pass
        
    @abstractmethod
    async def stream_workflow(
        self, 
        workflow_id: str, 
        input_data: Union[str, Dict[str, Any]], 
        options: Optional[Dict[str, Any]] = None,
        auth_context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式调用多智能体协作工作流
        
        Args:
            workflow_id: 工作流ID或名称
            input_data: 输入数据，可以是文本字符串或结构化数据
            options: 可选参数，如工作流配置等
            auth_context: 认证上下文，包含用户身份和授权信息
            
        Yields:
            工作流执行的各个事件和内容片段
        """
        pass
    
    @abstractmethod
    def get_status(self, execution_id: str) -> Dict[str, Any]:
        """
        获取特定执行的状态
        
        Args:
            execution_id: 执行ID
            
        Returns:
            执行状态信息
        """
        pass
    
    @abstractmethod
    def register_callback(self, execution_id: str, callback_url: str) -> bool:
        """
        注册回调，用于异步通知结果
        
        Args:
            execution_id: 执行ID
            callback_url: 回调URL
            
        Returns:
            注册是否成功
        """
        pass 