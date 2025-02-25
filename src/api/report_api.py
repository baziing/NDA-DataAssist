import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import uuid
import threading
import time
import logging
from datetime import datetime
import pandas as pd

from dotenv import load_dotenv
from pathlib import Path
dotenv_path = Path('.') / '.env.development'
load_dotenv(dotenv_path=dotenv_path)

from backend.config import OUTPUT_DIR, DB_CONFIG
from backend.report_task import ReportTask
from backend.task_scheduler import TaskScheduler  # 导入 TaskScheduler
from backend.tools.excel_utils import check_excel_file
from backend.utils import connect_db, execute_query
import sqlparse
import mysql.connector

app = Flask(__name__, static_folder='../../dist', static_url_path='/')
CORS(app)

# 数据库配置
app.config['DB_CONFIG'] = DB_CONFIG

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
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(file_path)

        # 调用 check_excel_file 函数进行校验
        result = check_excel_file(file_path)

        # 删除临时文件
        os.remove(file_path)

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"is_valid": False, "message": f"An error occurred: {str(e)}"}), 500
@app.route('/check_task_name', methods=['POST'])
def check_task_name():
    """检查任务名称是否重名"""
    data = request.get_json()
    game_type = data.get('gameType')
    task_name = data.get('taskName')

    if not game_type or not task_name:
        return jsonify({'is_valid': False, 'message': '游戏分类和任务名称不能为空'}), 400

    tasks = task_scheduler.get_tasks()
    for task in tasks:
        if task['gameType'] == game_type and task['taskName'] == task_name:
            return jsonify({'is_valid': False, 'message': '任务名称已存在'}), 200

    return jsonify({'is_valid': True}), 200

@app.route('/get_tasks', methods=['GET'])
def get_tasks_api():
    """获取所有任务"""
    try:
        tasks = task_scheduler.get_tasks()
        return jsonify(tasks), 200
    except Exception as e:
        return jsonify({'error': f'获取任务失败: {str(e)}'}), 500

@app.route('/check_sql', methods=['POST'])
def check_sql():
    """检查 SQL 语句的有效性"""
    data = request.get_json()
    filename = data.get('filename')

    if not filename:
        return jsonify({'is_valid': False, 'message': '未提供文件名'}), 400

    # 文件上传路径
    file_path = os.path.join(TEMPLATES_FOLDER, filename)
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return jsonify({'is_valid': False, 'message': '文件不存在'}), 400
    # 从 Excel 文件中读取 SQL 语句
    try:
        excel_result = check_excel_file(file_path)
        if not excel_result['is_valid']:
            return jsonify({"is_valid": False, "message": f"读取 Excel 文件失败: {excel_result['message']}"}), 400
        sql_list = excel_result['sql_list']
    except Exception as e:
        return jsonify({"is_valid": False, "message": f"读取 Excel 文件失败: {str(e)}"}), 400

    # 验证 SQL 语句的有效性
    for sql_dict in sql_list:
        try:
            sql = sql_dict['output_sql']
            logging.info(f"正在校验的 SQL 语句：{sql}")  # 添加详细日志
            sqlparse.parse(sql)
        except Exception as e:
            logging.error(f"SQL 校验失败，sql_dict: {sql_dict}, 错误信息: {str(e)}") # 添加详细日志
            return jsonify({"is_valid": False, "message": f"SQL 语句无效: {str(e)}"}), 400

    return jsonify({'is_valid': True}), 200

# 确保上传目录存在
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tmp'))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 创建 templates 和 variables 文件夹
TEMPLATES_FOLDER = os.path.join(UPLOAD_FOLDER, 'templates')
VARIABLES_FOLDER = os.path.join(UPLOAD_FOLDER, 'variables')
os.makedirs(TEMPLATES_FOLDER, exist_ok=True)
os.makedirs(VARIABLES_FOLDER, exist_ok=True)

# 创建 TaskScheduler 实例,TaskScheduler的构造函数会自动连接数据库
task_scheduler = TaskScheduler()

@app.route('/')
def index():
    return app.send_static_file('index.html')

tasks = {}

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
        # upload_dir = 'input_files'
        # os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(TEMPLATES_FOLDER, data['uuidFileName'])

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
        sql_statement = None # 初始化
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()

            # 开始事务
            connection.start_transaction()

            # 插入 autoreport_tasks 表
            # 插入 autoreport_tasks 表
            sql = "INSERT INTO autoreport_tasks (gameType, taskName, frequency, dayOfMonth, dayOfWeek, `time`) VALUES (%s, %s, %s, %s, %s, %s)"
            values = (
                game_type,
                task_name,
                frequency,
                day_of_month if day_of_month else None,
                day_of_week if day_of_week else None,
                time
            )
            cursor.execute(sql, values)
            task_id = cursor.lastrowid

            # 插入模板信息
            sql_order = 1
            for row in excel_result['sql_list']:
                sql = "INSERT INTO autoreport_templates (task_id, db_name, output_sql, sql_order, transpose, format, pos) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                values = (str(task_id), row['db_name'], row['output_sql'], sql_order, row.get('transpose', False), row.get('format'), row.get('pos'))
                cursor.execute(sql, values)
                sql_order += 1

            # 提交事务
            connection.commit()

            # 重新加载任务
            task_scheduler.load_tasks()

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
        connection = None # 确保连接未建立时也能回滚
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        # 生成唯一文件名
        filename = str(uuid.uuid4()) + '.xlsx'
        filepath = os.path.join(TEMPLATES_FOLDER, filename)
        file.save(filepath)
        print(f"File saved to: {filepath}") # 打印文件保存路径

        # 检查模板文件格式
        try:
            df = pd.read_excel(filepath)
            required_columns = ['db_name', 'output_sql']
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f'Invalid template format. Expected columns: {required_columns}')
        except Exception as e:
            os.remove(filepath)  # 格式错误时删除上传的文件
            return jsonify({'error': f'Error processing template file: {str(e)}'}), 400

        return jsonify({'message': 'File uploaded successfully', 'filename': filename, 'original_filename': file.filename }), 200
    else:
        return jsonify({'error': 'Invalid file type'}), 400


