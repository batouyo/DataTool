import os
import json
import datetime
import watchdog.observers
import watchdog.events
from utils.helpers import get_beijing_time, get_timestamp

class DataSyncManager:
    """生理数据与视频同步管理器
    
    负责监控生理数据文件变化并与视频录制同步
    """
    
    def __init__(self, data_path=None):
        """初始化同步管理器
        
        Args:
            data_path: 生理数据文件或目录路径
        """
        self.data_path = data_path
        self.is_monitoring = False
        self.observer = None
        self.sync_records = []  # 记录同步数据 [{'timestamp': ..., 'video_frames': {...}, 'data_event': ...}]
        self.recorders = {}  # 记录关联的VideoRecorder实例 {camera_id: recorder}
        self._last_event_time = None
        self._last_event_path = None
        self._debounce_interval = datetime.timedelta(milliseconds=100)  # 100毫秒去抖动间隔
        
    def set_data_path(self, path):
        """设置需要监控的数据文件路径
        
        Args:
            path: 文件或目录路径
        """
        self.data_path = path
        
    def add_recorder(self, camera_id, recorder):
        """添加要同步的录像机
        
        Args:
            camera_id: 摄像头ID
            recorder: VideoRecorder实例
        """
        self.recorders[camera_id] = recorder
        
    def remove_recorder(self, camera_id):
        """移除同步的录像机
        
        Args:
            camera_id: 摄像头ID
        """
        if camera_id in self.recorders:
            del self.recorders[camera_id]
            
    def start_monitoring(self):
        """开始监控数据文件变化"""
        if self.is_monitoring or not self.data_path:
            return False
            
        try:
            class FileChangeHandler(watchdog.events.FileSystemEventHandler):
                def __init__(self, callback):
                    self.callback = callback
                    
                def on_modified(self, event):
                    if not event.is_directory:
                        self.callback(event.src_path)
            
            # 创建观察者和处理器
            self.observer = watchdog.observers.Observer()
            
            # 确定监控目标（文件或目录）
            target_path = self.data_path
            if os.path.isfile(self.data_path):
                # 如果是文件，监控其父目录
                target_path = os.path.dirname(self.data_path)
                
            # 设置监控
            self.observer.schedule(
                FileChangeHandler(self._on_data_file_changed),
                target_path,
                recursive=False
            )
            
            # 开始监控
            self.observer.start()
            self.is_monitoring = True
            print(f"开始监控数据文件: {self.data_path}")
            return True
            
        except Exception as e:
            print(f"启动文件监控失败: {str(e)}")
            return False
    
    def stop_monitoring(self):
        """停止监控数据文件变化"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        self.is_monitoring = False
        print("已停止文件监控")
    
    def _on_data_file_changed(self, file_path):
        """当数据文件变化时的回调
        
        Args:
            file_path: 发生变化的文件路径
        """
        # 检查是否是我们关心的文件
        if os.path.isfile(self.data_path) and os.path.normpath(file_path) != os.path.normpath(self.data_path):
            return
            
        # 获取当前时间戳
        current_time = datetime.datetime.now()

        # 事件去抖动处理
        if self._last_event_time and self._last_event_path == file_path:
            if (current_time - self._last_event_time) < self._debounce_interval:
                # print(f"忽略重复的同步事件: {file_path}")
                return
        
        self._last_event_time = current_time
        self._last_event_path = file_path
        
        beijing_time = get_beijing_time()
        
        # 收集所有活动录像机的当前帧信息
        frames_info = {}
        for camera_id, recorder in self.recorders.items():
            if recorder.recording:
                frames_info[str(camera_id)] = {
                    'frame_count': recorder.frame_count,
                    'elapsed_seconds': (current_time - recorder.start_time).total_seconds()
                }
        
        # 只有在有活动录像机时才记录同步信息
        if frames_info:
            # 获取文件最后修改时间
            try:
                file_mtime = os.path.getmtime(file_path)
                file_mtime_str = datetime.datetime.fromtimestamp(file_mtime).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            except:
                file_mtime_str = "未知"
                
            # 创建同步记录
            sync_record = {
                'timestamp': current_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                'beijing_time': beijing_time,
                'video_frames': frames_info,
                'data_event': {
                    'file': os.path.basename(file_path),
                    'mtime': file_mtime_str
                }
            }
            
            self.sync_records.append(sync_record)
            print(f"同步事件记录: {sync_record}")
    
    def save_sync_data(self, output_path):
        """保存同步数据到JSON文件
        
        Args:
            output_path: 输出文件路径
        
        Returns:
            bool: 保存是否成功
        """
        if not self.sync_records:
            print("没有同步记录可供保存")
            return False
            
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'sync_records': self.sync_records,
                    'generated_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'data_file': self.data_path
                }, f, indent=2, ensure_ascii=False)
            
            print(f"同步数据已保存至: {output_path}")
            return True
        except Exception as e:
            print(f"保存同步数据失败: {str(e)}")
            return False
    
    def reset(self):
        """重置同步记录"""
        self.sync_records = []
        
    def __del__(self):
        """析构函数，确保停止监控"""
        self.stop_monitoring()
