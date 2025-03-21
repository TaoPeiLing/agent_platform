"""
Logo生成工具

为应用程序创建一个简单的Logo图片，如果不存在的话
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys

def create_simple_logo(width=200, height=200, save_path=None):
    """
    创建一个简单的Logo图片
    
    Args:
        width: 图片宽度
        height: 图片高度
        save_path: 保存路径，如果为None，则保存到默认位置
    
    Returns:
        保存的文件路径
    """
    # 确定保存路径
    if save_path is None:
        # 获取当前脚本所在目录
        current_dir = Path(__file__).parent.absolute()
        # 获取项目根目录
        root_dir = current_dir.parent
        # 确保images目录存在
        images_dir = root_dir / "images"
        images_dir.mkdir(exist_ok=True)
        # 设置保存路径
        save_path = images_dir / "logo.png"
    
    # 检查文件是否已存在
    if os.path.exists(save_path):
        print(f"Logo已存在: {save_path}")
        return save_path
    
    # 创建一个空白图片，使用RGBA模式支持透明背景
    image = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    
    # 绘制圆形背景
    circle_color = (0, 120, 212, 230)  # 蓝色，带有透明度
    draw.ellipse((10, 10, width-10, height-10), fill=circle_color)
    
    # 尝试加载字体
    try:
        # 尝试使用Arial字体
        font = ImageFont.truetype("arial.ttf", size=36)
    except IOError:
        try:
            # 尝试使用系统默认字体
            font = ImageFont.truetype(size=36)
        except IOError:
            # 如果无法加载任何TrueType字体，使用默认字体
            font = ImageFont.load_default()
    
    # 添加文字
    text = "SSS"
    text_color = (255, 255, 255, 255)  # 白色
    
    # 获取文字大小
    try:
        text_width, text_height = draw.textsize(text, font=font)
    except:
        # Pillow新版本兼容
        text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:4]
    
    # 计算文字位置，使其居中
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2
    
    # 绘制文字
    draw.text((text_x, text_y), text, font=font, fill=text_color)
    
    # 保存图片
    try:
        image.save(save_path)
        print(f"Logo已创建并保存到: {save_path}")
    except Exception as e:
        print(f"保存Logo时出错: {str(e)}")
    
    return save_path

if __name__ == "__main__":
    # 当直接运行此脚本时，创建Logo
    create_simple_logo()
    print("Logo生成完成") 