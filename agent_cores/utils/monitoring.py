"""
监控模块 - 提供基本的监控和指标收集功能
"""
import time
import logging
import functools
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
import threading
from contextlib import contextmanager

try:
    # 尝试导入普罗米修斯客户端库（可选依赖）
    import prometheus_client
    from prometheus_client import Counter, Gauge, Histogram, Summary
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    
try:
    # 尝试导入OpenAI跟踪功能（可选依赖）
    import openai
    from openai.types.beta.trace import Trace, RunTrace
    OPENAI_TRACING_AVAILABLE = True
except (ImportError, AttributeError):
    OPENAI_TRACING_AVAILABLE = False

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class MetricsCollector:
    """简单的指标收集器"""
    app_name: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    
    def __post_init__(self):
        """初始化指标"""
        if PROMETHEUS_AVAILABLE:
            # 初始化标准指标
            self.metrics["api_requests_total"] = Counter(
                f"{self.app_name}_api_requests_total",
                "API请求总数",
                ["method", "endpoint", "status"]
            )
            
            self.metrics["request_duration_seconds"] = Histogram(
                f"{self.app_name}_request_duration_seconds",
                "请求处理时间（秒）",
                ["method", "endpoint"]
            )
            
            self.metrics["active_connections"] = Gauge(
                f"{self.app_name}_active_connections",
                "活跃连接数"
            )
            
            self.metrics["agent_runs_total"] = Counter(
                f"{self.app_name}_agent_runs_total",
                "代理运行总数",
                ["agent_type", "status"]
            )
            
            self.metrics["agent_execution_time"] = Histogram(
                f"{self.app_name}_agent_execution_time",
                "代理执行时间（秒）",
                ["agent_type"]
            )
            
            self.metrics["tool_calls_total"] = Counter(
                f"{self.app_name}_tool_calls_total",
                "工具调用总数",
                ["tool_name", "status"]
            )
            
            logger.info("普罗米修斯指标已初始化")
        else:
            logger.warning("普罗米修斯客户端库未安装，指标收集已禁用")
    
    def track_request(self, method: str, endpoint: str, status: int, duration: float):
        """
        记录API请求
        
        Args:
            method: HTTP方法
            endpoint: 端点
            status: 状态码
            duration: 处理时间（秒）
        """
        if not PROMETHEUS_AVAILABLE:
            return
            
        with self._lock:
            self.metrics["api_requests_total"].labels(method, endpoint, status).inc()
            self.metrics["request_duration_seconds"].labels(method, endpoint).observe(duration)
    
    def track_agent_run(self, agent_type: str, status: str, duration: float):
        """
        记录代理运行
        
        Args:
            agent_type: 代理类型
            status: 状态（success/failure）
            duration: 执行时间（秒）
        """
        if not PROMETHEUS_AVAILABLE:
            return
            
        with self._lock:
            self.metrics["agent_runs_total"].labels(agent_type, status).inc()
            self.metrics["agent_execution_time"].labels(agent_type).observe(duration)
    
    def track_tool_call(self, tool_name: str, status: str):
        """
        记录工具调用
        
        Args:
            tool_name: 工具名称
            status: 状态（success/failure）
        """
        if not PROMETHEUS_AVAILABLE:
            return
            
        with self._lock:
            self.metrics["tool_calls_total"].labels(tool_name, status).inc()
    
    def start_http_server(self, port: int = 8001):
        """
        启动普罗米修斯指标HTTP服务器
        
        Args:
            port: 端口号
        """
        if PROMETHEUS_AVAILABLE:
            prometheus_client.start_http_server(port)
            logger.info(f"普罗米修斯指标服务器已启动，端口：{port}")
        else:
            logger.warning("普罗米修斯客户端库未安装，无法启动指标服务器")


@contextmanager
def measure_time():
    """测量代码块执行时间的上下文管理器"""
    start_time = time.time()
    try:
        yield start_time
    finally:
        duration = time.time() - start_time


class OpenAITracer:
    """OpenAI API跟踪器"""
    
    def __init__(self, enabled: bool = True):
        """
        初始化OpenAI跟踪器
        
        Args:
            enabled: 是否启用跟踪
        """
        self.enabled = enabled and OPENAI_TRACING_AVAILABLE
        self.client = None
        
        if self.enabled:
            try:
                # 配置OpenAI客户端，启用跟踪
                self.client = openai.OpenAI()
                logger.info("OpenAI跟踪已启用")
            except Exception as e:
                logger.error(f"OpenAI跟踪初始化失败: {e}")
                self.enabled = False
        
    def start_trace(self, name: str) -> Optional[Any]:
        """
        开始一个新的跟踪
        
        Args:
            name: 跟踪名称
            
        Returns:
            跟踪对象
        """
        if not self.enabled:
            return None
            
        try:
            # 创建新的跟踪
            return self.client.beta.traces.create(name=name)
        except Exception as e:
            logger.error(f"创建跟踪失败: {e}")
            return None
    
    def add_event(self, trace_id: str, event_type: str, data: Dict[str, Any]):
        """
        添加跟踪事件
        
        Args:
            trace_id: 跟踪ID
            event_type: 事件类型
            data: 事件数据
        """
        if not self.enabled or not trace_id:
            return
            
        try:
            # 添加事件（这是一个假设的API，实际实现可能不同）
            pass
        except Exception as e:
            logger.error(f"添加跟踪事件失败: {e}")


# 创建全局实例
metrics = MetricsCollector(app_name="sss_agent_platform")
tracer = OpenAITracer()


# 装饰器：测量函数执行时间
def measure_execution_time(func=None, *, name=None):
    """
    测量函数执行时间的装饰器
    
    Args:
        func: 被装饰的函数
        name: 自定义指标名称
    """
    def decorator(f):
        metric_name = name or f.__name__
        
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            with measure_time() as start_time:
                try:
                    result = f(*args, **kwargs)
                    metrics.track_agent_run(metric_name, "success", time.time() - start_time)
                    return result
                except Exception as e:
                    metrics.track_agent_run(metric_name, "failure", time.time() - start_time)
                    raise
        
        return wrapper
    
    if func is not None:
        return decorator(func)
    return decorator


# 示例用法
if __name__ == "__main__":
    # 启动指标服务器
    metrics.start_http_server(8001)
    
    # 测试指标收集
    metrics.track_request("GET", "/api/v1/agents", 200, 0.1)
    metrics.track_agent_run("assistant", "success", 1.5)
    metrics.track_tool_call("search_web", "success")
    
    # 测试装饰器
    @measure_execution_time
    def test_function():
        time.sleep(1)
        return "测试成功"
    
    test_function()
    print("监控测试完成") 