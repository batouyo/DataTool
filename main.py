import sys
import matplotlib
from PyQt5.QtWidgets import QApplication

# 从新模块导入
from app_window import MultiCameraRecorder
from utils.helpers import setup_chinese_fonts

def main():
    """主函数，用于启动应用程序"""
    # 尝试设置中文字体
    if not setup_chinese_fonts():
        # 如果设置失败，使用备选方案
        matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
        matplotlib.rcParams['axes.unicode_minus'] = False
        matplotlib.rcParams['font.family'] = 'sans-serif'
    
    # 启动Qt应用
    app = QApplication(sys.argv)
    window = MultiCameraRecorder()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