@app.route('/generate', methods=['POST'])
def generate_report_route():
    data = request.get_json()
    filename = data.get('filename')  # 获取的是uuid生成的文件名
    original_filename = data.get('original_filename')  # 获取原始文件名
    if not filename:
        return jsonify({'error': 'No filename provided'}), 400

    # 尝试从 templates 文件夹中查找文件
    filepath = os.path.join(TEMPLATES_FOLDER, filename)
    if os.path.exists(filepath):
        pass  # 文件存在，使用该路径
    else:
        # 尝试从 variables 文件夹中查找文件
        filepath = os.path.join(VARIABLES_FOLDER, filename)
        if os.path.exists(filepath):
            pass  # 文件存在，使用该路径
        else:
            return jsonify({'error': 'File not found'}), 404

    # 创建一个uuid作为task_id
    task_id = str(uuid.uuid4())
    variables_filename = data.get('variables_filename')
    task = ReportTask(filepath, original_filename, variables_filename)  # 传递 original_filename
    tasks[task_id] = task
    task.start()
    return jsonify({'message': 'Report generation started', 'task_id': task_id, 'original_filename': original_filename}), 200

@app.route('/progress/<task_id>', methods=['GET'])
def get_progress(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    status = task.get_status()
    if status['output_file']:
        status['output_filename'] = os.path.basename(status['output_file']) # 提取文件名
    # 在这里添加文件大小
    if status['output_file_size']:
      status['output_file_size'] = status['output_file_size']
    return jsonify(status), 200

@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    # 使用传入的文件名（包含日期目录），output作为根目录
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    file_path = os.path.join(project_root, 'output', filename)
    if not os.path.exists(file_path):
      return jsonify({'error': 'File not found'}), 404

    # 使用send_file发送文件
    try:
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': f'下载失败: {str(e)}'}), 500

@app.route('/reset/<task_id>', methods=['POST'])
def reset_task(task_id):
    task = tasks.get(task_id)
    if task:
        task.cancel()  # 取消任务（需要添加到 ReportTask 类）
        return jsonify({'message': f'Task {task_id} reset successfully'}), 200
    else:
        return jsonify({'error': 'Task not found'}), 404

# 定义全局变量
ALLOWED_EXTENSIONS = {'xlsx'}

# 检查文件扩展名是否合法
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_vars', methods=['POST'])
def upload_vars():
    print("Request headers:", request.headers) # 打印请求头
    if 'file' not in request.files:
        print("No file part in request.files")
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    print("File received:", file.filename) # 打印文件名
    if file.filename == '':
        print("No selected file")
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        # 生成唯一文件名
        filename = str(uuid.uuid4()) + '.xlsx'
        filepath = os.path.join(VARIABLES_FOLDER, filename)
        file.save(filepath)

        print(f"File saved to: {filepath}") # 打印文件保存路径

        # 打印文件的 MIME 类型（如果可以获取）
        if file.content_type:
            print(f"File MIME type: {file.content_type}")

        # 解析变量文件
        try:
            print(f"Filepath before read_excel: {filepath}")  # 打印 filepath 的值
            variables = []
            df = pd.read_excel(filepath)
            # 检查列名是否存在，并且转换为小写
            expected_columns = ['key', 'value']
            actual_columns = [col.lower() for col in df.columns]
            print("Actual columns:", actual_columns) # 打印实际列名
            if not all(col in actual_columns for col in expected_columns):
                raise ValueError(f'Invalid file format. Expected columns: {expected_columns}')
            # 提取 key 和 value 列
            keys = []
            for index, row in df.iterrows():
              key = row['key']
              value = row['value']
              keys.append(str(key))
              variables.append({'key': str(key), 'value': str(value)})

            # 检查是否有重复的 key
            if len(keys) != len(set(keys)):
                duplicates = [key for key in keys if keys.count(key) > 1]
                raise ValueError(f'Duplicate keys found: {", ".join(duplicates)}')

            return jsonify({'message': 'File uploaded and variables extracted successfully', 'variables': variables, 'filename': filename}), 200 #增加filename返回
        except Exception as e:
            print(f"Error processing file: {e}") # 打印详细错误
            print(f"Exception type: {type(e)}")  # 打印异常类型
            print(f"Exception args: {e.args}")  # 打印异常参数
            return jsonify({'error': f'Error processing file: {str(e)}'}), 400  # 更详细的错误信息
    else:
        return jsonify({'error': 'Invalid file type'}), 400
        
if __name__ == '__main__':
    # 创建并启动调度器线程
    scheduler_thread = threading.Thread(target=task_scheduler.start)
    scheduler_thread.daemon = True  # 设置为守护线程，以便主线程退出时自动退出
    scheduler_thread.start()

    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('VUE_APP_API_PORT')))
