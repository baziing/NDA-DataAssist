import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_DATABASE')
}

# 邮件配置
EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER'),
    'smtp_port': int(os.getenv('SMTP_PORT', 465)),
    'sender_email': os.getenv('MAIL_USERNAME'),
    'sender_password': os.getenv('MAIL_PASSWORD'),
    # 添加用户组
    'user_groups': {
        
    }
}

# 文件路径配置
INPUT_DIR = {
    'report': 'input_files',
    'format': 'tools/format/input'
}

OUTPUT_DIR = {
    'report': 'output_files',
    'format': 'tools/format/output'
}

# 日志配置
LOG_CONFIG = {
    'log_dir': 'logs',
    'log_file': 'autoreport.log',
    'log_level': 'INFO'
}
