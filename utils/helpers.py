import sys
import os
import datetime
import matplotlib
from matplotlib.font_manager import fontManager
from PyQt5.QtWidgets import QMessageBox

# 添加北京时间转换功能
def get_beijing_time():
    """获取格式化的北京时间"""
    # 北京时间是UTC+8
    utc_now = datetime.datetime.utcnow()
    beijing_now = utc_now + datetime.timedelta(hours=8)
    return beijing_now.strftime("%Y-%m-%d %H:%M:%S")

# 添加时间戳函数，用于日志和文件名
def get_timestamp():
    """获取当前时间戳，格式为：年月日_时分秒"""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# 新增：用于获取打包后资源的路径
def resource_path(relative_path):
    """ 获取资源的绝对路径，兼容开发环境和PyInstaller环境 """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller创建的临时文件夹
        base_path = sys._MEIPASS
    else:
        # 普通的开发环境
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# 重写：配置中文字体
def setup_chinese_fonts():
    """配置matplotlib以使用打包的中文字体"""
    font_path = resource_path(os.path.join('resources', 'simhei.ttf'))
    
    if not os.path.exists(font_path):
        print(f"错误: 字体文件未找到 at {font_path}")
        # 在GUI应用中，使用QMessageBox提示错误可能更友好
        # 但由于这个helper可能在非GUI线程中使用，暂时只打印
        return False
        
    try:
        fontManager.addfont(font_path)
        matplotlib.rcParams['font.sans-serif'] = ['SimHei'] + matplotlib.rcParams['font.sans-serif']
        matplotlib.rcParams['axes.unicode_minus'] = False
        matplotlib.rcParams['font.family'] = 'sans-serif'
        print("中文字体 'SimHei' 配置成功。")
        return True
    except Exception as e:
        print(f"配置中文字体时发生错误: {e}")
        return False
