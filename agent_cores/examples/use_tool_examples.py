"""
工具使用示例 - 演示各种工具的用法

本脚本展示了如何使用平台提供的各种工具，包括文件、音频和网络工具。
"""
import os
import logging
import asyncio
import json
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入工具
from agent_cores.tools import (
    FileManager,
    text_to_speech,
    speech_to_text,
    audio_info,
    http_request,
    download_file,
    check_url,
    ping
)


async def demo_file_tools():
    """演示文件操作工具的使用"""
    logger.info("===== 开始演示文件工具 =====")
    
    # 创建文件管理器实例
    file_manager = FileManager()
    
    # 列出文件
    logger.info("列出文件示例:")
    files_result = file_manager.list_files()
    logger.info(f"文件列表: {json.dumps(files_result, ensure_ascii=False, indent=2)}")
    
    # 写入文件
    test_content = "这是一个测试文件内容\n包含多行文本\n用于演示文件工具的使用。"
    write_result = file_manager.write_file("test_file.txt", test_content)
    logger.info(f"写入文件结果: {json.dumps(write_result, ensure_ascii=False, indent=2)}")
    
    # 读取文件
    read_result = file_manager.read_file("test_file.txt")
    logger.info(f"读取文件结果: {json.dumps(read_result, ensure_ascii=False, indent=2)}")
    
    logger.info("===== 文件工具演示结束 =====\n")


async def demo_audio_tools():
    """演示音频处理工具的使用"""
    logger.info("===== 开始演示音频工具 =====")
    
    # 文本转语音
    tts_result = text_to_speech("这是一个测试语音合成的示例文本，用于演示文本到语音的转换功能。")
    logger.info(f"文本转语音结果: {json.dumps(tts_result, ensure_ascii=False, indent=2)}")
    
    # 获取生成的音频文件
    audio_file = tts_result.get("file_path")
    
    # 获取音频信息
    if audio_file:
        info_result = audio_info(audio_file)
        logger.info(f"音频信息结果: {json.dumps(info_result, ensure_ascii=False, indent=2)}")
    
        # 语音转文本
        stt_result = speech_to_text(audio_file)
        logger.info(f"语音转文本结果: {json.dumps(stt_result, ensure_ascii=False, indent=2)}")
    
    logger.info("===== 音频工具演示结束 =====\n")


async def demo_network_tools():
    """演示网络工具的使用"""
    logger.info("===== 开始演示网络工具 =====")
    
    # HTTP请求
    http_result = http_request(
        url="https://api.example.com/weather",
        method="GET",
        params={"city": "北京"}
    )
    logger.info(f"HTTP请求结果: {json.dumps(http_result, ensure_ascii=False, indent=2)}")
    
    # 检查URL
    check_result = check_url("https://example.com")
    logger.info(f"URL检查结果: {json.dumps(check_result, ensure_ascii=False, indent=2)}")
    
    # 执行Ping
    ping_result = ping("example.com")
    logger.info(f"Ping结果: {json.dumps(ping_result, ensure_ascii=False, indent=2)}")
    
    # 下载文件
    workspace_dir = os.path.join(Path(__file__).parent.parent.parent, "workspace")
    os.makedirs(workspace_dir, exist_ok=True)
    output_path = os.path.join(workspace_dir, "downloaded_file.txt")
    
    download_result = download_file(
        url="https://example.com/sample.txt",
        output_path=output_path
    )
    logger.info(f"文件下载结果: {json.dumps(download_result, ensure_ascii=False, indent=2)}")
    
    logger.info("===== 网络工具演示结束 =====\n")


async def demo_combined_tools():
    """演示工具组合使用的场景"""
    logger.info("===== 开始演示工具组合使用 =====")
    
    # 场景：从网络获取数据并保存到文件
    file_manager = FileManager()
    
    # 1. 获取网络数据
    logger.info("1. 从网络获取数据...")
    http_result = http_request(
        url="https://api.example.com/news",
        method="GET"
    )
    
    if not http_result.get("error", True):
        data = http_result.get("data", {})
        
        # 2. 将数据保存到文件
        logger.info("2. 将数据保存到文件...")
        json_content = json.dumps(data, ensure_ascii=False, indent=2)
        write_result = file_manager.write_file("news_data.json", json_content)
        
        # 3. 读取文件内容并转换为语音
        if not write_result.get("error", True):
            logger.info("3. 将内容转换为语音...")
            file_path = write_result.get("file_path")
            read_result = file_manager.read_file(file_path)
            
            if not read_result.get("error", True):
                content = read_result.get("content", "")
                
                # 提取文章标题
                try:
                    news_data = json.loads(content)
                    articles = news_data.get("articles", [])
                    
                    if articles:
                        title = articles[0].get("title", "无标题")
                        summary = articles[0].get("summary", "无内容")
                        
                        # 4. 转换为语音
                        speech_text = f"最新新闻: {title}。{summary}"
                        tts_result = text_to_speech(speech_text)
                        
                        logger.info(f"已生成语音文件: {tts_result.get('file_path')}")
                except Exception as e:
                    logger.error(f"处理新闻数据失败: {str(e)}")
    
    logger.info("===== 工具组合使用演示结束 =====\n")


async def main():
    """主函数"""
    logger.info("开始工具使用示例演示")
    
    # 演示文件工具
    await demo_file_tools()
    
    # 演示音频工具
    await demo_audio_tools()
    
    # 演示网络工具
    await demo_network_tools()
    
    # 演示工具组合使用
    await demo_combined_tools()
    
    logger.info("工具使用示例演示完成")


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main()) 