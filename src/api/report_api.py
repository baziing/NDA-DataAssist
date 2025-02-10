from flask import Flask, request, jsonify
from flask_cors import CORS  # 导入 CORS
import os
import sys
import uuid
import os

# 将tools目录添加到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tools')))

# 导入report_generator.py中的函数和config模块
from report_generator import process_single_file
from config import OUTPUT_DIR, DB_CONFIG

app = Flask(__name__)
CORS(app)  # 启用 CORS

# 确保上传目录存在
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tmp', 'uploads'))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
        
        # 调用report_generator.py中的函数处理文件
        try:
            # 临时修改输出目录
            original_output_dir = OUTPUT_DIR['report']
            OUTPUT_DIR['report'] = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'output'))
            process_single_file(filepath)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            # 恢复输出目录
            OUTPUT_DIR['report'] = original_output_dir
        return jsonify({'message': 'File uploaded and processed successfully'}), 200

if __name__ == '__main__':
    app.run(debug=True)