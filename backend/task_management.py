import logging
from datetime import datetime
import mysql.connector
from flask import request, jsonify, send_file, Response, send_from_directory
import os

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

    @app.route('/task_management/task_recipients/<string:task_id>', methods=['GET'])
    def get_task_recipients(task_id):
        """获取任务的收件人信息"""
        try:
            logging.info(f"获取任务收件人信息，任务ID: {task_id}")
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)
            
            # 查询任务收件人 - 使用正确的表名 autoreport_tasks
            try:
                cursor.execute(
                    "SELECT id FROM autoreport_tasks WHERE id = %s",
                    (task_id,)
                )
                
                task = cursor.fetchone()
                
                if not task:
                    logging.warning(f"任务不存在，ID: {task_id}")
                    return jsonify({"recipients": [], "warning": "任务不存在"}), 200
                
                # 查询任务收件人关联表
                cursor.execute(
                    """
                    SELECT 
                        tr.id, 
                        CASE 
                            WHEN tr.email_id IS NOT NULL THEN CONCAT('email-', tr.email_id) 
                            WHEN tr.group_id IS NOT NULL THEN CONCAT('group-', tr.group_id)
                        END as recipient_id
                    FROM autoreport_task_recipients tr
                    WHERE tr.task_id = %s
                    """,
                    (task_id,)
                )
                
                recipients = cursor.fetchall()
                recipients_list = [r['recipient_id'] for r in recipients if r['recipient_id']]
                
            except mysql.connector.Error as db_err:
                # 如果是表不存在错误，尝试旧的方式
                if db_err.errno == 1146:  # 表不存在错误码
                    logging.warning(f"表不存在，尝试使用旧方式: {str(db_err)}")
                    return jsonify({"recipients": [], "warning": "数据库结构需要更新"}), 200
                else:
                    raise
            
            cursor.close()
            conn.close()
            
            logging.info(f"成功获取任务收件人，任务ID: {task_id}, 收件人数量: {len(recipients_list)}")
            return jsonify({"recipients": recipients_list})
            
        except Exception as e:
            logging.error(f"获取任务收件人失败: {str(e)}")
            # 返回空列表而不是错误，避免前端崩溃
            return jsonify({"recipients": [], "error": str(e)}), 200
    
    @app.route('/task_management/task_recipients/<string:task_id>', methods=['PUT'])
    def update_task_recipients(task_id):
        """更新任务的收件人信息"""
        try:
            logging.info(f"更新任务收件人信息，任务ID: {task_id}")
            data = request.json
            recipients = data.get('recipients', [])
            
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            try:
                # 首先检查任务是否存在
                cursor.execute(
                    "SELECT id FROM autoreport_tasks WHERE id = %s",
                    (task_id,)
                )
                
                if not cursor.fetchone():
                    logging.warning(f"任务不存在，无法更新收件人，ID: {task_id}")
                    return jsonify({"warning": "任务不存在"}), 404
                
                # 删除现有的收件人关联
                cursor.execute(
                    "DELETE FROM autoreport_task_recipients WHERE task_id = %s",
                    (task_id,)
                )
                
                # 添加新的收件人关联
                for recipient in recipients:
                    if recipient.startswith('email-'):
                        email_id = recipient.replace('email-', '')
                        cursor.execute(
                            "INSERT INTO autoreport_task_recipients (task_id, email_id, created_at, updated_at) VALUES (%s, %s, NOW(), NOW())",
                            (task_id, email_id)
                        )
                    elif recipient.startswith('group-'):
                        group_id = recipient.replace('group-', '')
                        cursor.execute(
                            "INSERT INTO autoreport_task_recipients (task_id, group_id, created_at, updated_at) VALUES (%s, %s, NOW(), NOW())",
                            (task_id, group_id)
                        )
                
                # 更新任务的最后修改时间
                cursor.execute(
                    "UPDATE autoreport_tasks SET last_modified_at = NOW() WHERE id = %s",
                    (task_id,)
                )
                
            except mysql.connector.Error as db_err:
                # 如果是表不存在错误，尝试旧的方式
                if db_err.errno == 1146:  # 表不存在错误码
                    logging.warning(f"表不存在，尝试使用旧方式: {str(db_err)}")
                    # 将收件人列表转换为逗号分隔的字符串，兼容旧版本
                    recipients_str = ','.join(recipients) if recipients else ''
                    try:
                        cursor.execute(
                            "UPDATE tasks SET recipients = %s, last_modified_at = NOW() WHERE id = %s",
                            (recipients_str, task_id)
                        )
                    except Exception as e:
                        logging.error(f"使用旧方式更新收件人失败: {str(e)}")
                        return jsonify({"error": "数据库结构需要更新，无法保存收件人"}), 200
                else:
                    raise
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logging.info(f"成功更新任务收件人，任务ID: {task_id}, 收件人数量: {len(recipients)}")
            return jsonify({"message": "收件人更新成功"})
            
        except Exception as e:
            logging.error(f"更新任务收件人失败: {str(e)}")
            return jsonify({"error": f"更新任务收件人失败: {str(e)}"}), 200

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
            connection = mysql.connector.connect( **DB_CONFIG)
            cursor = connection.cursor(dictionary=True)
            
            # 查询任务信息
            sql = """
                SELECT * FROM autoreport_tasks
                WHERE id = %s
            """
            cursor.execute(sql, (task_id,))
            task = cursor.fetchone()
            
            if task is None:
                cursor.close()
                connection.close()
                return jsonify({'error': '任务不存在'}), 404
            
            # 将 task_id 转换为字符串类型
            task['id'] = str(task['id'])
            
            # 查询任务的收件人信息
            recipients = []
            
            # 查询关联的邮件组
            sql = """
                SELECT g.id, g.group_name, 'group' as type
                FROM autoreport_email_groups g
                JOIN autoreport_task_recipients tr ON g.id = tr.group_id
                WHERE tr.task_id = %s
            """
            cursor.execute(sql, (task_id,))
            email_groups = cursor.fetchall()
            
            # 查询关联的个人邮件
            sql = """
                SELECT e.id, e.email, 'email' as type
                FROM autoreport_emails e
                JOIN autoreport_task_recipients tr ON e.id = tr.email_id
                WHERE tr.task_id = %s
            """
            cursor.execute(sql, (task_id,))
            emails = cursor.fetchall()
            
            # 合并收件人信息
            for group in email_groups:
                recipients.append({
                    'id': f"group-{group['id']}",
                    'name': group['group_name'],
                    'type': 'group'
                })
                
            for email in emails:
                recipients.append({
                    'id': f"email-{email['id']}",
                    'email': email['email'],
                    'type': 'email'
                })
            
            # 将收件人信息添加到任务中
            task['recipients'] = recipients
            
            # 关闭数据库连接
            cursor.close()
            connection.close()
            
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
            is_enabled = data.get('isEnabled', True)
            recipients = data.get('recipients', [])  # 获取收件人列表
            
            logging.info(f"更新任务 - 接收到的数据: {data}")
            
            if not game_type or not task_name or not frequency or not time:
                return jsonify({"message": "请填写所有必填项！"}), 400
            
            # 连接数据库获取当前任务状态
            connection = mysql.connector.connect(**DB_CONFIG)
            cursor = connection.cursor(dictionary=True)
            
            # 查询当前任务状态
            cursor.execute("SELECT is_enabled FROM autoreport_tasks WHERE id = %s", (task_id,))
            current_task = cursor.fetchone()
            
            if not current_task:
                cursor.close()
                connection.close()
                return jsonify({"message": "任务不存在"}), 404
            
            # 检查调度状态是否变化
            is_enabled_changed = current_task['is_enabled'] != (1 if is_enabled else 0)
            
            # 计算新的next_run_at
            next_run_at = None
            if is_enabled:  # 只有在启用状态下才计算下次运行时间
                next_run_at = calculate_next_run_at(frequency, day_of_month, day_of_week, time)
                logging.info(f"更新任务 - 计算出的 next_run_at: {next_run_at}")
                if next_run_at is None and is_enabled:
                    cursor.close()
                    connection.close()
                    return jsonify({"message": "计算下次运行时间失败"}), 500
            
            # 开始事务
            connection.start_transaction()
            
            try:
                # 更新任务信息
                sql = """
                    UPDATE autoreport_tasks
                    SET gameType = %s, taskName = %s, frequency = %s, 
                        dayOfMonth = %s, dayOfWeek = %s, time = %s,
                        next_run_at = %s, last_modified_at = NOW(),
                        is_enabled = %s
                    WHERE id = %s
                """
                values = (
                    game_type, task_name, frequency,
                    day_of_month if day_of_month else None,
                    day_of_week if day_of_week else None,
                    time, next_run_at, is_enabled, task_id
                )
                
                logging.info(f"更新任务 - SQL: {sql}, 参数: {values}")
                cursor.execute(sql, values)
                
                # 更新收件人信息
                # 先删除现有的收件人关联
                sql = "DELETE FROM autoreport_task_recipients WHERE task_id = %s"
                cursor.execute(sql, (task_id,))
                
                # 添加新的收件人关联
                if recipients:
                    for recipient in recipients:
                        # 解析收件人ID和类型（邮件组或个人邮件）
                        recipient_parts = recipient.split('-')
                        if len(recipient_parts) == 2:
                            recipient_type, recipient_id = recipient_parts
                            
                            if recipient_type == 'group':
                                # 添加邮件组关联
                                sql = "INSERT INTO autoreport_task_recipients (task_id, group_id) VALUES (%s, %s)"
                                values = (task_id, recipient_id)
                                cursor.execute(sql, values)
                            elif recipient_type == 'email':
                                # 添加个人邮件关联
                                sql = "INSERT INTO autoreport_task_recipients (task_id, email_id) VALUES (%s, %s)"
                                values = (task_id, recipient_id)
                                cursor.execute(sql, values)
                
                # 提交事务
                connection.commit()
                logging.info(f"更新任务 - 影响行数: {cursor.rowcount}")
                
            except Exception as e:
                # 回滚事务
                connection.rollback()
                logging.error(f"更新任务失败: {str(e)}", exc_info=True)
                cursor.close()
                connection.close()
                return jsonify({"message": f"更新任务失败: {str(e)}"}), 500
            
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
            
            try:
                # 删除任务相关的收件人关联
                sql = "DELETE FROM autoreport_task_recipients WHERE task_id = %s"
                cursor.execute(sql, (str(task_id),))
                
                # 删除任务相关的SQL模板
                sql = "DELETE FROM autoreport_templates WHERE task_id = %s"
                cursor.execute(sql, (str(task_id),))
                
                # 删除任务
                sql = "DELETE FROM autoreport_tasks WHERE id = %s"
                cursor.execute(sql, (str(task_id),))
                
                # 提交事务
                connection.commit()
                
                # 重新加载任务
                task_scheduler.load_tasks()
                
                return jsonify({"message": "任务删除成功！"}), 200
                
            except Exception as e:
                # 回滚事务
                connection.rollback()
                logging.error(f"删除任务失败: {str(e)}", exc_info=True)
                return jsonify({"message": f"删除任务失败: {str(e)}"}), 500
                
            finally:
                # 关闭数据库连接
                cursor.close()
                connection.close()
            
        except Exception as e:
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
            connection = None
            cursor = None
            try:
                connection = mysql.connector.connect(**DB_CONFIG)
                cursor = connection.cursor()
                logging.info("批量删除任务 - 数据库连接成功")
                
                # 开始事务
                connection.start_transaction()
                
                # 更新任务信息
                placeholders = ', '.join(['%s'] * len(task_ids))
                
                # 删除任务相关的收件人关联
                sql = f"DELETE FROM autoreport_task_recipients WHERE task_id IN ({placeholders})"
                cursor.execute(sql, task_ids)
                
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
                
            finally:
                if connection and connection.is_connected():
                    if cursor:
                        cursor.close()
                    connection.close()
                
        except Exception as e:
            logging.error(f"批量删除任务失败: {str(e)}", exc_info=True)
            return jsonify({"message": f"批量删除任务失败: {str(e)}"}), 500

    @app.route('/task_management/task_files/<string:task_id>', methods=['GET'])
    def get_task_files(task_id):
        """获取指定任务生成的文件列表"""
        try:
            # 尝试多个可能的路径
            possible_paths = [
                os.path.abspath(os.path.join('output', 'report_scheduler', str(task_id))),
                os.path.abspath(os.path.join('output', 'report-scheduler', str(task_id))),
                os.path.abspath(os.path.join('output', 'report_scheduler', task_id)),
            ]
            
            files = []
            found_dir = None
            
            for path in possible_paths:
                logging.info(f"尝试查找目录: {path}")
                if os.path.exists(path) and os.path.isdir(path):
                    found_dir = path
                    logging.info(f"找到目录: {path}")
                    
                    for filename in os.listdir(path):
                        file_path = os.path.join(path, filename)
                        if os.path.isfile(file_path):
                            # 获取文件信息
                            file_stats = os.stat(file_path)
                            created_time = datetime.fromtimestamp(file_stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                            
                            files.append({
                                'filename': filename,
                                'created_at': created_time,
                                'size': file_stats.st_size
                            })
                    
                    break
            
            if not found_dir:
                logging.warning(f"未找到任务 {task_id} 的目录，尝试过的路径: {possible_paths}")
                return jsonify([]), 200
            
            logging.info(f"在 {found_dir} 中找到 {len(files)} 个文件")
            
            # 按创建时间倒序排序
            files.sort(key=lambda x: x['created_at'], reverse=True)
            
            return jsonify(files), 200
            
        except Exception as e:
            logging.error(f"获取任务文件列表失败: {str(e)}", exc_info=True)
            return jsonify({'error': f'获取任务文件列表失败: {str(e)}'}), 500

    @app.route('/task_management/download_file/<string:task_id>/<path:filename>', methods=['GET'])
    def download_task_file(task_id, filename):
        """下载指定任务的文件"""
        try:
            logging.info(f"尝试下载文件: {filename}, 任务ID: {task_id}")
            
            # 构建基本目录路径
            base_dir = os.path.abspath(os.path.join('output', 'report_scheduler', str(task_id)))
            logging.info(f"基本目录路径: {base_dir}")
            
            # 检查目录是否存在
            if not os.path.exists(base_dir):
                logging.error(f"目录不存在: {base_dir}")
                return jsonify({'error': f'目录不存在: {base_dir}'}), 404
            
            # 检查文件是否存在
            file_path = os.path.join(base_dir, filename)
            logging.info(f"完整文件路径: {file_path}")
            
            if not os.path.exists(file_path):
                logging.error(f"文件不存在: {file_path}")
                return jsonify({'error': f'文件不存在: {file_path}'}), 404
            
            # 尝试使用send_from_directory
            try:
                logging.info(f"尝试使用send_from_directory发送文件")
                return send_from_directory(
                    base_dir,
                    filename,
                    as_attachment=True
                )
            except Exception as e:
                logging.error(f"send_from_directory失败: {str(e)}", exc_info=True)
            
            # 如果send_from_directory失败，尝试直接读取文件
            try:
                logging.info(f"尝试直接读取文件并返回")
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                
                response = Response(
                    file_data,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
                        if filename.endswith('.xlsx') else 'application/octet-stream',
                    headers={
                        'Content-Disposition': f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}',
                        'Content-Length': str(os.path.getsize(file_path))
                    }
                )
                
                return response
                
            except Exception as e:
                logging.error(f"直接读取文件失败: {str(e)}", exc_info=True)
                return jsonify({'error': f'读取文件失败: {str(e)}'}), 500
            
        except Exception as e:
            logging.error(f"下载文件处理失败: {str(e)}", exc_info=True)
            return jsonify({'error': f'下载文件处理失败: {str(e)}'}), 500
