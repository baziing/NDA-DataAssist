import schedule
import time
import threading
import json
import os
import sys  # 导入 sys 模块
import pandas as pd
# import mysql.connector # 不需要直接导入
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from .report_generator_v2 import generate_report
import logging
from backend.config import DB_CONFIG
from backend.tools.excel_utils import check_excel_file
from backend.config.mail_config import MAIL_CONFIG
from backend.email_sender import EmailSender
from backend.utils import connect_db, execute_query  # 导入数据库连接函数
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
import urllib.parse

# 配置日志
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

# 生成带日期的日志文件名
timestamp = datetime.now().strftime('%Y%m%d')
global_log_file = os.path.join(log_dir, f'combined_{timestamp}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(global_log_file, mode='a')  # 只输出到文件，使用追加模式
    ]
)

# 创建 Flask 应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求
app.debug = True

# 数据库配置
app.config['DB_CONFIG'] = DB_CONFIG

# 邮件发送器
email_sender = EmailSender()

@app.route('/check_excel_file', methods=['POST'])
def check_excel_file_api():
    """
    接收前端传递的文件，并调用 check_excel_file 函数进行文件校验。
    """
    try:
        if 'file' not in request.files:
            return jsonify({"is_valid": False, "message": "No file part"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"is_valid": False, "message": "No selected file"}), 400

        # 将文件保存到临时位置
        file_path = os.path.join('tmp', file.filename)
        os.makedirs('tmp', exist_ok=True)
        file.save(file_path)

        # 调用 check_excel_file 函数进行校验
        result = check_excel_file(file_path)

        # 删除临时文件
        os.remove(file_path)

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"is_valid": False, "message": f"An error occurred: {str(e)}"}), 500

@app.route('/check_task_name', methods=['POST'])
def check_task_name_api():
    """
    接收前端传递的游戏分类和任务名称，并检查任务名称是否重名。
    """
    try:
        data = request.get_json()
        game_type = data.get('gameType')
        task_name = data.get('taskName')

        if not game_type or not task_name:
            return jsonify({"message": "请填写所有必填项！"}), 400

        # 检查数据库，确保每个游戏分类下，任务名称不能重名
        db_config = app.config['DB_CONFIG']
        connection = None
        cursor = None
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()

            cursor.execute("SELECT * FROM autoreport_tasks WHERE gameType = %s AND taskName = %s", (game_type, task_name))
            result = cursor.fetchone()

            if result:
                return jsonify({"is_valid": False, "message": "任务名称已存在"}), 200
            else:
                return jsonify({"is_valid": True, "message": "任务名称可用"}), 200
        except Exception as e:
            return jsonify({"is_valid": False, "message": f"数据库连接或查询失败: {str(e)}"}), 500
        finally:
            if connection and connection.is_connected():
                if cursor:
                    cursor.close()
                connection.close()


    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

