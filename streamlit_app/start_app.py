#!/usr/bin/env python
"""
应用启动脚本

提供一个简单的方式来启动Streamlit应用
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def start_app():
    """启动Streamlit应用"""
    # 打印欢迎信息
    print("=" * 50)
    print("欢迎使用 SSS Agent Platform 企业连接器")
    print("=" * 50)
    
    # 获取当前脚本所在目录
    current_dir = Path(__file__).parent.absolute()
    
    # 安装依赖（如果需要）
    install_dependencies(current_dir)
    
    # 检查应用文件是否存在
    app_file = current_dir / "app.py"
    if not app_file.exists():
        print(f"错误: 应用文件不存在: {app_file}")
        sys.exit(1)

    # 启动应用
    print("\n正在启动应用...")
    
    try:
        # 使用subprocess启动Streamlit应用
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            str(app_file)
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        
        # 启动进程
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待进程启动
        time.sleep(2)
        
        # 如果进程仍在运行，则认为启动成功
        if process.poll() is None:
            print("\n应用已成功启动!")
            print("\n您可以在浏览器中访问以下地址:")
            print("http://localhost:8501")
            print("\n按 Ctrl+C 停止应用")
            
            # 持续输出应用日志
            while True:
                output = process.stdout.readline()
                if output:
                    print(output.strip())
                
                # 检查进程是否仍在运行
                if process.poll() is not None:
                    break
                
                time.sleep(0.1)
        else:
            # 如果进程已经退出，则输出错误信息
            stdout, stderr = process.communicate()
            print("\n应用启动失败!")
            if stdout:
                print("\nSTDOUT:")
                print(stdout)
            if stderr:
                print("\nSTDERR:")
                print(stderr)
    
    except KeyboardInterrupt:
        print("\n接收到中断信号，正在停止应用...")
        if 'process' in locals() and process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
        print("应用已停止")
    
    except Exception as e:
        print(f"\n启动应用时出错: {str(e)}")
        sys.exit(1)

def install_dependencies(current_dir):
    """安装依赖项
    
    Args:
        current_dir: 当前脚本所在目录
    """
    try:
        # 检查依赖文件是否存在
        requirements_file = current_dir / "requirements.txt"
        if not requirements_file.exists():
            print("依赖文件不存在，跳过安装步骤")
            return
        
        print("正在检查依赖项...")
        
        # 安装依赖
        print(f"安装依赖: {requirements_file}")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", 
            str(requirements_file)
        ])
        
        print("依赖项安装完成")
    
    except Exception as e:
        print(f"安装依赖项时出错: {str(e)}")
        print("请手动安装依赖: pip install -r requirements.txt")

if __name__ == "__main__":
    start_app() 