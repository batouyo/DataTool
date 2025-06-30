"""
监护仪数据模拟生成器

这个脚本用于模拟监护仪设备向文本文件定时写入生理数据的行为，
可用于测试数据同步功能。
"""

import os
import sys
import time
import random
import datetime
import argparse
from math import sin, pi

def generate_ecg_sample(sample_count=500, base_value=2048, amplitude=500):
    """生成模拟的ECG波形数据
    
    Args:
        sample_count: 采样点数
        base_value: 基线值
        amplitude: 波形振幅
    
    Returns:
        str: 由^分隔的数据点字符串
    """
    # 创建基本ECG模式的简化版本
    samples = []
    
    for i in range(sample_count):
        # 创建一个粗略的ECG波形：基线 + QRS复合波（简化）
        t = i / sample_count * 2 * pi
        
        # 基础正弦波
        value = sin(t)
        
        # 每隔一定间隔添加"R峰"
        if i % 100 == 50:
            value = 0.8  # R波峰
        elif i % 100 == 60:
            value = -0.4  # S波谷
            
        # 转换到目标振幅和基线
        value = int(base_value + value * amplitude)
        
        # 添加一些随机噪声
        value += random.randint(-20, 20)
        
        samples.append(str(value))
    
    return "^".join(samples)

def generate_pleth_sample(sample_count=60, base_value=2048, amplitude=300):
    """生成模拟的脉搏血氧波形数据
    
    Args:
        sample_count: 采样点数
        base_value: 基线值
        amplitude: 波形振幅
    
    Returns:
        str: 由^分隔的数据点字符串
    """
    samples = []
    
    for i in range(sample_count):
        t = i / sample_count * 2 * pi
        
        # 创建脉搏波形 - 快速上升，缓慢下降
        if i % (sample_count // 5) < (sample_count // 15):
            # 快速上升阶段
            phase = (i % (sample_count // 5)) / (sample_count // 15) * pi/2
            value = sin(phase)
        else:
            # 缓慢下降阶段
            phase = ((i % (sample_count // 5)) - (sample_count // 15)) / ((sample_count // 5) - (sample_count // 15)) * pi/2 + pi/2
            value = cos(phase)
        
        # 转换到目标振幅和基线
        value = int(base_value + value * amplitude)
        
        # 添加一些随机噪声
        value += random.randint(-10, 10)
        
        samples.append(str(value))
    
    return "^".join(samples)

def generate_data_sample():
    """生成一个完整的监护仪数据样本"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 生成一些随机的生理指标
    heart_rate = random.randint(60, 100)
    spo2 = random.randint(95, 100)
    resp_rate = random.randint(12, 20)
    
    # 模拟HL7格式的数据（简化版）
    data = [
        f"Received at {timestamp}",
        f"OBX|1|NA|1.2.3.4.5^ECG I^MDC|1|{generate_ecg_sample()}",
        f"OBX|2|NA|1.2.3.4.6^PLETH^MDC|2|{generate_pleth_sample()}",
        f"OBX|3|NM|1.2.3.4.5.1^MDC_ATTR_SAMP_RATE^MDC|1.1|500",
        f"OBX|4|NM|1.2.3.4.6.1^MDC_ATTR_SAMP_RATE^MDC|2.1|60",
        f"OBX|5|NM|1.2.3.4.7^MDC_ECG_HEART_RATE^MDC|3|{heart_rate}",
        f"OBX|6|NM|1.2.3.4.8^MDC_PULS_OXIM_SAT_O2^MDC|4|{spo2}",
        f"OBX|7|NM|1.2.3.4.9^MDC_TTHOR_RESP_RATE^MDC|5|{resp_rate}"
    ]
    
    return "\n".join(data)

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='监护仪数据模拟生成器')
    parser.add_argument('-f', '--file', default='monitor_data.txt', help='写入的文件路径')
    parser.add_argument('-i', '--interval', type=float, default=5.0, help='写入间隔（秒）')
    parser.add_argument('-c', '--count', type=int, default=0, help='写入次数（0表示无限循环）')
    parser.add_argument('-a', '--append', action='store_true', help='是否追加模式（默认覆盖）')
    args = parser.parse_args()
    
    # 确定文件打开模式
    mode = 'a' if args.append else 'w'
    
    # 打印启动信息
    print(f"数据生成器已启动，将写入文件：{args.file}")
    print(f"写入间隔：{args.interval}秒")
    if args.count > 0:
        print(f"计划写入次数：{args.count}")
    else:
        print("将无限循环写入，按Ctrl+C终止")
    
    try:
        count = 0
        while args.count == 0 or count < args.count:
            # 生成数据
            data = generate_data_sample()
            
            # 写入文件
            with open(args.file, mode, encoding='utf-8') as f:
                f.write(data + "\n\n")
                f.flush()  # 确保立即写入磁盘
            
            # 更新计数和显示
            count += 1
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 已写入第{count}次数据")
            
            # 等待下一次写入
            time.sleep(args.interval)
    
    except KeyboardInterrupt:
        print("\n用户中断，程序结束")
    except Exception as e:
        print(f"发生错误：{str(e)}")
    finally:
        print(f"总共写入了{count}次数据")

if __name__ == "__main__":
    from math import cos  # 导入cos函数用于生成波形
    main() 