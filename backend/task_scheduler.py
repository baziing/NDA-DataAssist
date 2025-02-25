import schedule
import time
import threading
import json
import os
import sys  # 导入 sys 模块
# import mysql.connector # 不需要直接导入
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from .report_generator_v2 import generate_report
import logging
from backend.config import DB_CONFIG
from backend.tools.excel_utils import check_excel_file
from backend.config.mail_config import MAIL_CONFIG
from backend.tools.mail.email_sender import EmailSender
from backend.utils import connect_db, execute_query  # 导入数据库连接函数

# 配置日志
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

# 生成带时间戳的日志文件名
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = os.path.join(log_dir, f'task_scheduler_{timestamp}.log')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
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
            return jsonify({"is_valid": False, "message": "游戏分类和任务名称不能为空"}), 400

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
        return jsonify({"is_valid": False, "message": f"An error occurred: {str(e)}"}), 500

@app.route('/create_task', methods=['POST'])
def create_task_api():
    """
    接收前端传递的任务信息，并将相关字段传入 `autoreport_templates` 表，并按照顺序给文件中的 SQL 排序传入 `sql_order` 字段。
    """
    try:
        data = request.get_json()
        filename = data.get('filename')
        game_type = data.get('gameType')
        task_name = data.get('taskName')
        frequency = data.get('frequency')
        day_of_month = data.get('dayOfMonth')
        day_of_week = data.get('dayOfWeek')
        time = data.get('time')

        if not filename or not game_type or not task_name or not frequency or not time:
            return jsonify({"message": "请填写所有必填项！"}), 400

        # 文件上传路径
        upload_dir = 'input_files'
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)

        # 从 Excel 文件中读取 SQL 语句
        try:
            excel_result = check_excel_file(file_path)
            if not excel_result['is_valid']:
                return jsonify({"message": f"读取 Excel 文件失败: {excel_result['message']}"}), 500
            sql_list = excel_result['sql_list']
        except Exception as e:
            logging.error(f"读取 Excel 文件失败: {str(e)}", exc_info=True)
            return jsonify({"message": f"读取 Excel 文件失败: {str(e)}"}), 500

        # 验证 SQL 语句的有效性
        # 验证 SQL 语句的有效性
        import sqlparse
        for sql_dict in sql_list:
            try:
                sql = sql_dict['output_sql']
                logging.info(f"正在校验的 SQL 语句：{sql}")  # 添加详细日志
                sqlparse.parse(sql)
            except Exception as e:
                logging.error(f"SQL 校验失败，sql_dict: {sql_dict}, 错误信息: {str(e)}", exc_info=True)
                return jsonify({"message": f"SQL 语句无效: {str(e)}"}), 500

        # 将相关字段传入 `autoreport_templates` 表，并按照顺序给文件中的 SQL 排序传入 `sql_order` 字段
        db_config = app.config['DB_CONFIG']
        connection = None  # 初始化 connection 为 None
        cursor = None
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()

            # 开始事务
            connection.start_transaction()

            # 插入 autoreport_tasks 表
            sql = "INSERT INTO autoreport_tasks (original_filename, gameType, taskName, frequency, dayOfMonth, dayOfWeek, time) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            values = (filename, game_type, task_name, frequency, day_of_month, day_of_week, time)
            cursor.execute(sql, values)
            task_id = cursor.lastrowid

            # 插入模板信息
            sql_order = 1
            for row in excel_result['sql_list']:
                sql = "INSERT INTO autoreport_templates (task_id, db_name, output_sql, sql_order, transpose) VALUES (%s, %s, %s, %s, %s)"
                values = (int(task_id), row['db_name'], row['output_sql'], sql_order, False)
                cursor.execute(sql, values)
                sql_order += 1

            # 提交事务
            connection.commit()
            return jsonify({"message": "任务创建成功！"}), 200

        except Exception as e:
            if connection and connection.is_connected():
                connection.rollback()  # 回滚事务
            logging.error(f"插入 autoreport_templates 失败，当前 sql_statement: {sql_statement}, 错误信息: {str(e)}", exc_info=True)
            return jsonify({"message": f"数据库操作失败: {str(e)}"}), 500

        finally:
            # 从 finally 块中移除关闭连接的代码
            if connection and connection.is_connected():
                if cursor:
                    cursor.close()
            # connection.close()  # 注释掉这行代码

    except Exception as e:
        if connection and connection.is_connected():
            connection.rollback()
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
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
            cursor.execute("SELECT * FROM autoreport_tasks")
            tasks = cursor.fetchall()
            for task in tasks:
                try:
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
        """安排任务"""
        job = None
        if task_info['frequency'] == 'day':
            job = self.scheduler.every().day.at(task_info['time'])
        elif task_info['frequency'] == 'week':
            if task_info['dayOfWeek']:
                # schedule库的周几从0开始，0=周一，1=周二，...，6=周日
                weekday_map = {
                    1: 'monday',
                    2: 'tuesday',
                    3: 'wednesday',
                    4: 'thursday',
                    5: 'friday',
                    6: 'saturday',
                    7: 'sunday',
                }
                day_of_week = weekday_map.get(int(task_info['dayOfWeek']))
                if day_of_week:
                    job = getattr(self.scheduler.every(), day_of_week).at(task_info['time'])
        elif task_info['frequency'] == 'month':
            if task_info['dayOfMonth']:
                job = self.scheduler.every(int(task_info['dayOfMonth'])).days.at(task_info['time'])
        if job is not None:
            job.do(self.run_task, task_info)

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
        self.close_connection()
        logging.info("定时任务调度器已停止")

    def close_connection(self):
        """关闭数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logging.info("数据库连接已关闭")
