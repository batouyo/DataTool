import numpy as np
import traceback
from PyQt5.QtCore import QThread, pyqtSignal
from oximeter_data_analyzer import OximeterDataAnalyzer

class AnalysisThread(QThread):
    """后台分析线程，避免UI卡顿"""
    analysis_complete = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    progress_update = pyqtSignal(str)
    
    def __init__(self, input_file):
        super().__init__()
        self.input_file = input_file
    
    def run(self):
        try:
            self.progress_update.emit("正在解析文件...")
            analyzer = OximeterDataAnalyzer(self.input_file)
            analyzer.parse_file()
            
            # 检查并修复无效的采样率
            for signal_name, rate in analyzer.sampling_rates.items():
                if np.isnan(rate) or rate <= 0:
                    # 根据信号类型设置默认采样率
                    if 'ECG' in signal_name:
                        analyzer.sampling_rates[signal_name] = 500
                    elif 'PLETH' in signal_name:
                        analyzer.sampling_rates[signal_name] = 60
                    elif 'IMPED' in signal_name:
                        analyzer.sampling_rates[signal_name] = 256
                    else:
                        analyzer.sampling_rates[signal_name] = 100
            
            # 如果没有解析到任何数据，提前返回错误
            if not analyzer.signals and not analyzer.discrete_params:
                self.error_occurred.emit("未能从文件中解析出有效数据，请检查文件格式是否正确")
                return
            
            self.progress_update.emit("正在导出Excel数据...")
            try:
                analyzer.export_to_excel()
            except Exception as e:
                # 导出Excel失败不影响其他功能
                error_details = traceback.format_exc()
                print(f"导出Excel失败: {str(e)}\n{error_details}")
                # 继续执行，不中断分析过程
            
            self.analysis_complete.emit(analyzer)
        except Exception as e:
            error_details = traceback.format_exc()
            self.error_occurred.emit(f"分析过程中出错: {str(e)}\n\n详细信息:\n{error_details}")
