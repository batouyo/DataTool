import re
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from datetime import datetime
import argparse
import matplotlib

# 检测并配置中文字体
def setup_chinese_fonts():
    """检测系统中可用的中文字体并配置matplotlib"""
    from matplotlib.font_manager import FontManager
    import platform
    
    # 获取所有可用字体
    font_manager = FontManager()
    font_names = [font.name for font in font_manager.ttflist]
    
    # 常见中文字体列表
    chinese_fonts = [
        'SimHei', 'Microsoft YaHei', 'SimSun', 'NSimSun', 'FangSong', 'KaiTi',
        'Arial Unicode MS', 'DengXian', 'STSong', 'STFangsong', 'STKaiti', 'STXihei',
        'Heiti SC', 'Heiti TC', 'LiHei Pro', 'Hiragino Sans GB', 'WenQuanYi Zen Hei',
        'WenQuanYi Micro Hei', 'Source Han Sans CN', 'Source Han Serif CN',
        'Noto Sans CJK SC', 'Noto Sans CJK TC', 'Noto Sans CJK JP', 'Noto Sans CJK KR'
    ]
    
    # 找到系统中可用的中文字体
    available_chinese_fonts = []
    for font in chinese_fonts:
        if font in font_names:
            available_chinese_fonts.append(font)
    
    # 如果找到可用的中文字体，配置matplotlib
    if available_chinese_fonts:
        print(f"找到可用的中文字体: {available_chinese_fonts}")
        matplotlib.rcParams['font.sans-serif'] = available_chinese_fonts + ['sans-serif']
        matplotlib.rcParams['axes.unicode_minus'] = False
        matplotlib.rcParams['font.family'] = 'sans-serif'
        return True
    else:
        print("警告: 未找到可用的中文字体，图形中的中文可能无法正确显示")
        return False

# 尝试设置中文字体
setup_chinese_fonts()

# 如果上面的方法失败，使用备选方案
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False
matplotlib.rcParams['font.family'] = 'sans-serif'


