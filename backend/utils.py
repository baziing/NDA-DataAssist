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
        connection = mysql.connector.connect(autocommit=False, **db_config)
        if connection.is_connected():
            logging.info(f'成功连接数据库: {db_config["host"]}')
            return connection
    except Error as e:
        logging.error(f'数据库连接失败: {e}')
        raise

def execute_query(connection, query):
    """
    执行SQL查询，支持大型SQL语句
    """
    try:
        # 修改连接设置以支持大型查询
        connection.set_charset_collation('utf8mb4', 'utf8mb4_general_ci')
        
        # 使用会话级别的设置来提高大型SQL的兼容性
        with connection.cursor() as config_cursor:
            try:
                # 设置会话级别参数，不影响全局设置
                config_cursor.execute("SET SESSION net_read_timeout=3600")  # 1小时
                config_cursor.execute("SET SESSION max_execution_time=3600000")  # 1小时(毫秒)
                config_cursor.execute("SET SESSION max_allowed_packet=1073741824")  # 1GB (注意：实际上这是无效的，仅为完整性)
            except Exception as e:
                logging.warning(f"设置会话参数失败: {e}")
                
        cursor = connection.cursor()
        
        # 记录SQL长度
        sql_length = len(query)
        if sql_length > 100000:
            logging.info(f"执行长SQL查询, 长度: {sql_length} 字符")
        elif sql_length > 10000:
            logging.info(f"执行中等长度SQL查询, 长度: {sql_length} 字符")
        
        # 执行查询
        multi = False
        if ";" in query and not query.strip().endswith(';'):
            multi = True  # 如果查询包含多个语句，使用multi=True
            
        cursor.execute(query, multi=multi)
        
        result = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        return column_names, result
    except Error as e:
        logging.error(f'SQL查询失败: {e}')
        # 记录更多信息以便调试
        logging.error(f'SQL长度: {len(query)} 字符')
        
        # 将长SQL片段保存到单独的文件
        if len(query) > 1000:
            try:
                import os
                from datetime import datetime
                error_log_dir = os.path.join('logs', 'sql_errors')
                os.makedirs(error_log_dir, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                error_log_file = os.path.join(error_log_dir, f'sql_error_utils_{timestamp}.sql')
                
                with open(error_log_file, 'w', encoding='utf-8') as f:
                    f.write(f"-- 错误信息: {str(e)}\n")
                    f.write(f"-- SQL长度: {len(query)} 字符\n")
                    f.write(f"-- 时间: {timestamp}\n\n")
                    f.write(query)
                
                logging.error(f'完整SQL已保存到: {error_log_file}')
            except Exception as log_error:
                logging.error(f'保存SQL日志失败: {log_error}')
        else:
            # 只记录查询的前100个和后100个字符
            logging.error(f'SQL前100字符: {query[:100]}')
            logging.error(f'SQL后100字符: {query[-100:]}')
        
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
