"""
网络工具模块 - 提供网络请求功能

包含用于发送网络请求的工具函数，支持各种HTTP方法。
"""
import logging
import json
import time
import random
from typing import Dict, Any, List, Optional, Union

# 配置日志
logger = logging.getLogger(__name__)


def http_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, str]] = None,
    data: Optional[Union[Dict[str, Any], str]] = None,
    timeout: int = 30,
    verify_ssl: bool = True
) -> Dict[str, Any]:
    """
    发送HTTP请求
    
    Args:
        url: 请求URL
        method: HTTP方法，如GET、POST、PUT、DELETE等
        headers: 请求头
        params: URL参数
        data: 请求体数据
        timeout: 超时时间（秒）
        verify_ssl: 是否验证SSL证书
    
    Returns:
        包含响应结果的字典
    """
    logger.info(f"HTTP请求: {method} {url}")
    
    # 模拟发送请求
    # 在实际应用中，这里应使用requests库发送真实请求
    
    try:
        # 模拟网络延迟
        delay = random.uniform(0.2, 1.5)
        time.sleep(delay)
        
        # 记录请求详情
        request_details = {
            "url": url,
            "method": method,
            "headers": headers or {},
            "params": params or {},
            "timeout": timeout,
            "verify_ssl": verify_ssl
        }
        
        if data:
            if isinstance(data, dict):
                request_details["data"] = data
            else:
                request_details["data"] = f"<string data of length {len(str(data))}>"
        
        # 模拟响应
        if "error" in url.lower() or method not in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"]:
            # 模拟错误响应
            return {
                "error": True,
                "message": f"请求失败: {'无效的HTTP方法' if method not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD'] else '服务器错误'}",
                "status_code": 400 if method not in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"] else 500,
                "request": request_details,
                "elapsed": delay
            }
        
        # 模拟不同的响应
        if "example.com" in url:
            response_data = {"message": "这是一个示例响应", "success": True}
        elif "api" in url and "weather" in url:
            response_data = {
                "location": "北京",
                "temperature": 23,
                "condition": "晴",
                "humidity": 45,
                "wind": "东北风3级"
            }
        elif "api" in url and "news" in url:
            response_data = {
                "articles": [
                    {"title": "模拟新闻标题1", "summary": "这是一条模拟新闻的摘要内容..."},
                    {"title": "模拟新闻标题2", "summary": "这是另一条模拟新闻的摘要内容..."}
                ],
                "count": 2
            }
        else:
            response_data = {"status": "ok", "timestamp": time.time()}
        
        # 返回模拟响应
        return {
            "error": False,
            "status_code": 200,
            "headers": {
                "Content-Type": "application/json",
                "Server": "MockServer/1.0",
                "Date": time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
            },
            "data": response_data,
            "request": request_details,
            "elapsed": delay
        }
        
    except Exception as e:
        logger.error(f"HTTP请求失败: {str(e)}")
        return {
            "error": True,
            "message": f"HTTP请求失败: {str(e)}",
            "request": {
                "url": url,
                "method": method
            }
        }


def download_file(url: str, output_path: str, timeout: int = 60) -> Dict[str, Any]:
    """
    下载文件
    
    Args:
        url: 下载URL
        output_path: 输出文件路径
        timeout: 超时时间（秒）
    
    Returns:
        包含下载结果的字典
    """
    logger.info(f"下载文件: {url} -> {output_path}")
    
    try:
        # 模拟下载延迟
        file_size = random.randint(1024, 10485760)  # 1KB到10MB
        delay = file_size / 1048576  # 模拟1MB/s的下载速度
        time.sleep(min(delay, 5))  # 限制最大延迟为5秒
        
        # 模拟文件创建
        with open(output_path, 'w') as f:
            f.write(f"MOCK_DOWNLOAD_CONTENT:{url}")
        
        return {
            "error": False,
            "message": "文件下载成功",
            "url": url,
            "output_path": output_path,
            "file_size": file_size,
            "download_time": delay,
            "speed": f"{file_size / delay / 1024:.2f} KB/s"
        }
        
    except Exception as e:
        logger.error(f"下载文件失败: {str(e)}")
        return {
            "error": True,
            "message": f"下载文件失败: {str(e)}",
            "url": url,
            "output_path": output_path
        }


def check_url(url: str, timeout: int = 10) -> Dict[str, Any]:
    """
    检查URL是否可访问
    
    Args:
        url: 要检查的URL
        timeout: 超时时间（秒）
    
    Returns:
        包含检查结果的字典
    """
    logger.info(f"检查URL: {url}")
    
    try:
        # 模拟检查
        time.sleep(random.uniform(0.1, 0.5))
        
        # 模拟不同结果
        if "error" in url.lower() or "invalid" in url.lower():
            return {
                "error": False,
                "accessible": False,
                "status_code": 404,
                "message": "URL不可访问",
                "url": url,
                "response_time": random.uniform(0.1, 0.5)
            }
        else:
            return {
                "error": False,
                "accessible": True,
                "status_code": 200,
                "message": "URL可访问",
                "url": url,
                "response_time": random.uniform(0.05, 0.2)
            }
            
    except Exception as e:
        logger.error(f"检查URL失败: {str(e)}")
        return {
            "error": True,
            "message": f"检查URL失败: {str(e)}",
            "url": url
        }


def ping(host: str, count: int = 4) -> Dict[str, Any]:
    """
    Ping主机
    
    Args:
        host: 主机名或IP地址
        count: ping次数
    
    Returns:
        包含ping结果的字典
    """
    logger.info(f"Ping主机: {host}, 次数: {count}")
    
    try:
        # 模拟ping结果
        results = []
        total_time = 0
        
        for i in range(count):
            # 模拟每次ping的延迟时间
            if "unreachable" in host.lower():
                # 模拟不可达的主机
                time_ms = None
                status = "超时"
            else:
                time_ms = random.uniform(20, 100)
                total_time += time_ms
                status = "成功"
            
            results.append({
                "sequence": i + 1,
                "time_ms": time_ms,
                "status": status
            })
            
            # 短暂延迟模拟ping间隔
            time.sleep(0.1)
        
        # 计算统计信息
        success_count = sum(1 for r in results if r["status"] == "成功")
        loss_rate = (count - success_count) / count * 100
        
        if success_count > 0:
            avg_time = total_time / success_count
            min_time = min(r["time_ms"] for r in results if r["time_ms"] is not None)
            max_time = max(r["time_ms"] for r in results if r["time_ms"] is not None)
        else:
            avg_time = min_time = max_time = None
        
        return {
            "error": False,
            "host": host,
            "count": count,
            "success_count": success_count,
            "loss_rate": loss_rate,
            "min_time": min_time,
            "avg_time": avg_time,
            "max_time": max_time,
            "results": results
        }
            
    except Exception as e:
        logger.error(f"Ping失败: {str(e)}")
        return {
            "error": True,
            "message": f"Ping失败: {str(e)}",
            "host": host
        } 