class OximeterDataAnalyzer:
    def __init__(self, input_file):
        """初始化分析器"""
        self.input_file = input_file
        self.signals = {}  # 存储所有信号数据
        self.timestamps = {}  # 存储时间戳
        self.sampling_rates = {}  # 存储采样率
        self.units = {}  # 存储单位
        self.discrete_params = {}  # 存储离散参数
        
    def parse_file(self):
        """解析输入文件"""
        print(f"解析文件: {self.input_file}")
        
        with open(self.input_file, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 提取时间戳
        timestamp_matches = re.findall(r'Received at\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', content)
        all_timestamps = [datetime.strptime(ts, '%Y-%m-%d %H:%M:%S') for ts in timestamp_matches]
        
        # 提取OBX段落（包含实际数据）
        obx_segments = re.findall(r'OBX\|\d+\|([A-Z]{2})\|([\d\^]+)\^([^\^]+)\^[^\|]+\|([^\|]+)\|([^\|]+)', content)
        
        # 提取不同类型的信号
        for segment_type, signal_code, signal_name, signal_id, values in obx_segments:
            # 处理NA类型（波形数据）
            if segment_type == 'NA':
                # 提取波形数据值
                if '^' in values:
                    # 有些波形数据使用^分隔
                    try:
                        data_values = []
                        for x in values.split('^'):
                            x = x.strip()
                            if x and x.lstrip('-').isdigit():
                                data_values.append(int(x))
                            else:
                                data_values.append(np.nan)
                        
                        # 如果所有值都是NaN，跳过这个信号
                        if all(np.isnan(v) for v in data_values):
                            continue
                        
                        # 存储波形数据
                        if signal_name not in self.signals:
                            self.signals[signal_name] = []
                            self.timestamps[signal_name] = []
                        
                        self.signals[signal_name].extend(data_values)
                        
                        # 如果有时间戳，则与数据关联
                        if all_timestamps:
                            timestamp = all_timestamps[0]  # 使用当前数据块的时间戳
                            self.timestamps[signal_name].append(timestamp)
                    except Exception as e:
                        print(f"解析'{signal_name}'信号数据时出错: {str(e)}")
            
            # 处理NM类型（数值数据）
            elif segment_type == 'NM':
                if signal_name == 'MDC_ATTR_SAMP_RATE':
                    # 采样率
                    try:
                        rate_value = float(values)
                        if rate_value > 0:  # 确保采样率为正数
                            parent_signal = self.get_parent_signal(signal_id)
                            if parent_signal:
                                self.sampling_rates[parent_signal] = rate_value
                    except (ValueError, TypeError):
                        print(f"无法解析'{signal_name}'的采样率: {values}")
                
                elif signal_name == 'MDC_ATTR_NU_MSMT_RES':
                    # 测量分辨率
                    pass
                
                elif signal_name in ['MDC_PULS_OXIM_SAT_O2', 'MDC_PULS_OXIM_PULS_RATE', 'MDC_BLD_PERF_INDEX', 
                                    'MDC_TTHOR_RESP_RATE', 'MDC_ECG_HEART_RATE']:
                    # 离散参数
                    try:
                        value = float(values)
                        self.discrete_params[signal_name] = value
                    except (ValueError, TypeError):
                        print(f"无法解析'{signal_name}'的值: {values}")
        
        # 检查并设置默认采样率
        default_sampling_rates = {
            'ECG': 500,
            'PLETH': 60,
            'IMPED': 256
        }
        
        for signal_name in self.signals.keys():
            if signal_name not in self.sampling_rates:
                # 根据信号名称设置默认采样率
                for signal_type, rate in default_sampling_rates.items():
                    if signal_type in signal_name:
                        self.sampling_rates[signal_name] = rate
                        break
                else:
                    # 如果没有匹配的信号类型，使用通用默认值
                    self.sampling_rates[signal_name] = 100
        
        # 检查是否成功解析到数据
        if not self.signals:
            print("警告: 未能找到有效的波形数据!")
        else:
            print(f"成功解析到 {len(self.signals)} 种信号:")
            for signal_name, data in self.signals.items():
                sampling_rate = self.sampling_rates.get(signal_name, "未知")
                print(f"  - {signal_name}: {len(data)} 个采样点, 采样率: {sampling_rate} Hz")
    
    def get_parent_signal(self, signal_id):
        """从信号ID中提取父信号名称"""
        parts = signal_id.split('.')
        if len(parts) >= 4:
            # 在OBX segments中，父信号ID通常是前几个部分
            parent_id = '.'.join(parts[:-1])
            
            # 在已解析的信号中查找匹配的信号名
            for signal_name in self.signals.keys():
                if parent_id in signal_name:
                    return signal_name
        return None
    
    def visualize_waveforms(self):
        """可视化波形数据"""
        if not self.signals:
            print("无数据可供可视化")
            return
        
        # 将信号分类
        ecg_signals = {k: v for k, v in self.signals.items() if 'ECG' in k}
        pleth_signals = {k: v for k, v in self.signals.items() if 'PLETH' in k}
        imp_signals = {k: v for k, v in self.signals.items() if 'IMPED' in k}
        other_signals = {k: v for k, v in self.signals.items() if 'ECG' not in k and 'PLETH' not in k and 'IMPED' not in k}
        
        # 创建图形
        num_plots = len(ecg_signals) + (1 if pleth_signals else 0) + (1 if imp_signals else 0) + len(other_signals)
        if num_plots == 0:
            print("没有可供绘制的波形数据")
            return
        
        fig = plt.figure(figsize=(15, num_plots * 3))
        gs = GridSpec(num_plots, 1, figure=fig)
        
        # 设置全局字体
        plt.rcParams['font.sans-serif'] = matplotlib.rcParams['font.sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
        
        plot_idx = 0
        
        # 绘制ECG信号
        for signal_name, data in ecg_signals.items():
            ax = fig.add_subplot(gs[plot_idx])
            
            # 确定X轴时间刻度
            sampling_rate = self.sampling_rates.get(signal_name, 500)  # 默认500Hz
            time_seconds = np.arange(len(data)) / sampling_rate
            
            # 绘制波形
            ax.plot(time_seconds, data, label=signal_name)
            ax.set_title(f"ECG 波形: {signal_name}", fontproperties=plt.rcParams['font.sans-serif'][0])
            ax.set_xlabel("时间 (秒)", fontproperties=plt.rcParams['font.sans-serif'][0])
            ax.set_ylabel("振幅 (mV)", fontproperties=plt.rcParams['font.sans-serif'][0])
            ax.grid(True)
            ax.legend(prop={'family': plt.rcParams['font.sans-serif'][0]})
            
            plot_idx += 1
        
        # 绘制血氧脉搏波形
        if pleth_signals:
            ax = fig.add_subplot(gs[plot_idx])
            for signal_name, data in pleth_signals.items():
                sampling_rate = self.sampling_rates.get(signal_name, 60)  # 默认60Hz
                time_seconds = np.arange(len(data)) / sampling_rate
                
                ax.plot(time_seconds, data, label=signal_name)
                ax.set_title("血氧脉搏波形", fontproperties=plt.rcParams['font.sans-serif'][0])
                ax.set_xlabel("时间 (秒)", fontproperties=plt.rcParams['font.sans-serif'][0])
                ax.set_ylabel("振幅", fontproperties=plt.rcParams['font.sans-serif'][0])
                ax.grid(True)
                ax.legend(prop={'family': plt.rcParams['font.sans-serif'][0]})
                
            plot_idx += 1
        
        # 绘制胸阻抗波形
        if imp_signals:
            ax = fig.add_subplot(gs[plot_idx])
            for signal_name, data in imp_signals.items():
                sampling_rate = self.sampling_rates.get(signal_name, 256)  # 默认256Hz
                time_seconds = np.arange(len(data)) / sampling_rate
                
                ax.plot(time_seconds, data, label=signal_name)
                ax.set_title("胸阻抗波形", fontproperties=plt.rcParams['font.sans-serif'][0])
                ax.set_xlabel("时间 (秒)", fontproperties=plt.rcParams['font.sans-serif'][0])
                ax.set_ylabel("阻抗", fontproperties=plt.rcParams['font.sans-serif'][0])
                ax.grid(True)
                ax.legend(prop={'family': plt.rcParams['font.sans-serif'][0]})
                
            plot_idx += 1
        
        # 绘制其他信号
        for signal_name, data in other_signals.items():
            ax = fig.add_subplot(gs[plot_idx])
            
            sampling_rate = self.sampling_rates.get(signal_name, 100)  # 默认100Hz
            time_seconds = np.arange(len(data)) / sampling_rate
            
            ax.plot(time_seconds, data, label=signal_name)
            ax.set_title(f"其他波形: {signal_name}", fontproperties=plt.rcParams['font.sans-serif'][0])
            ax.set_xlabel("时间 (秒)", fontproperties=plt.rcParams['font.sans-serif'][0])
            ax.set_ylabel("值", fontproperties=plt.rcParams['font.sans-serif'][0])
            ax.grid(True)
            ax.legend(prop={'family': plt.rcParams['font.sans-serif'][0]})
            
            plot_idx += 1
        
        plt.tight_layout()
        
        # 保存图片
        output_image = os.path.splitext(self.input_file)[0] + "_waveforms.png"
        plt.savefig(output_image, dpi=300)
        print(f"波形图已保存至 {output_image}")
        
        # 显示图形
        plt.show()
    
    def export_to_excel(self):
        """将数据导出为Excel文件"""
        if not self.signals and not self.discrete_params:
            print("无数据可供导出")
            return
        
        # 创建安全的文件名（移除特殊字符）
        base_name = os.path.basename(self.input_file)
        base_name = base_name.replace(',', '_').replace(' ', '_')
        safe_name = ''.join(c for c in base_name if c.isalnum() or c in '_.-')
        
        # 创建Excel写入器
        output_dir = os.path.dirname(self.input_file)
        output_file = os.path.join(output_dir, os.path.splitext(safe_name)[0] + "_data.xlsx")
        
        # 如果文件已存在，添加时间戳避免冲突
        if os.path.exists(output_file):
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_file = os.path.join(output_dir, os.path.splitext(safe_name)[0] + f"_data_{timestamp}.xlsx")
        
        try:
            writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
            
            # 导出波形数据（按秒组织）
            for signal_name, data in self.signals.items():
                # 获取采样率并确保它是有效的数值
                sampling_rate = self.sampling_rates.get(signal_name, 100)  # 默认100Hz
                if np.isnan(sampling_rate) or sampling_rate <= 0:
                    sampling_rate = 100  # 如果采样率无效，使用默认值
                
                # 确保采样率是整数
                sampling_rate = int(sampling_rate)
                
                # 将数据重组为按秒的格式
                seconds = int(np.ceil(len(data) / sampling_rate))
                reshaped_data = {}
                
                for i in range(seconds):
                    start_idx = int(i * sampling_rate)
                    end_idx = int((i + 1) * sampling_rate)
                    
                    # 确保索引不超出范围
                    end_idx = min(end_idx, len(data))
                    
                    # 获取当前秒的数据
                    second_data = data[start_idx:end_idx]
                    
                    # 如果当前秒的数据点数少于采样率，则补充NaN值
                    if len(second_data) < sampling_rate:
                        second_data = np.pad(second_data, 
                                            (0, sampling_rate - len(second_data)),
                                            'constant', 
                                            constant_values=np.nan)
                    
                    # 存储当前秒的数据
                    reshaped_data[f'第{i+1}秒'] = second_data
                
                # 创建DataFrame
                df = pd.DataFrame(reshaped_data)
                
                # 添加采样点索引列
                df.index = [f'采样点{i+1}' for i in range(len(df))]
                
                # 创建安全的表名
                sheet_name = ''.join(c for c in signal_name[:30] if c.isalnum() or c in '_')
                if not sheet_name:  # 如果表名为空，使用默认名称
                    sheet_name = f"Signal_{len(writer.sheets)}"
                
                # 将DataFrame写入Excel
                df.to_excel(writer, sheet_name=sheet_name)
                
                # 调整列宽
                worksheet = writer.sheets[sheet_name]
                worksheet.set_column(0, len(reshaped_data), 12)
            
            # 导出离散参数
            if self.discrete_params:
                # 创建DataFrame
                params_df = pd.DataFrame({
                    '参数名': list(self.discrete_params.keys()),
                    '值': list(self.discrete_params.values())
                })
                
                # 将DataFrame写入Excel
                params_df.to_excel(writer, sheet_name='离散参数', index=False)
                
                # 调整列宽
                worksheet = writer.sheets['离散参数']
                worksheet.set_column(0, 0, 30)
                worksheet.set_column(1, 1, 15)
            
            # 保存Excel文件
            writer.close()
            print(f"数据已导出至 {output_file}")
            return output_file
        
        except PermissionError:
            print(f"权限错误: 无法写入文件 '{output_file}'")
            print("可能是文件已被其他程序打开，请关闭该文件后重试")
            # 尝试使用备用文件名
            try:
                backup_file = os.path.join(output_dir, "oximeter_data_backup.xlsx")
                writer = pd.ExcelWriter(backup_file, engine='xlsxwriter')
                # ... 重复上面的导出逻辑 ...
                writer.close()
                print(f"数据已导出至备用文件: {backup_file}")
                return backup_file
            except Exception as e:
                print(f"备用导出也失败: {str(e)}")
                return None
        
        except Exception as e:
            print(f"导出Excel时出错: {str(e)}")
            return None


def main():
    parser = argparse.ArgumentParser(description='血氧仪数据分析工具')
    parser.add_argument('input_file', help='输入的血氧仪数据文件路径')
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not os.path.exists(args.input_file):
        print(f"错误: 文件 '{args.input_file}' 不存在!")
        return
    
    # 创建分析器实例
    analyzer = OximeterDataAnalyzer(args.input_file)
    
    # 解析文件
    analyzer.parse_file()
    
    # 可视化波形
    analyzer.visualize_waveforms()
    
    # 导出到Excel
    analyzer.export_to_excel()


if __name__ == "__main__":
    main() 