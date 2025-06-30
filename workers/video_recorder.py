import os
import datetime
import time
import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from utils.helpers import get_timestamp

class VideoRecorder(QThread):
    """用于在后台录制视频的线程类"""
    update_frame = pyqtSignal(np.ndarray, int)
    error = pyqtSignal(str, int)
    recording_finished = pyqtSignal(int, dict)  # 发出录制完成信号，包含摄像头ID和录制信息
    
    def __init__(self, camera_id, output_path, fps=30, subject_name="", parent=None):
        super().__init__(parent)
        self.camera_id = camera_id
        self.output_path = output_path
        self.subject_folder = ""  # 被测对象文件夹
        self.subject_name = subject_name  # 被测对象名称
        self.custom_fps = fps  # 自定义帧率
        self.running = False
        self.recording = False
        self.cap = None
        self.out = None
        self.record_duration = 0  # 录制时长(分钟)，0表示无限制
        self.start_time = None  # 开始录制的时间
        self.end_time = None  # 结束录制的时间
        self.frame_count = 0  # 录制的帧数
        self.output_filename = ""  # 输出文件名
    
    def run(self):
        self.running = True
        self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
        
        if not self.cap.isOpened():
            self.error.emit(f"无法打开摄像头 ID: {self.camera_id} 的视频帧", self.camera_id)
            self.running = False
            return
        
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 帧间隔时间（秒）
        frame_interval = 1.0 / self.custom_fps
        
        while self.running:
            loop_start_time = time.time()
            
            ret, frame = self.cap.read()
            if not ret:
                self.error.emit(f"无法读取摄像头 ID: {self.camera_id} 的视频帧", self.camera_id)
                break
            
            self.update_frame.emit(frame, self.camera_id)
            
            if self.recording and self.out is not None:
                self.out.write(frame)
                self.frame_count += 1
                
                if self.record_duration > 0 and self.start_time is not None:
                    elapsed = (datetime.datetime.now() - self.start_time).total_seconds()
                    if elapsed >= self.record_duration * 60:
                        self.stop_recording()

            # 控制帧率
            elapsed_time = time.time() - loop_start_time
            sleep_time = frame_interval - elapsed_time
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        if self.cap:
            self.cap.release()
        if self.out:
            self.out.release()
    
    def set_subject(self, subject_name):
        """设置被测对象名称及其文件夹"""
        self.subject_name = subject_name
        # 创建主输出目录下的被测对象子目录
        self.subject_folder = os.path.join(self.output_path, subject_name)
        if not os.path.exists(self.subject_folder):
            os.makedirs(self.subject_folder)
    
    def start_recording(self, duration=0, subject_name=""):
        if not self.cap or not self.cap.isOpened():
            return False
        
        # 设置被测对象
        if subject_name:
            self.set_subject(subject_name)
        
        # 确保存在被测对象文件夹
        if not self.subject_folder:
            return False
        
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 按照摄像头编号命名视频文件
        timestamp = get_timestamp()
        self.output_filename = f"camera_{self.camera_id}.avi"
        output_path = os.path.join(self.subject_folder, self.output_filename)
        
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.out = cv2.VideoWriter(output_path, fourcc, self.custom_fps, (width, height))
        
        self.recording = True
        self.start_time = datetime.datetime.now()
        self.record_duration = duration
        self.frame_count = 0  # 重置帧数计数
        return True
    
    def stop_recording(self):
        """停止录制并返回录制信息"""
        if not self.recording:
            return
            
        self.recording = False
        self.end_time = datetime.datetime.now()
        
        if self.out:
            self.out.release()
            self.out = None
        
        # 收集录制信息
        recording_info = {
            "camera_id": self.camera_id,
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "end_time": self.end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "duration_seconds": (self.end_time - self.start_time).total_seconds(),
            "frame_count": self.frame_count,
            "fps_setting": self.custom_fps,
            "filename": self.output_filename,
            "subject": self.subject_name
        }
        
        # 发出录制完成信号
        self.recording_finished.emit(self.camera_id, recording_info)
    
    def stop(self):
        self.running = False
        self.recording = False
        self.wait()
