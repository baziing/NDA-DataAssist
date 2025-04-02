"""
Routes for handling Dify requests
"""
from flask import request, jsonify
import pymysql
import logging
from ..config import DB_CONFIG
from flask_cors import cross_origin

def register_dify_routes(app):
    @app.route('/api/dify/query', methods=['POST'])
    @cross_origin()  # 添加CORS支持
    def handle_dify_query():
        """处理POST请求以执行SQL查询"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No JSON data received"}), 400
                
            sql_queries = data.get('sql_query')
            if not sql_queries:
                return jsonify({"error": "Missing sql_query parameter"}), 400

            app.logger.info(f"Received query: {sql_queries}")  # 添加日志

            # 使用配置文件中的数据库连接信息
            conn = None
            cursor = None
            try:
                conn = pymysql.connect(
                    host=DB_CONFIG['host'],
                    user=DB_CONFIG['user'],
                    password=DB_CONFIG['password'],
                    database=DB_CONFIG['database'],
                    port=DB_CONFIG['port'],
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor
                )

                cursor = conn.cursor()

                # 分割SQL语句并逐个执行
                for sql_query in sql_queries.split(';'):
                    if sql_query.strip():
                        app.logger.info(f"Executing query: {sql_query.strip()}")  # 添加日志
                        cursor.execute(sql_query)

                # 获取结果
                results = cursor.fetchall()
                app.logger.info(f"Query results: {results}")  # 添加日志

                return jsonify(results), 200

            except Exception as e:
                app.logger.error(f"Database error: {str(e)}")  # 添加详细错误日志
                return jsonify({"error": f"Database error: {str(e)}"}), 500

            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()

        except Exception as e:
            app.logger.error(f"Request processing error: {str(e)}")  # 添加详细错误日志
            return jsonify({"error": str(e)}), 500

    @app.route('/api/dify/health', methods=['GET'])
    @cross_origin()  # 添加CORS支持
    def dify_health_check():
        """健康检查端点"""
        return jsonify({'status': 'ok'}) 