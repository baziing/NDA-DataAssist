from flask import Flask, request, jsonify, send_file
from flask_cors import CORS  # 导入 CORS
import os
import sys
import uuid
import threading
import time
import logging
from datetime import datetime
import pandas as pd

from dotenv import load_dotenv
from pathlib import Path  # 导入 Path

dotenv_path = Path('.') / '.env.development'  # 指定 .env.development 文件的路径
load_dotenv(dotenv_path=dotenv_path)

# 将tools目录添加到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tools')))

# 导入report_generator.py中的函数和config模块
from report_generator_v2 import generate_report
from config import OUTPUT_DIR, DB_CONFIG
from report_task import ReportTask

app = Flask(__name__)
CORS(app)  # 启用 CORS

# 确保上传目录存在
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tmp'))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 创建 templates 和 variables 文件夹
TEMPLATES_FOLDER = os.path.join(UPLOAD_FOLDER, 'templates')
VARIABLES_FOLDER = os.path.join(UPLOAD_FOLDER, 'variables')
os.makedirs(TEMPLATES_FOLDER, exist_ok=True)
os.makedirs(VARIABLES_FOLDER, exist_ok=True)

# 存储任务的字典，key为uuid，value为ReportTask对象
tasks = {}

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
    return jsonify({'message': 'Report generation started', 'task_id': task_id}), 200

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
    # 尝试直接使用传入的文件名（包含日期目录）
    file_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')), filename)
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
    app.run(debug=True, port=int(os.environ.get('VUE_APP_API_PORT')))
