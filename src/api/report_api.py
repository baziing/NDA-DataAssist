from flask import Flask, request, jsonify, send_file
from flask_cors import CORS  # 导入 CORS
import os
import sys
import uuid
import threading
import time
import logging
from datetime import datetime

# 将tools目录添加到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tools')))

# 导入report_generator.py中的函数和config模块
from report_generator import process_single_file
from config import OUTPUT_DIR, DB_CONFIG
from report_task import ReportTask

app = Flask(__name__)
CORS(app)  # 启用 CORS

# 确保上传目录存在
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tmp', 'uploads'))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 存储任务的字典，key为uuid，value为ReportTask对象
tasks = {}

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        # 生成唯一文件名
        filename = str(uuid.uuid4()) + '.xlsx'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({'message': 'File uploaded successfully', 'filename': filename, 'original_filename': file.filename }), 200

@app.route('/generate', methods=['POST'])
def generate_report_route():
    data = request.get_json()
    filename = data.get('filename') # 获取的是uuid生成的文件名
    original_filename = data.get('original_filename')  # 获取原始文件名
    if not filename:
        return jsonify({'error': 'No filename provided'}), 400
    # 使用original_filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    # 创建一个uuid作为task_id
    task_id = str(uuid.uuid4())
    task = ReportTask(filepath, original_filename) # 传递 original_filename
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

if __name__ == '__main__':
    app.run(debug=True)
