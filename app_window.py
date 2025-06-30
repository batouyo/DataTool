import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QTabWidget, QMessageBox)
from PyQt5.QtCore import QTimer, Qt

from utils.helpers import get_beijing_time, get_timestamp
from ui.camera_tab import CameraTab
from ui.oximeter_tab import OximeterTab

class MultiCameraRecorder(QMainWindow):
    """多功能生理数据采集工具主窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("多功能生理数据采集工具")
        self.setMinimumSize(1200, 800)
        
        # 中心组件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 创建北京时间显示区域
        self.create_time_display()
        
        # 创建选项卡Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { 
                border: 1px solid #CCCCCC; 
                border-radius: 4px;
                padding: 5px;
                background-color: #F8F8F8;
            }
            QTabBar::tab {
                background-color: #E0E0E0;
                padding: 8px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
        """)
        
        # 添加摄像头录制选项卡
        self.camera_tab = CameraTab()
        self.tab_widget.addTab(self.camera_tab, "多摄像头录制")
        
        # 添加血氧仪分析选项卡
        self.oximeter_tab = OximeterTab()
        self.tab_widget.addTab(self.oximeter_tab, "血氧仪数据分析")
        
        # 将选项卡Widget添加到主布局
        self.main_layout.addWidget(self.tab_widget)
        
        # 设置应用样式
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                padding: 5px;
                border-radius: 3px;
            }
            QLabel {
                padding: 2px;
            }
            QComboBox, QSpinBox {
                padding: 3px;
                border: 1px solid #AAAAAA;
                border-radius: 2px;
            }
        """)
        
        # 启动定时器，更新北京时间
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.update_beijing_time)
        self.time_timer.start(1000)
        self.update_beijing_time()
    
    def create_time_display(self):
        """创建北京时间显示区域"""
        time_widget = QWidget()
        time_layout = QVBoxLayout(time_widget)
        
        time_title = QLabel("北京时间")
        time_title.setAlignment(Qt.AlignCenter)
        time_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #003366;
            background-color: #E6F0FF;
            border: 1px solid #9999CC;
            border-radius: 4px;
            padding: 5px 15px;
        """)
        self.time_label.setMinimumWidth(250)
        
        time_layout.addWidget(time_title)
        time_layout.addWidget(self.time_label)
        
        time_container = QHBoxLayout()
        time_container.addStretch(1)
        time_container.addWidget(time_widget)
        time_container.addStretch(1)
        
        self.main_layout.addLayout(time_container)
    
    def update_beijing_time(self):
        """更新北京时间显示"""
        beijing_time = get_beijing_time()
        self.time_label.setText(beijing_time)
    
    def closeEvent(self, event):
        """关闭窗口时清理资源"""
        if self.time_timer.isActive():
            self.time_timer.stop()
        
        # 调用CameraTab的清理方法
        self.camera_tab.cleanup()
        
        super().closeEvent(event)
