import os
import sys
import threading
import time
import logging
from datetime import datetime
from report_generator_v2 import generate_report

# 配置日志
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

# 生成带时间戳的日志文件名
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = os.path.join(log_dir, f'report_task_{timestamp}.log')

# 配置日志
logging.basicConfig(
    level=logging.INFO,  # 保留INFO级别日志
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

class ReportTask:
    def __init__(self, input_file, original_filename):
        self.input_file = input_file
        self.original_filename = original_filename  # 存储原始文件名
        self.output_file = None
        self.progress = 0
        self.status = {}  # pending, running, success, failed
        self.status['state'] = 'pending'
        self.thread = None
        self.error = None
        self.logs = []  # 新增日志列表
        self.output_file_size = None  # 新增文件大小属性
        self.cancelled = False  # 新增取消标志
        self.variables_filename = None

    def run(self):
        self.status['status'] = 'running'
        try:
            # 模拟执行过程，实际情况需要根据process_single_file的实现来更新进度,这里设置几个关键节点来更新
            logging.info(f'开始处理文件: {self.input_file}')
            self.logs.append(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - 开始处理文件: {self.original_filename}')
            self.output_file = generate_report(self.input_file, self, self.variables_filename)
            self.status['status'] = 'success'
            self.output_file_size = os.path.getsize(self.output_file)  # 获取文件大小
            logging.info(f'文件处理成功')
            self.logs.append(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - 文件处理成功')
        except Exception as e:
            self.status['status'] = 'failed'
            self.error = str(e)
            logging.error(f'处理文件失败: {e}')
            self.logs.append(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - 处理文件失败: {e}')
        finally:
            if not self.cancelled:  # 如果任务没有被取消
                logging.info('任务完成')
                self.logs.append(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - 任务完成')
    def update_progress(self, progress):
        """更新进度"""
        if isinstance(progress, dict):
          self.progress = progress.get('progress', self.progress)
          if 'log' in progress:
              self.logs.append(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - {progress["log"]}')
        else:
          self.progress = progress

        # 检查是否取消
        if self.cancelled:
            raise Exception('任务已取消')
    
    def start(self):
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def get_status(self):
        return {
            'progress': self.progress,
            'status': self.status,
            'output_file': self.output_file,
            'output_file_size': self.output_file_size,
            'error': self.error,
            'logs': self.logs  # 返回日志信息
        }
    
    def cancel(self):
        """取消任务"""
        self.cancelled = True

if __name__ == '__main__':
    # 示例用法
    task = ReportTask('input.xlsx')
    task.start()
    while task.thread.is_alive():
        status = task.get_status()
        print(f"Progress: {status['progress']}, Status: {status['status']}")
        time.sleep(1)

    status = task.get_status()
    print(f"Final Status: {status['status']}, Output File: {status['output_file']}")
