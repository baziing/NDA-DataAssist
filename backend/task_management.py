import logging
from datetime import datetime
import mysql.connector
from flask import request, jsonify

from backend.config import DB_CONFIG
from backend.task_scheduler import calculate_next_run_at

def register_task_management_routes(app, task_scheduler):
    """
    注册任务管理相关的路由
    
    参数:
        app: Flask应用实例
        task_scheduler: TaskScheduler实例，从report_api.py传入
    """
    
    @app.route('/task_management/tasks', methods=['GET'])
    def get_tasks_with_pagination():
        """获取所有任务，支持分页和筛选"""
        try:
            # 获取查询参数
            page = request.args.get('page', 1, type=int)
            page_size = request.args.get('pageSize', 20, type=int)
            game_type = request.args.get('gameType', '')
            task_name = request.args.get('taskName', '')
            frequency = request.args.get('frequency', '')
            day_of_week = request.args.get('dayOfWeek', '')
            day_of_month = request.args.get('dayOfMonth', '')
            
            # 构建查询条件
            conditions = []
            params = []
            
            if game_type:
                conditions.append("gameType = %s")
                params.append(game_type)
            
            if task_name:
                conditions.append("taskName LIKE %s")
                params.append(f"%{task_name}%")
            
            if frequency:
                conditions.append("frequency = %s")
                params.append(frequency)
            
            if day_of_week and frequency == 'week':
                conditions.append("dayOfWeek = %s")
                params.append(day_of_week)
            
            if day_of_month and frequency == 'month':
                conditions.append("dayOfMonth = %s")
                params.append(day_of_month)
            
            # 构建SQL查询
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # 连接数据库
            connection = mysql.connector.connect(**DB_CONFIG)
            cursor = connection.cursor(dictionary=True)
            
            # 获取总记录数
            count_sql = f"SELECT COUNT(*) as total FROM autoreport_tasks WHERE {where_clause}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total']
            
            # 获取分页数据
            offset = (page - 1) * page_size
            sql = f"""
                SELECT * FROM autoreport_tasks 
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(sql, params + [page_size, offset])
            tasks = cursor.fetchall()

            # 将 task_id 转换为字符串类型
            tasks = [{**task, 'id': str(task['id'])} for task in tasks]
            
            # 关闭数据库连接
            cursor.close()
            connection.close()
            
            return jsonify({
                'tasks': tasks,
                'total': total,
                'page': page,
                'pageSize': page_size
            }), 200
            
        except Exception as e:
            logging.error(f"获取任务列表失败: {str(e)}", exc_info=True)
            return jsonify({'error': f'获取任务列表失败: {str(e)}'}), 500

    @app.route('/task_management/task_sql/<string:task_id>', methods=['GET'])
    def get_task_sql(task_id):
        """获取指定任务的SQL信息"""
        try:
            print(f"获取任务SQL，任务ID: {task_id}")  # 添加调试信息
            
            # 连接数据库
            connection = mysql.connector.connect(**DB_CONFIG)
            cursor = connection.cursor(dictionary=True)
            
            # 查询SQL信息
            sql = """
                SELECT * FROM autoreport_templates
                WHERE task_id = %s
                ORDER BY sql_order
            """
            cursor.execute(sql, (str(task_id),))
            sql_data = cursor.fetchall()
            
            print(f"查询结果: {sql_data}")  # 添加调试信息
            
            # 关闭数据库连接
            cursor.close()
            connection.close()
            
            return jsonify(sql_data), 200
            
        except Exception as e:
            logging.error(f"获取任务SQL失败: {str(e)}", exc_info=True)
            print(f"获取任务SQL出错: {str(e)}")  # 添加调试信息
            return jsonify({'error': f'获取任务SQL失败: {str(e)}'}), 500

    @app.route('/task_management/task/<string:task_id>', methods=['GET'])
    def get_task(task_id):
        """获取指定任务的信息"""
        try:
            # 连接数据库
            connection = mysql.connector.connect(**DB_CONFIG)
            cursor = connection.cursor(dictionary=True)
            
            # 查询任务信息
            sql = """
                SELECT * FROM autoreport_tasks
                WHERE id = %s
            """
            cursor.execute(sql, (task_id,))
            task = cursor.fetchone()
            
            # 关闭数据库连接
            cursor.close()
            connection.close()
            
            if task is None:
                return jsonify({'error': '任务不存在'}), 404
            
            # 将 task_id 转换为字符串类型
            task['id'] = str(task['id'])
            
            return jsonify(task), 200
            
        except Exception as e:
            logging.error(f"获取任务信息失败: {str(e)}", exc_info=True)
            return jsonify({'error': f'获取任务信息失败: {str(e)}'}), 500

    @app.route('/task_management/task/<string:task_id>', methods=['PUT'])
    def update_task(task_id):
        """更新任务信息"""
        try:
            data = request.get_json()
            game_type = data.get('gameType')
            task_name = data.get('taskName')
            frequency = data.get('frequency')
            day_of_month = data.get('dayOfMonth')
            day_of_week = data.get('dayOfWeek')
            time = data.get('time')
            
            logging.info(f"更新任务 - 接收到的数据: {data}")
            
            if not game_type or not task_name or not frequency or not time:
                return jsonify({"message": "请填写所有必填项！"}), 400
            
            # 计算新的next_run_at
            next_run_at = calculate_next_run_at(frequency, day_of_month, day_of_week, time)
            logging.info(f"更新任务 - 计算出的 next_run_at: {next_run_at}")
            if next_run_at is None:
                return jsonify({"message": "计算下次运行时间失败"}), 500
            
            # 连接数据库
            try:
                connection = mysql.connector.connect(**DB_CONFIG)
                cursor = connection.cursor()
                logging.info("更新任务 - 数据库连接成功")
            except Exception as e:
                logging.error(f"更新任务 - 数据库连接失败: {str(e)}", exc_info=True)
                return jsonify({"message": f"数据库连接失败: {str(e)}"}), 500
            
            # 更新任务信息
            sql = """
                UPDATE autoreport_tasks
                SET gameType = %s, taskName = %s, frequency = %s, 
                    dayOfMonth = %s, dayOfWeek = %s, time = %s,
                    next_run_at = %s, last_modified_at = NOW()
                WHERE id = %s
            """
            values = (
                game_type, task_name, frequency,
                day_of_month if day_of_month else None,
                day_of_week if day_of_week else None,
                time, next_run_at, task_id
            )
            
            logging.info(f"更新任务 - SQL: {sql}, 参数: {values}")
            cursor.execute(sql, values)
            connection.commit()
            logging.info(f"更新任务 - 影响行数: {cursor.rowcount}")
            
            # 关闭数据库连接
            cursor.close()
            connection.close()
            
            # 重新加载任务
            task_scheduler.load_tasks()
            logging.info("更新任务 - 任务重新加载成功")
            
            return jsonify({"message": "任务更新成功！"}), 200
            
        except Exception as e:
            logging.error(f"更新任务失败: {str(e)}, data: {data}", exc_info=True)
            return jsonify({"message": f"更新任务失败: {str(e)}"}), 500

    @app.route('/task_management/task/<string:task_id>', methods=['DELETE'])
    def delete_task(task_id):
        """删除指定任务"""
        try:
            # 连接数据库
            connection = mysql.connector.connect(**DB_CONFIG)
            cursor = connection.cursor()
            
            # 开始事务
            connection.start_transaction()
            
            # 删除任务相关的SQL模板
            sql = "DELETE FROM autoreport_templates WHERE task_id = %s"
            cursor.execute(sql, (str(task_id),))
            
            # 删除任务
            sql = "DELETE FROM autoreport_tasks WHERE id = %s"
            cursor.execute(sql, (str(task_id),))
            
            # 提交事务
            connection.commit()
            
            # 关闭数据库连接
            cursor.close()
            connection.close()
            
            # 重新加载任务
            task_scheduler.load_tasks()
            
            return jsonify({"message": "任务删除成功！"}), 200
            
        except Exception as e:
            if connection and connection.is_connected():
                connection.rollback()
            logging.error(f"删除任务失败: {str(e)}", exc_info=True)
            return jsonify({"message": f"删除任务失败: {str(e)}"}), 500

    @app.route('/task_management/tasks/batch_delete', methods=['POST'])
    def batch_delete_tasks():
        """批量删除任务"""
        try:
            data = request.get_json()
            task_ids = data.get('taskIds', [])
            
            if not task_ids:
                return jsonify({"message": "未选择任何任务"}), 400
            
            # 确保所有任务ID都是字符串
            task_ids = [str(task_id) for task_id in task_ids]
            
            # 连接数据库
            connection = mysql.connector.connect(**DB_CONFIG)
            cursor = connection.cursor()
            
            # 开始事务
            connection.start_transaction()
            
            # 构建IN子句的参数占位符
            placeholders = ', '.join(['%s'] * len(task_ids))
            
            # 删除任务相关的SQL模板
            sql = f"DELETE FROM autoreport_templates WHERE task_id IN ({placeholders})"
            cursor.execute(sql, task_ids)
            
            # 删除任务
            sql = f"DELETE FROM autoreport_tasks WHERE id IN ({placeholders})"
            cursor.execute(sql, task_ids)
            
            # 提交事务
            connection.commit()
            
            # 关闭数据库连接
            cursor.close()
            connection.close()
            
            # 重新加载任务
            task_scheduler.load_tasks()
            
            return jsonify({"message": f"成功删除 {len(task_ids)} 个任务！"}), 200
            
        except Exception as e:
            if connection and connection.is_connected():
                connection.rollback()
            logging.error(f"批量删除任务失败: {str(e)}", exc_info=True)
            return jsonify({"message": f"批量删除任务失败: {str(e)}"}), 500
