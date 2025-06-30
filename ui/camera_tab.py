import os
import re
import json
import cv2
import numpy as np

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
                           QLabel, QPushButton, QComboBox, QLineEdit, QFileDialog,
                           QMessageBox, QSpinBox, QInputDialog, QCheckBox, QApplication)
from PyQt5.QtCore import Qt, pyqtSlot

from ui.camera_view import CameraView
from workers.video_recorder import VideoRecorder
from services.data_sync_manager import DataSyncManager
from utils.helpers import get_timestamp

class CameraTab(QWidget):
    """多摄像头录制选项卡"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化变量
        self.camera_views = {}
        self.camera_recorders = {}
        self.is_recording = False
        self.current_subject = ""
        self.recording_logs = {}
        
        # 创建数据同步管理器
        self.data_sync_manager = DataSyncManager()

        self.setup_ui()
        
        # 确保输出目录存在
        output_dir = self.output_dir_edit.text()
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def setup_ui(self):
        """设置UI"""
        camera_layout = QVBoxLayout(self)
        
        # 控制区域
        self.control_group = QGroupBox("控制面板")
        self.control_layout = QVBoxLayout(self.control_group)
        
        # 摄像头控制部分
        self.camera_control_layout = QHBoxLayout()
        
        # 摄像头选择
        self.camera_combo = QComboBox()
        self.camera_combo.addItem("选择摄像头...")
        self.camera_combo.setMinimumWidth(150)
        
        self.scan_button = QPushButton("扫描摄像头设备")
        self.scan_button.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.scan_button.clicked.connect(self.refresh_cameras)
        
        self.add_camera_button = QPushButton("添加摄像头")
        self.add_camera_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.add_camera_button.clicked.connect(self.add_camera)
        
        self.camera_control_layout.addWidget(QLabel("摄像头:"))
        self.camera_control_layout.addWidget(self.camera_combo)
        self.camera_control_layout.addWidget(self.scan_button)
        self.camera_control_layout.addWidget(self.add_camera_button)
        self.camera_control_layout.addStretch(1)
        
        # 输出目录选择
        self.output_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("选择输出目录...")
        self.output_dir_edit.setText(os.path.join(os.getcwd(), "recordings"))
        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self.browse_output_dir)
        
        self.output_layout.addWidget(QLabel("输出目录:"))
        self.output_layout.addWidget(self.output_dir_edit)
        self.output_layout.addWidget(self.browse_button)
        
        # 数据同步配置部分
        self.sync_layout = QHBoxLayout()
        
        # 同步开关
        self.sync_checkbox = QCheckBox("启用生理数据同步")
        self.sync_checkbox.setChecked(False)
        self.sync_checkbox.stateChanged.connect(self.toggle_sync_options)
        
        # 数据文件选择
        self.data_file_edit = QLineEdit()
        self.data_file_edit.setPlaceholderText("选择生理数据文件...")
        self.data_file_edit.setEnabled(False)
        
        self.browse_data_button = QPushButton("浏览...")
        self.browse_data_button.clicked.connect(self.browse_data_file)
        self.browse_data_button.setEnabled(False)
        
        self.sync_layout.addWidget(self.sync_checkbox)
        self.sync_layout.addWidget(QLabel("数据文件:"))
        self.sync_layout.addWidget(self.data_file_edit, 1)
        self.sync_layout.addWidget(self.browse_data_button)
        
        # 当前对象显示
        self.subject_layout = QHBoxLayout()
        self.subject_layout.addWidget(QLabel("当前对象:"))
        self.subject_label = QLabel("未设置")
        self.subject_label.setStyleSheet("font-weight: bold; color: #006699; padding: 2px 5px; background-color: #F0F0F0; border: 1px solid #CCCCCC; border-radius: 3px;")
        self.subject_layout.addWidget(self.subject_label)
        self.subject_layout.addStretch(1)
        
        # 录制参数设置
        self.record_params_layout = QHBoxLayout()
        
        # 录制时长设置
        self.duration_layout = QHBoxLayout()
        self.duration_layout.addWidget(QLabel("录制时长(分钟):"))
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(0, 1440)
        self.duration_spinbox.setValue(10)
        self.duration_spinbox.setSpecialValueText("无限制")
        self.duration_spinbox.setToolTip("设置录制时长，0表示无限制")
        self.duration_layout.addWidget(self.duration_spinbox)
        
        # 帧率选择
        self.fps_layout = QHBoxLayout()
        self.fps_layout.addWidget(QLabel("视频帧率:"))
        self.fps_combo = QComboBox()
        self.fps_combo.addItem("30 FPS", 30)
        self.fps_combo.addItem("60 FPS", 60)
        self.fps_layout.addWidget(self.fps_combo)
        
        self.record_params_layout.addLayout(self.duration_layout)
        self.record_params_layout.addSpacing(20)
        self.record_params_layout.addLayout(self.fps_layout)
        self.record_params_layout.addStretch(1)
        
        # 录制控制
        self.record_layout = QHBoxLayout()
        self.record_button = QPushButton("开始录制")
        self.record_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.record_button.setMinimumWidth(150)
        self.record_button.clicked.connect(self.start_recording)
        
        self.stop_button = QPushButton("停止录制")
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("background-color: #F44336; color: white; font-weight: bold; padding: 8px;")
        self.stop_button.setMinimumWidth(150)
        self.stop_button.clicked.connect(self.stop_recording)
        
        self.record_layout.addStretch(1)
        self.record_layout.addWidget(self.record_button)
        self.record_layout.addWidget(self.stop_button)
        self.record_layout.addStretch(1)
        
        # 添加所有控制布局到控制面板
        self.control_layout.addLayout(self.camera_control_layout)
        self.control_layout.addLayout(self.output_layout)
        self.control_layout.addLayout(self.sync_layout)
        self.control_layout.addLayout(self.subject_layout)
        self.control_layout.addLayout(self.record_params_layout)
        self.control_layout.addLayout(self.record_layout)
        
        # 预览区域标题
        self.preview_label = QLabel("摄像头预览区域")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px; margin-bottom: 10px;")
        
        # 摄像头预览区域容器
        self.preview_container = QWidget()
        self.grid_layout = QGridLayout(self.preview_container)
        self.grid_layout.setSpacing(10)
        
        # 预览区域初始提示
        self.no_camera_label = QLabel("请点击\"扫描摄像头设备\"按钮，然后添加摄像头到预览区域")
        self.no_camera_label.setAlignment(Qt.AlignCenter)
        self.no_camera_label.setStyleSheet("font-size: 14px; color: #666666; padding: 50px;")
        self.grid_layout.addWidget(self.no_camera_label, 0, 0)
        
        # 添加所有组件到摄像头选项卡
        camera_layout.addWidget(self.control_group)
        camera_layout.addWidget(self.preview_label)
        camera_layout.addWidget(self.preview_container, 1)

    def refresh_cameras(self):
        """刷新可用摄像头列表"""
        self.camera_combo.clear()
        self.camera_combo.addItem("选择摄像头...")
        
        self.scan_button.setText("正在扫描...")
        self.scan_button.setEnabled(False)
        QApplication.processEvents()
        
        found_cameras = 0
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                found_cameras += 1
                cap.release()
                self.camera_combo.addItem(f"摄像头 #{i}")
        
        self.scan_button.setText("扫描摄像头设备")
        self.scan_button.setEnabled(True)
        
        if found_cameras == 0:
            QMessageBox.information(self, "提示", "未找到可用的摄像头设备")
        else:
            QMessageBox.information(self, "提示", f"找到 {found_cameras} 个摄像头设备")

    def add_camera(self):
        """添加选定的摄像头到界面"""
        camera_text = self.camera_combo.currentText()
        if camera_text == "选择摄像头...":
            QMessageBox.warning(self, "警告", "请先选择一个摄像头")
            return
        
        camera_id = int(camera_text.split("#")[1])
        if camera_id in self.camera_views:
            QMessageBox.information(self, "提示", f"摄像头 #{camera_id} 已添加")
            return
        
        if not self.camera_views:
            item = self.grid_layout.itemAt(0)
            if item is not None and item.widget() is self.no_camera_label:
                self.grid_layout.removeWidget(self.no_camera_label)
                self.no_camera_label.hide()
        
        num_cameras = len(self.camera_views)
        row = num_cameras // 2
        col = num_cameras % 2
        
        camera_view = CameraView(camera_id)
        self.camera_views[camera_id] = camera_view
        self.grid_layout.addWidget(camera_view, row, col)
        
        fps = self.fps_combo.currentData()
        output_dir = self.output_dir_edit.text()
        
        recorder = VideoRecorder(camera_id, output_dir, fps=fps)
        recorder.update_frame.connect(self.update_camera_frame)
        recorder.error.connect(self.handle_camera_error)
        recorder.recording_finished.connect(self.handle_recording_finished)
        
        self.camera_recorders[camera_id] = recorder
        recorder.start()

    @pyqtSlot(np.ndarray, int)
    def update_camera_frame(self, frame, camera_id):
        """更新摄像头视图的帧"""
        if camera_id in self.camera_views:
            self.camera_views[camera_id].update_frame(frame)
    
    @pyqtSlot(str, int)
    def handle_camera_error(self, error_msg, camera_id):
        """处理摄像头错误"""
        if camera_id in self.camera_views:
            self.camera_views[camera_id].set_error(error_msg)
    
    @pyqtSlot(int, dict)
    def handle_recording_finished(self, camera_id, recording_info):
        """处理录制完成信号"""
        if camera_id not in self.recording_logs:
            self.recording_logs[camera_id] = []
        self.recording_logs[camera_id].append(recording_info)
        
        all_stopped = all(not r.recording for r in self.camera_recorders.values())
                
        if all_stopped and self.is_recording:
            self.write_recording_logs()
            
            self.is_recording = False
            self.record_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            
            if self.data_sync_manager.is_monitoring:
                self.data_sync_manager.stop_monitoring()
                output_dir = self.output_dir_edit.text()
                subject_dir = os.path.join(output_dir, self.current_subject)
                sync_file = os.path.join(subject_dir, "sync_data.json")
                if self.data_sync_manager.sync_records and self.data_sync_manager.save_sync_data(sync_file):
                    print(f"同步数据已保存至: {sync_file}")
            
            QMessageBox.information(self, "录制完成", f"所有摄像头录制已完成，视频和日志已保存至: {os.path.join(self.output_dir_edit.text(), self.current_subject)}")

    def browse_output_dir(self):
        """选择输出目录"""
        output_dir = QFileDialog.getExistingDirectory(self, "选择输出目录", self.output_dir_edit.text())
        if output_dir:
            self.output_dir_edit.setText(output_dir)
            for recorder in self.camera_recorders.values():
                recorder.output_path = output_dir
    
    def ask_subject_name(self):
        """询问用户输入被测对象名称"""
        subject_name, ok = QInputDialog.getText(self, "输入对象名称", "请为本次录制的对象命名：", QLineEdit.Normal)
        if not ok or not subject_name.strip():
            return ""
        if re.search(r'[\\/:*?"<>|]', subject_name):
            QMessageBox.warning(self, "警告", "对象名称不能包含以下字符: \\ / : * ? \" < > |")
            return self.ask_subject_name()
        return subject_name.strip()
    
    def start_recording(self):
        """开始所有摄像头的录制"""
        if not self.camera_recorders:
            QMessageBox.warning(self, "警告", "请先添加至少一个摄像头")
            return
        
        subject_name = self.ask_subject_name()
        if not subject_name:
            return
        
        self.current_subject = subject_name
        self.subject_label.setText(subject_name)
        
        output_dir = self.output_dir_edit.text()
        try:
            os.makedirs(os.path.join(output_dir, subject_name), exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法创建对象目录: {str(e)}")
            return
        
        self.recording_logs = {}
        duration = self.duration_spinbox.value()
        fps = self.fps_combo.currentData()
        
        self.data_sync_manager.reset()
        for camera_id, recorder in self.camera_recorders.items():
            recorder.custom_fps = fps
            if recorder.start_recording(duration=duration, subject_name=subject_name):
                self.camera_views[camera_id].set_recording(True)
                self.data_sync_manager.add_recorder(camera_id, recorder)
        
        self.is_recording = True
        self.record_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        if self.sync_checkbox.isChecked() and self.data_file_edit.text():
            if not self.data_sync_manager.start_monitoring():
                QMessageBox.warning(self, "同步警告", "无法启动数据文件监控。录制将继续，但不会记录同步信息。")
        
        if duration > 0:
            QMessageBox.information(self, "录制已开始", f"录制开始，对象：{subject_name}，录制时长：{duration}分钟。")
    
    def stop_recording(self):
        """停止所有摄像头的录制"""
        for recorder in self.camera_recorders.values():
            if recorder.recording:
                recorder.stop_recording()
                self.camera_views[recorder.camera_id].set_recording(False)
                self.data_sync_manager.remove_recorder(recorder.camera_id)
        
        if self.data_sync_manager.is_monitoring:
            self.data_sync_manager.stop_monitoring()
            if self.data_sync_manager.sync_records and self.is_recording:
                reply = QMessageBox.question(self, "保存同步数据", "有未保存的同步记录数据。是否保存？", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    subject_dir = os.path.join(self.output_dir_edit.text(), self.current_subject or f"未命名_{get_timestamp()}")
                    os.makedirs(subject_dir, exist_ok=True)
                    sync_file = os.path.join(subject_dir, "sync_data.json")
                    self.data_sync_manager.save_sync_data(sync_file)
    
    def write_recording_logs(self):
        """将录制信息写入日志文件"""
        if not self.recording_logs:
            return
        subject_dir = os.path.join(self.output_dir_edit.text(), self.current_subject)
        try:
            for camera_id, logs in self.recording_logs.items():
                if not logs: continue
                log_file = os.path.join(subject_dir, f"camera_{camera_id}_log.txt")
                with open(log_file, "w") as f:
                    log = logs[0]
                    f.write(f"摄像头 #{camera_id} 录制日志\n")
                    f.write(f"对象名称: {self.current_subject}\n")
                    f.write(f"录制时间: {log['start_time']} 至 {log['end_time']}\n")
                    f.write(f"总帧数: {log['frame_count']}\n")
                    f.write(f"设置帧率: {log['fps_setting']}\n")
                    f.write(f"实际时长(秒): {log['duration_seconds']:.3f}\n")
                    f.write(f"平均实际帧率: {log['frame_count']/max(log['duration_seconds'], 0.001):.2f}\n")
                    f.write(f"文件名: {log['filename']}\n")
            
            json_log_file = os.path.join(subject_dir, "recording_info.json")
            with open(json_log_file, "w") as f:
                json.dump(self.recording_logs, f, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"写入日志文件时出错: {str(e)}")

    def toggle_sync_options(self, state):
        """切换数据同步选项的启用状态"""
        enabled = state == Qt.Checked
        self.data_file_edit.setEnabled(enabled)
        self.browse_data_button.setEnabled(enabled)
        if not enabled and self.data_sync_manager.is_monitoring:
            self.data_sync_manager.stop_monitoring()
    
    def browse_data_file(self):
        """选择生理数据文件"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择生理数据文件", "", "文本文件 (*.txt);;所有文件 (*)")
        if file_path:
            self.data_file_edit.setText(file_path)
            self.data_sync_manager.set_data_path(file_path)
    
    def cleanup(self):
        """关闭窗口时清理资源"""
        for recorder in self.camera_recorders.values():
            recorder.stop_recording()
            recorder.stop()
        
        if self.data_sync_manager.is_monitoring:
            self.data_sync_manager.stop_monitoring()
            if self.data_sync_manager.sync_records and self.is_recording:
                reply = QMessageBox.question(self, "保存同步数据", "有未保存的同步记录数据。是否保存？", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    subject_dir = os.path.join(self.output_dir_edit.text(), self.current_subject or f"未命名_{get_timestamp()}")
                    os.makedirs(subject_dir, exist_ok=True)
                    sync_file = os.path.join(subject_dir, "sync_data.json")
                    self.data_sync_manager.save_sync_data(sync_file)
