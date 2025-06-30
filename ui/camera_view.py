import cv2
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap

class CameraView(QWidget):
    """单个摄像头视图组件"""
    
    def __init__(self, camera_id, parent=None):
        super().__init__(parent)
        self.camera_id = camera_id
        self.recording = False
        
        self.layout = QVBoxLayout(self)
        
        # 摄像头标签
        self.title_label = QLabel(f"摄像头 #{camera_id}")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        # 视频显示区域
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(320, 240)
        self.video_label.setStyleSheet("background-color: black; border: 1px solid #CCCCCC;")
        
        # 状态标签
        self.status_label = QLabel("未连接")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.video_label)
        self.layout.addWidget(self.status_label)
        
        # 设置边框
        self.setStyleSheet("border: 2px solid #AAAAAA; border-radius: 5px; padding: 5px; background-color: #F0F0F0;")
    
    def update_frame(self, frame):
        h, w, c = frame.shape
        bytes_per_line = 3 * w
        
        # 将OpenCV的BGR转换为RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 转换为QImage和QPixmap
        q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        
        # 调整图像大小以适应标签
        pixmap = pixmap.scaled(self.video_label.width(), self.video_label.height(), 
                             Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # 显示图像
        self.video_label.setPixmap(pixmap)
        
        # 更新状态标签
        if self.recording:
            self.status_label.setText("正在录制")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.status_label.setText("已连接")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
    
    def set_recording(self, recording):
        self.recording = recording
        if recording:
            self.status_label.setText("正在录制")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.status_label.setText("已连接")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
    
    def set_error(self, error_msg):
        self.status_label.setText(error_msg)
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        # 清除视频显示
        self.video_label.clear()
        self.video_label.setText("无法连接")
        self.video_label.setStyleSheet("background-color: black; color: white; border: 1px solid #CCCCCC;")
