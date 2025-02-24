import logging
import os
import mysql.connector
from mysql.connector import Error
from backend.config import DB_CONFIG, LOG_CONFIG

def setup_logging():
    """
    配置日志
    """
    if not os.path.exists(LOG_CONFIG['log_dir']):
        os.makedirs(LOG_CONFIG['log_dir'])
    
    logging.basicConfig(
        filename=os.path.join(LOG_CONFIG['log_dir'], LOG_CONFIG['log_file']),
        level=LOG_CONFIG['log_level'],
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def connect_db():
    """
    连接MySQL数据库（使用默认配置）
    """
    return connect_db_with_config(DB_CONFIG)

def connect_db_with_config(db_config):
    """
    使用自定义配置连接MySQL数据库
    Args:
        db_config (dict): 数据库连接配置，包含host, port, user, password, database
    """
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            logging.info(f'成功连接数据库: {db_config["host"]}')
            return connection
    except Error as e:
        logging.error(f'数据库连接失败: {e}')
        raise

def execute_query(connection, query):
    """
    执行SQL查询
    """
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        return column_names, result
    except Error as e:
        logging.error(f'SQL查询失败: {e}')
        raise
    finally:
        if cursor:
            cursor.close()

def ensure_dir_exists(path):
    """
    确保目录存在，不存在则创建
    """
    if not os.path.exists(path):
        os.makedirs(path)
        logging.info(f'创建目录: {path}')
