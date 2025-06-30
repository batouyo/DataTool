import os
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
                           QPushButton, QComboBox, QFileDialog, QMessageBox,
                           QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import pyqtSlot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from workers.analysis_thread import AnalysisThread

class MatplotlibCanvas(FigureCanvas):
    """Matplotlib画布类，用于在Qt界面中显示图形"""
    def __init__(self, parent=None, width=10, height=6, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(MatplotlibCanvas, self).__init__(self.fig)

class OximeterTab(QWidget):
    """血氧仪数据分析选项卡"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.analyzer = None
        self.input_file = None
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        oximeter_layout = QVBoxLayout(self)
        
        # 顶部控制区域
        control_layout = QHBoxLayout()
        
        # 文件选择区域
        file_group = QGroupBox("数据文件")
        file_layout = QHBoxLayout(file_group)
        
        self.file_path_label = QLabel("未选择文件")
        self.file_path_label.setWordWrap(True)
        self.browse_oximeter_button = QPushButton("浏览...")
        self.browse_oximeter_button.clicked.connect(self.browse_oximeter_file)
        
        file_layout.addWidget(self.file_path_label, 3)
        file_layout.addWidget(self.browse_oximeter_button, 1)
        
        # 操作区域
        action_group = QGroupBox("操作")
        action_layout = QHBoxLayout(action_group)
        
        self.analyze_button = QPushButton("分析数据")
        self.analyze_button.clicked.connect(self.analyze_data)
        self.analyze_button.setEnabled(False)
        
        self.export_excel_button = QPushButton("导出Excel")
        self.export_excel_button.clicked.connect(self.export_to_excel)
        self.export_excel_button.setEnabled(False)
        
        self.save_image_button = QPushButton("保存图像")
        self.save_image_button.clicked.connect(self.save_image)
        self.save_image_button.setEnabled(False)
        
        action_layout.addWidget(self.analyze_button)
        action_layout.addWidget(self.export_excel_button)
        action_layout.addWidget(self.save_image_button)
        
        # 信号选择区域
        signal_group = QGroupBox("信号选择")
        signal_layout = QHBoxLayout(signal_group)
        
        self.signal_selector = QComboBox()
        self.signal_selector.currentIndexChanged.connect(self.update_plot)
        self.signal_selector.setEnabled(False)
        
        signal_layout.addWidget(QLabel("选择信号:"))
        signal_layout.addWidget(self.signal_selector)
        
        # 添加控制区域到布局
        control_layout.addWidget(file_group, 3)
        control_layout.addWidget(action_group, 2)
        control_layout.addWidget(signal_group, 2)
        
        oximeter_layout.addLayout(control_layout)
        
        # 创建内部标签页
        self.oximeter_tab_widget = QTabWidget()
        
        # 波形显示标签页
        self.waveform_tab = QWidget()
        waveform_layout = QVBoxLayout(self.waveform_tab)
        
        # 创建Matplotlib画布
        self.canvas = MatplotlibCanvas(width=10, height=6)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        waveform_layout.addWidget(self.toolbar)
        waveform_layout.addWidget(self.canvas)
        
        # 数据表格标签页
        self.data_tab = QWidget()
        data_layout = QVBoxLayout(self.data_tab)
        
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(0)
        self.data_table.setRowCount(0)
        
        data_layout.addWidget(self.data_table)
        
        # 参数信息标签页
        self.params_tab = QWidget()
        params_layout = QVBoxLayout(self.params_tab)
        
        self.params_table = QTableWidget()
        self.params_table.setColumnCount(2)
        self.params_table.setHorizontalHeaderLabels(["参数名", "值"])
        self.params_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        
        params_layout.addWidget(self.params_table)
        
        # 添加标签页
        self.oximeter_tab_widget.addTab(self.waveform_tab, "波形显示")
        self.oximeter_tab_widget.addTab(self.data_tab, "数据表格")
        self.oximeter_tab_widget.addTab(self.params_tab, "参数信息")
        
        oximeter_layout.addWidget(self.oximeter_tab_widget)
        
        # 状态栏标签
        self.oximeter_status_label = QLabel("准备就绪")
        self.oximeter_status_label.setStyleSheet("color: #666666; padding: 5px;")
        oximeter_layout.addWidget(self.oximeter_status_label)

    def browse_oximeter_file(self):
        """打开文件对话框选择血氧仪数据文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择血氧仪数据文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_path:
            self.input_file = file_path
            self.file_path_label.setText(file_path)
            self.analyze_button.setEnabled(True)
            self.oximeter_status_label.setText(f"已选择文件: {os.path.basename(file_path)}")
    
    def analyze_data(self):
        """分析血氧仪数据文件"""
        if not self.input_file or not os.path.exists(self.input_file):
            QMessageBox.warning(self, "错误", "请先选择有效的数据文件")
            return
        
        # 禁用按钮，防止重复操作
        self.analyze_button.setEnabled(False)
        self.export_excel_button.setEnabled(False)
        self.save_image_button.setEnabled(False)
        
        # 创建并启动分析线程
        self.analysis_thread = AnalysisThread(self.input_file)
        self.analysis_thread.analysis_complete.connect(self.on_analysis_complete)
        self.analysis_thread.error_occurred.connect(self.on_analysis_error)
        self.analysis_thread.progress_update.connect(self.update_oximeter_status)
        self.analysis_thread.start()
        
        self.oximeter_status_label.setText("正在分析数据...")
    
    @pyqtSlot(object)
    def on_analysis_complete(self, analyzer):
        """分析完成后的回调"""
        self.analyzer = analyzer
        
        # 更新信号选择下拉框
        self.signal_selector.clear()
        self.signal_selector.addItem("全部ECG信号")
        self.signal_selector.addItem("全部PLETH信号")
        self.signal_selector.addItem("全部IMPED信号")
        
        for signal_name in self.analyzer.signals.keys():
            self.signal_selector.addItem(signal_name)
        
        # 启用按钮
        self.signal_selector.setEnabled(True)
        self.export_excel_button.setEnabled(True)
        self.save_image_button.setEnabled(True)
        self.analyze_button.setEnabled(True)
        
        # 更新UI
        self.update_plot()
        self.update_data_table()
        self.update_params_table()
        
        self.oximeter_status_label.setText("分析完成")
    
    @pyqtSlot(str)
    def on_analysis_error(self, error_msg):
        """分析出错后的回调"""
        QMessageBox.critical(self, "分析错误", error_msg)
        self.analyze_button.setEnabled(True)
        self.oximeter_status_label.setText("分析失败")
    
    @pyqtSlot(str)
    def update_oximeter_status(self, message):
        """更新状态栏信息"""
        self.oximeter_status_label.setText(message)
    
    def update_plot(self):
        """更新波形图"""
        if not self.analyzer:
            return
        
        # 清除当前图形
        self.canvas.axes.clear()
        
        # 获取当前选择的信号
        current_selection = self.signal_selector.currentText()
        
        # 获取中文字体
        chinese_font = plt.rcParams['font.sans-serif'][0] if plt.rcParams['font.sans-serif'] else 'SimHei'
        
        if current_selection == "全部ECG信号":
            # 绘制所有ECG信号
            ecg_signals = {k: v for k, v in self.analyzer.signals.items() if 'ECG' in k}
            if ecg_signals:
                for i, (signal_name, data) in enumerate(ecg_signals.items()):
                    sampling_rate = self.analyzer.sampling_rates.get(signal_name, 500)
                    # 确保采样率是有效值
                    if np.isnan(sampling_rate) or sampling_rate <= 0:
                        sampling_rate = 500  # 默认值
                    time_seconds = np.arange(len(data)) / sampling_rate
                    self.canvas.axes.plot(time_seconds, data, label=signal_name)
                
                self.canvas.axes.set_title("心电图(ECG)波形", fontproperties=chinese_font)
        
        elif current_selection == "全部PLETH信号":
            # 绘制所有PLETH信号
            pleth_signals = {k: v for k, v in self.analyzer.signals.items() if 'PLETH' in k}
            if pleth_signals:
                for signal_name, data in pleth_signals.items():
                    sampling_rate = self.analyzer.sampling_rates.get(signal_name, 60)
                    # 确保采样率是有效值
                    if np.isnan(sampling_rate) or sampling_rate <= 0:
                        sampling_rate = 60  # 默认值
                    time_seconds = np.arange(len(data)) / sampling_rate
                    self.canvas.axes.plot(time_seconds, data, label=signal_name)
                
                self.canvas.axes.set_title("血氧脉搏波形", fontproperties=chinese_font)
        
        elif current_selection == "全部IMPED信号":
            # 绘制所有IMPED信号
            imp_signals = {k: v for k, v in self.analyzer.signals.items() if 'IMPED' in k}
            if imp_signals:
                for signal_name, data in imp_signals.items():
                    sampling_rate = self.analyzer.sampling_rates.get(signal_name, 256)
                    # 确保采样率是有效值
                    if np.isnan(sampling_rate) or sampling_rate <= 0:
                        sampling_rate = 256  # 默认值
                    time_seconds = np.arange(len(data)) / sampling_rate
                    self.canvas.axes.plot(time_seconds, data, label=signal_name)
                
                self.canvas.axes.set_title("胸阻抗波形", fontproperties=chinese_font)
        
        else:
            # 绘制单个选定信号
            if current_selection in self.analyzer.signals:
                data = self.analyzer.signals[current_selection]
                sampling_rate = self.analyzer.sampling_rates.get(current_selection, 100)
                # 确保采样率是有效值
                if np.isnan(sampling_rate) or sampling_rate <= 0:
                    sampling_rate = 100  # 默认值
                time_seconds = np.arange(len(data)) / sampling_rate
                
                self.canvas.axes.plot(time_seconds, data)
                self.canvas.axes.set_title(f"波形: {current_selection}", fontproperties=chinese_font)
        
        # 设置坐标轴标签
        self.canvas.axes.set_xlabel("时间 (秒)", fontproperties=chinese_font)
        self.canvas.axes.set_ylabel("振幅", fontproperties=chinese_font)
        self.canvas.axes.grid(True)
        self.canvas.axes.legend(prop={'family': chinese_font})
        
        # 刷新画布
        self.canvas.draw()
    
    def update_data_table(self):
        """更新数据表格"""
        if not self.analyzer or not self.analyzer.signals:
            return
        
        # 获取当前选择的信号
        current_selection = self.signal_selector.currentText()
        
        # 如果是分组选项，选择第一个匹配的信号
        if current_selection == "全部ECG信号":
            ecg_signals = {k: v for k, v in self.analyzer.signals.items() if 'ECG' in k}
            if ecg_signals:
                signal_name = list(ecg_signals.keys())[0]
                data = ecg_signals[signal_name]
            else:
                self.data_table.setRowCount(0)
                self.data_table.setColumnCount(0)
                return
        elif current_selection == "全部PLETH信号":
            pleth_signals = {k: v for k, v in self.analyzer.signals.items() if 'PLETH' in k}
            if pleth_signals:
                signal_name = list(pleth_signals.keys())[0]
                data = pleth_signals[signal_name]
            else:
                self.data_table.setRowCount(0)
                self.data_table.setColumnCount(0)
                return
        elif current_selection == "全部IMPED信号":
            imp_signals = {k: v for k, v in self.analyzer.signals.items() if 'IMPED' in k}
            if imp_signals:
                signal_name = list(imp_signals.keys())[0]
                data = imp_signals[signal_name]
            else:
                self.data_table.setRowCount(0)
                self.data_table.setColumnCount(0)
                return
        else:
            # 单个信号
            if current_selection in self.analyzer.signals:
                signal_name = current_selection
                data = self.analyzer.signals[signal_name]
            else:
                self.data_table.setRowCount(0)
                self.data_table.setColumnCount(0)
                return
        
        # 获取采样率并确保它是有效的整数
        sampling_rate = self.analyzer.sampling_rates.get(signal_name, 100)
        if np.isnan(sampling_rate) or sampling_rate <= 0:
            sampling_rate = 100  # 如果采样率无效，使用默认值
        sampling_rate = int(sampling_rate)
        
        # 将数据按秒组织
        seconds = min(10, int(np.ceil(len(data) / sampling_rate)))  # 最多显示10秒数据
        
        # 设置表格大小
        self.data_table.setRowCount(sampling_rate)
        self.data_table.setColumnCount(seconds)
        
        # 设置表头
        self.data_table.setHorizontalHeaderLabels([f"第{i+1}秒" for i in range(seconds)])
        self.data_table.setVerticalHeaderLabels([f"采样点{i+1}" for i in range(sampling_rate)])
        
        # 填充数据
        for second in range(seconds):
            start_idx = int(second * sampling_rate)
            end_idx = min(int((second + 1) * sampling_rate), len(data))
            
            for i, value in enumerate(data[start_idx:end_idx]):
                item = QTableWidgetItem(str(value))
                self.data_table.setItem(i, second, item)
        
        # 调整列宽
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    
    def update_params_table(self):
        """更新参数表格"""
        if not self.analyzer:
            return
        
        # 清除当前表格内容
        self.params_table.setRowCount(0)
        
        # 添加离散参数
        if self.analyzer.discrete_params:
            self.params_table.setRowCount(len(self.analyzer.discrete_params))
            
            for i, (param_name, value) in enumerate(self.analyzer.discrete_params.items()):
                # 参数名
                name_item = QTableWidgetItem(param_name)
                self.params_table.setItem(i, 0, name_item)
                
                # 参数值
                value_item = QTableWidgetItem(str(value))
                self.params_table.setItem(i, 1, value_item)
        
        # 添加采样率信息
        if self.analyzer.sampling_rates:
            current_row = self.params_table.rowCount()
            self.params_table.setRowCount(current_row + len(self.analyzer.sampling_rates))
            
            for i, (signal_name, rate) in enumerate(self.analyzer.sampling_rates.items()):
                # 参数名
                name_item = QTableWidgetItem(f"{signal_name} 采样率")
                self.params_table.setItem(current_row + i, 0, name_item)
                
                # 参数值
                value_item = QTableWidgetItem(f"{rate} Hz")
                self.params_table.setItem(current_row + i, 1, value_item)
    
    def export_to_excel(self):
        """导出数据到Excel"""
        if not self.analyzer:
            return
        
        try:
            self.oximeter_status_label.setText("正在导出Excel...")
            
            base_name = os.path.basename(self.analyzer.input_file)
            base_name = base_name.replace(',', '_').replace(' ', '_')
            safe_name = ''.join(c for c in base_name if c.isalnum() or c in '_.-')
            
            output_dir = os.path.dirname(self.analyzer.input_file)
            default_output_file = os.path.join(output_dir, os.path.splitext(safe_name)[0] + "_data.xlsx")
            
            if os.path.exists(default_output_file):
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Question)
                msg_box.setText(f"文件 {default_output_file} 已存在")
                msg_box.setInformativeText("您想要覆盖现有文件，还是选择新的保存位置？")
                overwrite_button = msg_box.addButton("覆盖", QMessageBox.AcceptRole)
                save_as_button = msg_box.addButton("另存为", QMessageBox.ActionRole)
                cancel_button = msg_box.addButton("取消", QMessageBox.RejectRole)
                msg_box.setDefaultButton(save_as_button)
                
                msg_box.exec_()
                
                if msg_box.clickedButton() == cancel_button:
                    self.oximeter_status_label.setText("导出已取消")
                    return
                elif msg_box.clickedButton() == save_as_button:
                    output_file, _ = QFileDialog.getSaveFileName(
                        self, "导出Excel", default_output_file, "Excel文件 (*.xlsx);;所有文件 (*)"
                    )
                    if not output_file:
                        self.oximeter_status_label.setText("导出已取消")
                        return
                else:  # 覆盖
                    try:
                        os.remove(default_output_file)
                    except Exception as e:
                        QMessageBox.warning(self, "无法覆盖文件", f"无法删除现有文件: {str(e)}\n\n可能是文件正在被其他程序使用。请关闭该文件后重试。")
                        self.oximeter_status_label.setText("导出失败")
                        return
                    
                    output_file = default_output_file
            else:
                output_file = default_output_file
            
            try:
                result = self.analyzer.export_to_excel()
                
                if result:
                    QMessageBox.information(self, "导出成功", f"文件已保存至:\n{result}")
                    self.oximeter_status_label.setText(f"数据已导出至 {result}")
                else:
                    raise Exception("导出函数返回失败")
                    
            except Exception as e:
                QMessageBox.critical(self, "导出错误", f"导出Excel时出错: {str(e)}\n\n可能是文件被其他程序占用或没有写入权限。")
                self.oximeter_status_label.setText("导出失败")
        except Exception as e:
            QMessageBox.critical(self, "导出错误", f"导出Excel时出错: {str(e)}")
            self.oximeter_status_label.setText("导出失败")
    
    def save_image(self):
        """保存当前图像"""
        if not self.analyzer:
            return
        
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存图像", "", "PNG图像 (*.png);;JPEG图像 (*.jpg);;所有文件 (*)"
            )
            
            if file_path:
                self.canvas.fig.savefig(file_path, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "保存成功", f"文件已保存至:\n{file_path}")
                self.oximeter_status_label.setText(f"图像已保存至 {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "保存错误", f"保存图像时出错: {str(e)}")
            self.oximeter_status_label.setText("保存失败")
