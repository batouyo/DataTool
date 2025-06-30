import datetime
import matplotlib
from matplotlib.font_manager import FontManager

# 添加北京时间转换功能
def get_beijing_time():
    """获取北京时间"""
    # 北京时间是UTC+8
    utc_now = datetime.datetime.utcnow()
    beijing_now = utc_now + datetime.timedelta(hours=8)
    return beijing_now.strftime("%Y-%m-%d %H:%M:%S")

# 添加时间戳函数，用于日志和文件名
def get_timestamp():
    """获取当前时间戳，格式为：年月日_时分秒"""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# 配置中文字体
def setup_chinese_fonts():
    """检测系统中可用的中文字体并配置matplotlib"""
    
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
        print("警告: 未找到可用的中文字体")
        return False