class TaskScheduler:
    def __init__(self):
        self.scheduler = schedule.Scheduler()
        self.stop_event = threading.Event()  # 用于停止调度线程的事件
        self.connection = None  # 初始化为 None
        self.tasks = []

    def get_tasks(self):
        """获取所有任务"""
        cursor = None
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connection = connect_db()  # 重新连接数据库
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM autoreport_tasks")
            tasks = cursor.fetchall()
            return tasks
        except Exception as e:
            logging.error(f"获取任务失败: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def load_tasks(self):
        """从数据库加载任务"""
        cursor = None
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connection = connect_db()
            cursor = self.connection.cursor(dictionary=True)
            # 修改SQL查询，只加载启用的任务
            cursor.execute("SELECT * FROM autoreport_tasks WHERE is_enabled = TRUE")
            tasks = cursor.fetchall()
            for task in tasks:
                try:
                    # Convert dayOfWeek to string
                    if task['dayOfWeek'] is not None:
                        task['dayOfWeek'] = str(task['dayOfWeek'])
                    self.tasks.append(task)
                    self.schedule_task(task)  # 重新安排已加载的任务
                except Exception as e:
                    logging.error(f"加载任务 {task} 失败: {e}", exc_info=True)
            logging.info(f"已加载任务: {len(self.tasks)}")

        except Exception as e:
            logging.error(f"加载任务失败: {e}", exc_info=True)
            self.tasks = []
        finally:
            if cursor:
                cursor.close()


    def schedule_task(self, task_info):
        """根据任务信息安排定时任务"""
        try:
            logging.info(f"Scheduling task with time: {task_info['time']}")
            
            frequency = task_info['frequency']
            day_of_month = task_info['dayOfMonth']
            day_of_week = task_info['dayOfWeek']
            
            # 将数字形式的星期几转换为英文名称 (1-7 对应 周一-周日)
            weekday_mapping = {
                '1': 'monday',
                '2': 'tuesday',
                '3': 'wednesday',
                '4': 'thursday',
                '5': 'friday',
                '6': 'saturday',
                '7': 'sunday'
            }
            
            # 根据频率安排任务
            if frequency == 'day':
                job = self.scheduler.every().day.at(task_info['time'])
            elif frequency == 'week' and day_of_week:
                # 将数字转换为英文星期几名称
                if day_of_week in weekday_mapping:
                    day_of_week_name = weekday_mapping[day_of_week]
                    # 先计算今天的目标时间
                    target_time = datetime.strptime(task_info['time'], '%H:%M').time()
                    target_datetime = datetime.combine(datetime.now().date(), target_time)
                    
                    # 如果是目标星期几，且目标时间还没到，就用今天的时间
                    if datetime.now().weekday() == int(day_of_week) - 1 and target_datetime > datetime.now():
                        next_run_at = target_datetime
                    else:
                        # 否则计算到下一个目标星期几的天数
                        days_ahead = (int(day_of_week) - 1) - datetime.now().weekday()
                        if days_ahead <= 0:  # 如果已经过了本周的目标日期
                            days_ahead += 7
                        next_run_at = datetime.combine((datetime.now() + timedelta(days=days_ahead)).date(), target_time)
                    
                    logging.info(f"周任务 {task_info['taskName']} 的下次执行时间: {next_run_at}")
                    
                    # 使用 schedule 的 every().seconds.do() 来调度
                    time_diff = (next_run_at - datetime.now()).total_seconds()
                    job = self.scheduler.every(int(time_diff)).seconds
                    
                    def weekly_job_wrapper():
                        try:
                            # 执行任务
                            self.run_task(task_info)
                        finally:
                            # 计算下次执行时间
                            next_run_at = calculate_next_run_at(task_info['frequency'], task_info['dayOfMonth'], task_info['dayOfWeek'], task_info['time'])
                            # 创建新的调度（使用新的时间）
                            new_time_diff = (next_run_at - datetime.now()).total_seconds()
                            new_job = self.scheduler.every(int(new_time_diff)).seconds
                            new_job.do(weekly_job_wrapper)
                            logging.info(f"周任务 {task_info['taskName']} 重新调度到 {next_run_at}")
                            # 取消当前的一次性任务
                            return schedule.CancelJob
                    
                    # 直接设置任务回调
                    job.do(weekly_job_wrapper)
                    
                    logging.info(f"周任务 {task_info['taskName']} 已调度到 {next_run_at}")
                    return job
            elif frequency == 'month' and day_of_month:
                # 月度任务处理逻辑
                try:
                    day_of_month = int(day_of_month)
                    logging.info(f"月份日期: {day_of_month}")
                    
                    # 先计算今天的目标时间
                    target_time = datetime.strptime(task_info['time'], '%H:%M').time()
                    target_datetime = datetime.combine(datetime.now().date(), target_time)
                    
                    # 如果是目标日期当天，且目标时间还没到，就用今天的时间
                    if datetime.now().day == day_of_month and target_datetime > datetime.now():
                        next_run_at = target_datetime
                    else:
                        # 否则计算下个月的执行时间
                        if datetime.now().day > day_of_month or (datetime.now().day == day_of_month and target_datetime <= datetime.now()):
                            # 如果今天的日期已经过了目标日期，或者是目标日期但时间已过，调度到下个月
                            month = datetime.now().month + 1
                            year = datetime.now().year
                            if month > 12:
                                month = 1
                                year += 1
                        else:
                            # 如果今天的日期还没到目标日期，调度到本月
                            month = datetime.now().month
                            year = datetime.now().year
                        
                        next_run_at = datetime(year, month, day_of_month, int(task_info['time'][:2]), int(task_info['time'][3:]))
                    
                    logging.info(f"计算得到的下次执行时间: {next_run_at}")
                    
                    # 使用 schedule 的 every().seconds.do() 来调度
                    time_diff = (next_run_at - datetime.now()).total_seconds()
                    job = self.scheduler.every(int(time_diff)).seconds
                    
                    def monthly_job_wrapper():
                        try:
                            # 执行任务
                            self.run_task(task_info)
                        finally:
                            # 计算下次执行时间
                            next_run_at = calculate_next_run_at(task_info['frequency'], task_info['dayOfMonth'], task_info['dayOfWeek'], task_info['time'])
                            # 创建新的调度（使用新的时间）
                            new_time_diff = (next_run_at - datetime.now()).total_seconds()
                            new_job = self.scheduler.every(int(new_time_diff)).seconds
                            new_job.do(monthly_job_wrapper)
                            logging.info(f"月度任务 {task_info['taskName']} 重新调度到 {next_run_at}")
                            # 取消当前的一次性任务
                            return schedule.CancelJob
                    
                    # 直接设置任务回调
                    job.do(monthly_job_wrapper)
                    
                    logging.info(f"月度任务 {task_info['taskName']} 已调度到 {next_run_at}")
                    return job
                except ValueError:
                    logging.error(f"无效的月份日期格式: {day_of_month}")
                    return None
            else:
                logging.error(f"无效的频率设置: {frequency}")
                return None
            
            # 只为非月度任务设置任务回调
            if frequency != 'month':
                job.do(self.run_task, task_info)
            
            return job

        except Exception as e:
            logging.error(f"安排任务失败: {e}")
            return None

    def run_task(self, task_info):
        """运行任务"""
        try:
            logging.info(f"开始执行任务: {task_info['taskName']}")

            # 1. 参数准备
            task_id = task_info['id']
            cursor = None
            try:
                if self.connection is None or not self.connection.is_connected():
                    self.connection = connect_db()
                cursor = self.connection.cursor(dictionary=True)

                # 查询 autoreport_tasks 表
                cursor.execute("SELECT * FROM autoreport_tasks WHERE id = %s", (task_id,))
                task_data = cursor.fetchone()
                if not task_data:
                    raise Exception(f"找不到任务 ID: {task_id}")

                game_type = task_data['gameType']
                task_name = task_data['taskName']
                settings = task_data.get('settings')  # 获取settings字段

                # 解析settings字段
                if settings:
                    try:
                        if isinstance(settings, str):
                            settings = json.loads(settings)
                        # 确保 settings 是字典类型
                        if not isinstance(settings, dict):
                            settings = {}
                    except json.JSONDecodeError:
                        logging.warning(f"解析settings字段失败: {settings}")
                        settings = {}
                else:
                    settings = {}

                # 更新task_info中的settings
                task_info['settings'] = settings
                logging.info(f"任务 {task_name} 的 settings: {settings}")  # 添加日志

                # 查询 autoreport_templates 表
                cursor.execute("SELECT * FROM autoreport_templates WHERE task_id = %s ORDER BY sql_order", (task_id,))
                templates = cursor.fetchall()
                if not templates:
                    raise Exception(f"任务 ID: {task_id} 没有找到对应的 SQL 模板")

            except Exception as e:
                logging.error(f"数据库查询失败: {e}")
                raise
            finally:
                if cursor:
                    cursor.close()

            # 2. 数据筛选与排序 (在此场景中，已经在数据库查询时完成)

            # 3. 报表生成
            # 创建一个 DataFrame，包含 db_name, output_sql, format, transpose(Y/N), pos
            data = []
            for template in templates:
                data.append({
                    'db_name': template['db_name'],
                    'output_sql': template['output_sql'],  # 保留原始格式，不替换换行符
                    'format': template.get('format', ''),
                    'transpose(Y/N)': 'Y' if template.get('transpose') else 'N',  # 将布尔值转换为 Y/N
                    'pos': template.get('pos', ''),
                    'sheet_name': template.get('sheet_name', '汇总报表'),
                    'sheet_order': template.get('sheet_order', 0)
                })
            df = pd.DataFrame(data)

            # 将DataFrame按照sheet_name和sheet_order组织成字典格式
            sheets_data = {}
            for sheet_name, group in df.groupby('sheet_name', dropna=False):
                sheet_name = sheet_name or '汇总报表'  # 如果sheet_name为空，使用默认名称
                sheets_data[sheet_name] = {
                    'order': group['sheet_order'].iloc[0],  # 使用该工作表的第一个order值
                    'data': group  # 直接使用分组后的DataFrame
                }

            # 创建一个模拟的task对象
            class MockTask:
                def __init__(self, task_name, task_info):
                    self.cancelled = False
                    self.progress_data = {'progress': 0, 'log': ''}
                    self.task_name = task_name
                    self._task_info = task_info  # 保存task_info引用

                def update_progress(self, data):
                    self.progress_data = data
                    logging.info(f"Task Progress: {data['progress']}%, Log: {data['log']}")

                @property
                def settings(self):
                    # 优先从task_info获取settings
                    if hasattr(self._task_info, 'settings'):
                        return self._task_info.settings
                    # 如果task_info是字典，从字典中获取
                    if isinstance(self._task_info, dict) and 'settings' in self._task_info:
                        return self._task_info['settings']
                    return None

            task = MockTask(task_data['taskName'], task_info)
            logging.info(f"创建MockTask对象: {task.task_name}, settings: {task.settings}")
            
            # 创建任务专属目录
            output_dir = os.path.join('output', 'report_scheduler', str(task_id))
            os.makedirs(output_dir, exist_ok=True)
            
            # 调用 generate_report 函数，指定输出目录
            output_path = generate_report(task, task_info, data_frame=sheets_data, variables_filename=None, output_dir=output_dir)

            if output_path is None:
                logging.error(f"任务 {task_info['taskName']} 执行完成，但报表路径为空")
            else:
                logging.info(f"任务 {task_info['taskName']} 执行完成，报表已生成: {output_path}")

            # 确保文件路径以 .xlsx 结尾
            if not output_path.lower().endswith('.xlsx'):
                new_output_path = output_path + '.xlsx'
                os.rename(output_path, new_output_path)
                output_path = new_output_path

            # 更新数据库
            now = datetime.now()
            next_run_at = calculate_next_run_at(task_info['frequency'], task_info['dayOfMonth'], task_info['dayOfWeek'], task_info['time'])
            update_sql = "UPDATE autoreport_tasks SET last_run_at = %s, last_run_status = %s, last_run_log = %s, next_run_at = %s WHERE id = %s"
            update_values = (now, 'success', '', next_run_at, task_info['id'])
            try:
                cursor = self.connection.cursor()
                cursor.execute(update_sql, update_values)
                self.connection.commit()
                logging.info(f"任务 {task_info['taskName']} 数据库更新成功")
                
                # 如果成功生成报表，发送邮件
                if output_path:
                    try:
                        # 获取任务的收件人邮箱列表
                        cursor.execute("""
                            WITH task_emails AS (
                                -- 直接关联的邮箱
                                SELECT e.email
                                FROM autoreport_emails e
                                JOIN autoreport_task_recipients tr ON e.id = tr.email_id
                                WHERE tr.task_id = %s
                                
                                UNION
                                
                                -- 通过邮箱组关联的邮箱
                                SELECT e.email
                                FROM autoreport_emails e
                                JOIN autoreport_email_group_members egm ON e.id = egm.email_id
                                JOIN autoreport_task_recipients tr ON egm.group_id = tr.group_id
                                WHERE tr.task_id = %s
                            )
                            SELECT email FROM task_emails ORDER BY email
                        """, (task_id, task_id))
                        
                        recipients = [row[0] for row in cursor.fetchall()]
                        
                        if recipients:
                            # 获取Excel文件名（不包含路径和扩展名）
                            excel_filename = os.path.basename(output_path)
                            excel_name_without_ext = os.path.splitext(excel_filename)[0]
                            
                            # 使用任务的游戏类型创建邮件主题和正文
                            game_type = task_data['gameType']  # 使用之前查询到的任务数据
                            subject = f"【{game_type}】{excel_name_without_ext}"
                            body = f"Dear all,\n\n请查收 {subject}。"

                            # 发送邮件
                            sender = EmailSender()
                            logging.info(f"任务 {task_info['taskName']} 的 output_path: {output_path}")
                            try:
                                with open(output_path, 'rb') as attachment:
                                    part = MIMEBase('application', 'octet-stream')
                                    part.set_payload(attachment.read())
                                encoders.encode_base64(part)
                                
                                # 修改这里，使用更简单的方式处理中文文件名
                                filename = os.path.basename(output_path)
                                # 直接使用RFC 5987编码方式，不使用Header类
                                encoded_filename = urllib.parse.quote(filename)
                                part.add_header(
                                    'Content-Disposition',
                                    f'attachment; filename*=UTF-8\'\'{encoded_filename}'
                                )
                                
                                sender.send_email(
                                    subject=subject,
                                    recipients=recipients,
                                    body=body,
                                    attachments=[part]  # 这里传入的是MIMEBase对象
                                )
                                logging.info(f"任务 {task_info['taskName']} 邮件发送成功，收件人: {', '.join(recipients)}")
                            except Exception as e:
                                logging.error(f"任务 {task_info['taskName']} 邮件发送失败: {e}")
                        else:
                            logging.info(f"任务 {task_info['taskName']} 没有配置收件人，跳过邮件发送")
                    except Exception as e:
                        logging.error(f"任务 {task_info['taskName']} 邮件发送失败: {e}") # 这行重复了，删除
            except Exception as e:
                logging.error(f"任务 {task_info['taskName']} 数据库更新失败: {e}")
            finally:
                if cursor:
                    cursor.close()

        except Exception as e:
            logging.error(f"任务 {task_info['taskName']} 执行失败: {e}")
            # 更新数据库
            now = datetime.now()
            next_run_at = calculate_next_run_at(task_info['frequency'], task_info['dayOfMonth'], task_info['dayOfWeek'], task_info['time'])
            update_sql = "UPDATE autoreport_tasks SET last_run_at = %s, last_run_status = %s, last_run_log = %s, next_run_at = %s WHERE id = %s"
            update_values = (now, 'failure', str(e), next_run_at, task_info['id'])
            try:
                cursor = self.connection.cursor()
                cursor.execute(update_sql, update_values)
                self.connection.commit()
                logging.info(f"任务 {task_info['taskName']} 数据库更新失败: {e}")
            except Exception as e:
                logging.error(f"任务 {task_info['taskName']} 数据库更新失败: {e}")
            finally:
                if cursor:
                    cursor.close()

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
        self.close_connection()
        logging.info("定时任务调度器已停止")

    def close_connection(self):
        """关闭数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logging.info("数据库连接已关闭")

def calculate_next_run_at(frequency, day_of_month, day_of_week, time):
    """计算下一次执行的时间"""
    logging.info("calculate_next_run_at 函数被调用")
    logging.info(f"calculate_next_run_at called with: frequency={frequency}, day_of_month={day_of_month}, day_of_week={day_of_week}, time={time}")
    now = datetime.now()
    logging.info(f"当前时间: {now}")  # 添加当前时间日志
    if frequency == 'day':
        logging.info(f"frequency == 'day', now.date() = {now.date()}, time = {time}")
        next_run_at = datetime.combine(now.date(), datetime.strptime(time, '%H:%M').time())
        logging.info(f"frequency == 'day', next_run_at = {next_run_at}")
        if next_run_at <= now:
            logging.info(f"frequency == 'day', next_run_at <= now, next_run_at = {next_run_at}, now = {now}")
            next_run_at += timedelta(days=1)
        logging.info(f"frequency == 'day', 最终 next_run_at = {next_run_at}")  # 添加最终结果日志
    elif frequency == 'week':
        if day_of_week:
            weekday_map = {
                1: 0,  # Monday
                2: 1,  # Tuesday
                3: 2,  # Wednesday
                4: 3,  # Thursday
                5: 4,  # Friday
                6: 5,  # Saturday
                7: 6  # Sunday
            }
            target_weekday = weekday_map.get(int(day_of_week))
            logging.info(f"星期几 (0-6): {target_weekday}")
            
            # 先计算今天的目标时间
            today = now.date()
            target_time = datetime.strptime(time, '%H:%M').time()
            target_datetime = datetime.combine(today, target_time)
            
            # 如果是同一天，且目标时间还没到，就用今天的时间
            if now.weekday() == target_weekday and target_datetime > now:
                next_run_at = target_datetime
            else:
                # 否则计算到下一个目标星期几的天数
                days_ahead = target_weekday - now.weekday()
                if days_ahead <= 0:  # 如果已经过了本周的目标日期
                    days_ahead += 7
                next_run_at = datetime.combine((now + timedelta(days=days_ahead)).date(), target_time)
            
            logging.info(f"计算得到的下次执行时间: {next_run_at}")
    elif frequency == 'month':
        if day_of_month:
            try:
                day_of_month = int(day_of_month)
                logging.info(f"月份日期: {day_of_month}")
                
                # 先计算今天的目标时间
                target_time = datetime.strptime(time, '%H:%M').time()
                target_datetime = datetime.combine(now.date(), target_time)
                
                # 如果是目标日期当天，且目标时间还没到，就用今天的时间
                if now.day == day_of_month and target_datetime > now:
                    next_run_at = target_datetime
                else:
                    # 否则计算下个月的执行时间
                    if now.day > day_of_month or (now.day == day_of_month and target_datetime <= now):
                        # 如果今天的日期已经过了目标日期，或者是目标日期但时间已过，调度到下个月
                        month = now.month + 1
                        year = now.year
                        if month > 12:
                            month = 1
                            year += 1
                    else:
                        # 如果今天的日期还没到目标日期，调度到本月
                        month = now.month
                        year = now.year
                    
                    next_run_at = datetime(year, month, day_of_month, int(time[:2]), int(time[3:]))
                
                logging.info(f"计算得到的下次执行时间: {next_run_at}")
            except ValueError:
                # Handle invalid day_of_month
                # 获取当月的最后一天
                import calendar
                last_day = calendar.monthrange(now.year, now.month)[1]
                day_of_month = last_day
                next_run_at = datetime(now.year, now.month, day_of_month, int(time[:2]), int(time[3:]))
                if next_run_at <= now:
                    month = now.month + 1
                    year = now.year
                    if month > 12:
                        month = 1
                        year += 1
                    # 再次获取下个月的最后一天
                    last_day = calendar.monthrange(year, month)[1]
                    day_of_month = last_day
                    next_run_at = datetime(year, month, day_of_month, int(time[:2]), int(time[3:]))
        logging.info(f"frequency == 'month', 最终 next_run_at = {next_run_at}")  # 添加最终结果日志
    else:
        next_run_at = None

    logging.info(f"calculate_next_run_at returning: {next_run_at}")
    
    return next_run_at
