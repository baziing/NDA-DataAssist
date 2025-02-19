import schedule
import time
import threading
import json
import os
import sys # 导入 sys 模块
from datetime import datetime
from report_generator_v2 import generate_report
import logging

# 配置日志
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

# 生成带时间戳的日志文件名
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = os.path.join(log_dir, f'task_scheduler_{timestamp}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

class TaskScheduler:
    def __init__(self, tasks_file='tasks.json'):
        self.tasks = []
        self.tasks_file = tasks_file
        self.scheduler = schedule.Scheduler()
        self.stop_event = threading.Event()  # 用于停止调度线程的事件

    def add_task(self, task_info):
        """添加任务"""
        self.tasks.append(task_info)
        self.schedule_task(task_info)
        self.save_tasks()  # 保存到文件
        logging.info(f"任务已添加: {task_info}")

    def load_tasks(self):
        """从文件加载任务"""
        if os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, 'r') as f:
                    self.tasks = json.load(f)
                    for task in self.tasks:
                        self.schedule_task(task)
                logging.info(f"已加载任务: {self.tasks}")
            except json.JSONDecodeError:
                logging.error("任务文件格式错误，无法加载任务。")
                self.tasks = []

    def save_tasks(self):
        """保存任务到文件"""
        with open(self.tasks_file, 'w') as f:
            json.dump(self.tasks, f)

    def schedule_task(self, task_info):
        """安排任务"""
        job = None
        if task_info['frequency'] == 'day':
            job = self.scheduler.every().day
        elif task_info['frequency'] == 'week':
            job = self.scheduler.every().week
            if task_info['dayOfWeek']:
                # schedule库的周几从0开始，0=周一，1=周二，...，6=周日
                weekday_map = {
                    1: schedule.monday,
                    2: schedule.tuesday,
                    3: schedule.wednesday,
                    4: schedule.thursday,
                    5: schedule.friday,
                    6: schedule.saturday,
                    7: schedule.sunday,
                }
                day_of_week = weekday_map.get(int(task_info['dayOfWeek']))
                if day_of_week:
                    job = job.at(task_info['time']).on(day_of_week)
        elif task_info['frequency'] == 'month':
            job = self.scheduler.every().month
            if task_info['dayOfMonth']:
                job = job.at(task_info['time']).day(int(task_info['dayOfMonth']))

        if job is not None:
          job.at(task_info['time']).do(self.run_task, task_info)

    def run_task(self, task_info):
        """运行任务"""
        try:
            logging.info(f"开始执行任务: {task_info['taskName']}")
            # 这里调用 report_generator_v2.py 中的 generate_report 函数
            # generate_report(task_info['filename'], task_info['variables_filename'])
            # 实际调用时，需要根据 generate_report 的具体参数进行调整
            logging.info(f"任务 {task_info['taskName']} 执行完成")
        except Exception as e:
            logging.error(f"任务 {task_info['taskName']} 执行失败: {e}")

    def start(self):
        """启动调度器"""
        self.load_tasks()  # 启动时加载任务
        logging.info("定时任务调度器已启动")
        while not self.stop_event.is_set():
            self.scheduler.run_pending()
            time.sleep(1)

    def stop(self):
        """停止调度器"""
        self.stop_event.set()
        logging.info("定时任务调度器已停止")
