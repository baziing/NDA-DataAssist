import logging
import json
import traceback
from mysql.connector import Error
from utils import connect_db, execute_query

# 设置更详细的日志格式
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('email_management')

def get_all_emails():
    """
    获取所有邮箱地址
    """
    logger.info("开始获取所有邮箱")
    conn = None
    cursor = None
    try:
        conn = connect_db()
        if not conn:
            logger.error("数据库连接失败")
            return {'status': 'error', 'message': '数据库连接失败'}
            
        logger.debug("数据库连接成功")
        cursor = conn.cursor(dictionary=True)
        
        # 查询所有邮箱
        query = """
        SELECT id, email FROM autoreport_emails
        ORDER BY email
        """
        logger.debug(f"执行SQL: {query}")
        cursor.execute(query)
        emails = cursor.fetchall()
        logger.debug(f"获取到 {len(emails)} 个邮箱")
        
        # 为每个邮箱获取所属组信息
        for email in emails:
            email['id'] = str(email['id'])  # 将 email_id 转换为字符串
            # 查询邮箱所属的组
            group_query = """
            SELECT g.id as value, g.group_name as label
            FROM autoreport_email_groups g
            JOIN autoreport_email_group_members m ON g.id = m.group_id
            WHERE m.email_id = %s
            """
            cursor.execute(group_query, (email['id'],))
            email['groups'] = cursor.fetchall()
            for group in email['groups']:
                group['value'] = str(group['value'])  # 将 group_id 转换为字符串
            
            # 查询邮箱接收的报表
            report_query = """
            SELECT t.id, t.taskName as name
            FROM autoreport_tasks t
            JOIN autoreport_task_recipients r ON t.id = r.task_id
            WHERE r.email_id = %s
            """
            cursor.execute(report_query, (email['id'],))
            email['reports'] = cursor.fetchall()
            for report in email['reports']:
                report['id'] = str(report['id'])  # 将 report_id 转换为字符串

        logger.info("成功获取所有邮箱及其关联信息")
        return {'status': 'success', 'data': emails}
    except Error as e:
        logger.error(f"获取邮箱列表失败: {e}")
        logger.error(traceback.format_exc())
        return {'status': 'error', 'message': f'获取邮箱列表失败: {str(e)}'}
    finally:
        try:
            if cursor:
                cursor.close()
                logger.debug("游标已关闭")
            if conn and conn.is_connected():
                conn.close()
                logger.debug("数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接时出错: {e}")

def search_emails(search_text):
    """
    搜索邮箱地址
    """
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        
        # 搜索邮箱
        query = """
        SELECT id, email FROM autoreport_emails
        WHERE email LIKE %s
        ORDER BY email
        """
        cursor.execute(query, (f'%{search_text}%',))
        emails = cursor.fetchall()
        
        # 为每个邮箱获取所属组信息
        for email in emails:
            email['id'] = str(email['id'])  # 将 email_id 转换为字符串
            # 查询邮箱所属的组
            group_query = """
            SELECT g.id as value, g.group_name as label
            FROM autoreport_email_groups g
            JOIN autoreport_email_group_members m ON g.id = m.group_id
            WHERE m.email_id = %s
            """
            cursor.execute(group_query, (email['id'],))
            email['groups'] = cursor.fetchall()
            for group in email['groups']:
                group['value'] = str(group['value'])  # 将 group_id 转换为字符串

            # 查询邮箱接收的报表
            report_query = """
            SELECT t.id, t.taskName as name
            FROM autoreport_tasks t
            JOIN autoreport_task_recipients r ON t.id = r.task_id
            WHERE r.email_id = %s
            """
            cursor.execute(report_query, (email['id'],))
            email['reports'] = cursor.fetchall()
            for report in email['reports']:
                report['id'] = str(report['id'])  # 将 report_id 转换为字符串
        
        return {'status': 'success', 'data': emails}
    except Error as e:
        logging.error(f"搜索邮箱失败: {e}")
        return {'status': 'error', 'message': f'搜索邮箱失败: {str(e)}'}
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def add_email(email_data):
    """
    添加新邮箱
    """
    logger.info(f"开始添加邮箱: {email_data['email']}")
    conn = None
    cursor = None
    try:
        conn = connect_db()
        if not conn:
            logger.error("数据库连接失败")
            return {'status': 'error', 'message': '数据库连接失败'}
            
        cursor = conn.cursor()
        
        # 开始事务
        conn.start_transaction()

        # 检查邮箱是否已存在
        check_email_query = "SELECT id FROM autoreport_emails WHERE email = %s"
        cursor.execute(check_email_query, (email_data['email'],))
        existing_email = cursor.fetchone()

        if existing_email:
            conn.rollback()
            logger.warning(f"邮箱 {email_data['email']} 已存在")
            return {'status': 'error', 'message': '邮箱已存在'}

        # 插入邮箱
        email_query = """
        INSERT INTO autoreport_emails (email)
        VALUES (%s)
        """
        logger.debug(f"执行SQL: {email_query} 参数: {email_data['email']}")
        cursor.execute(email_query, (email_data['email'],))
        email_id = str(cursor.lastrowid)
        logger.debug(f"邮箱插入成功，ID: {email_id}")

        # 添加邮箱与组的关联
        if 'groups' in email_data and email_data['groups']:
            for group_id in email_data['groups']:
                group_member_query = """
                INSERT INTO autoreport_email_group_members (email_id, group_id)
                VALUES (%s, %s)
                """
                cursor.execute(group_member_query, (email_id, str(group_id)))
            logger.debug(f"添加了 {len(email_data['groups'])} 个组关联")

        # 添加邮箱与报表的关联
        if 'reports' in email_data and email_data['reports']:
            for report_id in email_data['reports']:
                recipient_query = """
                INSERT INTO autoreport_task_recipients (task_id, email_id)
                VALUES (%s, %s)
                """
                cursor.execute(recipient_query, (str(report_id), email_id))
            logger.debug(f"添加了 {len(email_data['reports'])} 个报表关联")

        # 提交事务
        conn.commit()
        logger.info(f"邮箱 {email_data['email']} 添加成功")

        return {'status': 'success', 'message': '邮箱添加成功', 'id': email_id}
    except Error as e:
        # 回滚事务
        if conn and conn.is_connected():
            conn.rollback()
            logger.debug("事务已回滚")
        logger.error(f"添加邮箱失败: {e}")
        logger.error(traceback.format_exc())
        return {'status': 'error', 'message': f'添加邮箱失败: {str(e)}'}
    finally:
        if cursor:
            cursor.close()
            logger.debug("游标已关闭")
        if conn and conn.is_connected():
            # 确保在关闭连接前不执行任何提交操作
            try:
                conn.close()
            except Error as e:
                if e.errno != 1064: # 忽略由于回滚已经关闭连接导致的错误
                    raise
            logger.debug("数据库连接已关闭")

def update_email(email_data):
    """
    更新邮箱信息
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # 开始事务
        conn.start_transaction()
        
        # 更新邮箱地址
        email_query = """
        UPDATE autoreport_emails
        SET email = %s
        WHERE id = %s
        """
        cursor.execute(email_query, (email_data['email'], str(email_data['id'])))  # 将 email_data['id'] 转换为字符串
        
        # 删除旧的组关联
        delete_groups_query = """
        DELETE FROM autoreport_email_group_members
        WHERE email_id = %s
        """
        cursor.execute(delete_groups_query, (str(email_data['id']),))  # 将 email_data['id'] 转换为字符串
        
        # 添加新的组关联
        if 'groups' in email_data and email_data['groups']:
            for group_id in email_data['groups']:
                group_member_query = """
                INSERT INTO autoreport_email_group_members (email_id, group_id)
                VALUES (%s, %s)
                """
                cursor.execute(group_member_query, (str(email_data['id']), group_id))  # 将 email_data['id'] 转换为字符串
        
        # 删除旧的报表关联
        delete_reports_query = """
        DELETE FROM autoreport_task_recipients
        WHERE email_id = %s
        """
        cursor.execute(delete_reports_query, (str(email_data['id']),))  # 将 email_data['id'] 转换为字符串
        
        # 添加新的报表关联
        if 'reports' in email_data and email_data['reports']:
            for report_id in email_data['reports']:
                recipient_query = """
                INSERT INTO autoreport_task_recipients (task_id, email_id)
                VALUES (%s, %s)
                """
                cursor.execute(recipient_query, (report_id, str(email_data['id'])))  # 将 email_data['id'] 转换为字符串
        
        # 提交事务
        conn.commit()
        
        return {'status': 'success', 'message': '邮箱更新成功'}
    except Error as e:
        # 回滚事务
        if conn.is_connected():
            conn.rollback()
        logging.error(f"更新邮箱失败: {e}")
        return {'status': 'error', 'message': f'更新邮箱失败: {str(e)}'}
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def delete_email(email_id):
    """
    删除邮箱
    """
    logger.info(f"开始删除邮箱: ID={email_id}")
    conn = None
    cursor = None
    try:
        conn = connect_db()
        if not conn:
            logger.error("数据库连接失败")
            return {'status': 'error', 'message': '数据库连接失败'}
        
        cursor = conn.cursor()
        
        # 开始事务
        conn.start_transaction()
        
        # 删除邮箱前，先删除相关的组成员关系和报表接收者关系
        # 注意：如果表中设置了外键约束和CASCADE删除，这些步骤可能不是必需的
        
        # 1. 删除邮箱组成员关系
        delete_group_member_query = """
        DELETE FROM autoreport_email_group_members 
        WHERE email_id = %s
        """
        cursor.execute(delete_group_member_query, (email_id,))
        logger.debug(f"删除邮箱组成员关系成功，邮箱ID: {email_id}")
        
        # 2. 删除报表接收者关系
        delete_recipient_query = """
        DELETE FROM autoreport_task_recipients 
        WHERE email_id = %s
        """
        cursor.execute(delete_recipient_query, (str(email_id),))  # 将 email_id 转换为字符串
        logger.debug(f"删除报表接收者关系成功，邮箱ID: {email_id}")
        
        # 3. 删除邮箱
        delete_email_query = """
        DELETE FROM autoreport_emails 
        WHERE id = %s
        """
        cursor.execute(delete_email_query, (str(email_id),))  # 将 email_id 转换为字符串
        logger.debug(f"删除邮箱成功，ID: {email_id}")
        
        # 提交事务
        conn.commit()
        logger.info(f"邮箱删除成功，ID: {email_id}")
        
        return {
            'status': 'success',
            'message': '邮箱删除成功'
        }
    except Error as e:
        # 回滚事务
        if conn:
            conn.rollback()
        error_msg = str(e)
        logger.error(f"删除邮箱失败: {error_msg}")
        logger.error(traceback.format_exc())
        return {'status': 'error', 'message': f'删除邮箱失败: {error_msg}'}
    except Exception as e:
        # 回滚事务
        if conn:
            conn.rollback()
        error_msg = str(e)
        logger.error(f"删除邮箱时发生未知错误: {error_msg}")
        logger.error(traceback.format_exc())
        return {'status': 'error', 'message': f'删除邮箱时发生未知错误: {error_msg}'}
    finally:
        # 确保资源被正确关闭
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logger.debug("数据库连接已关闭")

def get_all_groups():
    """
    获取所有邮箱组
    """
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        
        # 查询所有邮箱组
        query = """
        SELECT g.id, g.group_name, 
               COUNT(m.email_id) as memberCount
        FROM autoreport_email_groups g
        LEFT JOIN autoreport_email_group_members m ON g.id = m.group_id
        GROUP BY g.id
        ORDER BY g.group_name
        """
        cursor.execute(query)
        groups = cursor.fetchall()
        
        # 为每个组获取成员邮箱
        for group in groups:
            group['id'] = str(group['id'])  # 将 group_id 转换为字符串
            member_query = """
            SELECT e.email
            FROM autoreport_emails e
            JOIN autoreport_email_group_members m ON e.id = m.email_id
            WHERE m.group_id = %s
            ORDER BY e.email
            """
            cursor.execute(member_query, (group['id'],))
            members = cursor.fetchall()
            group['memberEmails'] = [member['email'] for member in members]
        
        return {'status': 'success', 'data': groups}
    except Error as e:
        logging.error(f"获取邮箱组列表失败: {e}")
        return {'status': 'error', 'message': f'获取邮箱组列表失败: {str(e)}'}
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def search_groups(search_text):
    """
    搜索邮箱组
    """
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        
        # 搜索邮箱组
        query = """
        SELECT g.id, g.group_name, 
               COUNT(m.email_id) as memberCount
        FROM autoreport_email_groups g
        LEFT JOIN autoreport_email_group_members m ON g.id = m.group_id
        WHERE g.group_name LIKE %s
        GROUP BY g.id
        ORDER BY g.group_name
        """
        cursor.execute(query, (f'%{search_text}%',))
        groups = cursor.fetchall()
        
        # 为每个组获取成员邮箱
        for group in groups:
            group['id'] = str(group['id'])  # 将 group_id 转换为字符串
            member_query = """
            SELECT e.email
            FROM autoreport_emails e
            JOIN autoreport_email_group_members m ON e.id = m.email_id
            WHERE m.group_id = %s
            ORDER BY e.email
            """
            cursor.execute(member_query, (group['id'],))
            members = cursor.fetchall()
            group['memberEmails'] = [member['email'] for member in members]
        
        return {'status': 'success', 'data': groups}
    except Error as e:
        logging.error(f"搜索邮箱组失败: {e}")
        return {'status': 'error', 'message': f'搜索邮箱组失败: {str(e)}'}
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def add_group(group_data):
    """
    添加新邮箱组
    """
    logger.info(f"开始添加新邮箱组: {group_data['name']}")
    conn = None
    cursor = None
    try:
        conn = connect_db()
        if not conn:
            logger.error("数据库连接失败")
            return {'status': 'error', 'message': '数据库连接失败'}
        
        cursor = conn.cursor()
        
        # 开始事务
        conn.start_transaction()

        # 检查邮箱组是否已存在
        check_group_query = "SELECT id FROM autoreport_email_groups WHERE group_name = %s"
        cursor.execute(check_group_query, (group_data['name'],))
        existing_group = cursor.fetchone()

        if existing_group:
            conn.rollback()
            logger.warning(f"邮箱组 {group_data['name']} 已存在")
            return {'status': 'error', 'message': '邮箱组已存在'}

        # 1. 插入邮箱组
        group_name = group_data['name']
        insert_group_query = """
        INSERT INTO autoreport_email_groups (group_name) 
        VALUES (%s)
        """
        cursor.execute(insert_group_query, (group_name,))
        group_id = str(cursor.lastrowid)  # 将 group_id 转换为字符串
        logger.debug(f"邮箱组插入成功，ID: {group_id}")

        # 2. 处理成员
        if 'members' in group_data and group_data['members']:
            for member in group_data['members']:
                # 检查成员是否是已有邮箱ID或新邮箱地址
                if isinstance(member, int) or (isinstance(member, str) and member.isdigit()):
                    # 已有邮箱ID
                    email_id = int(member)

                    # 先检查记录是否已存在
                    check_query = """
                    SELECT COUNT(*) FROM autoreport_email_group_members 
                    WHERE group_id = %s AND email_id = %s
                    """
                    cursor.execute(check_query, (group_id, email_id))
                    exists = cursor.fetchone()[0] > 0

                    if not exists:
                        # 如果记录不存在，则插入
                        insert_member_query = """
                        INSERT INTO autoreport_email_group_members (group_id, email_id) 
                        VALUES (%s, %s)
                        """
                        cursor.execute(insert_member_query, (group_id, str(email_id)))
                        logger.debug(f"已有邮箱 {email_id} 添加到分组 {group_id}")
                else:
                    # 新邮箱地址
                    email = member

                    # 先检查邮箱是否已存在
                    check_email_query = """
                    SELECT id FROM autoreport_emails 
                    WHERE email = %s
                    """
                    cursor.execute(check_email_query, (email,))
                    result = cursor.fetchone()

                    if result:
                        # 邮箱已存在，获取ID
                        email_id = str(result[0])  # 将 email_id 转换为字符串
                        logger.debug(f"邮箱 {email} 已存在，ID: {email_id}")
                    else:
                        # 邮箱不存在，插入新邮箱
                        insert_email_query = """
                        INSERT INTO autoreport_emails (email) 
                        VALUES (%s)
                        """
                        cursor.execute(insert_email_query, (email,))
                        email_id = str(cursor.lastrowid)  # 将 email_id 转换为字符串
                        logger.debug(f"新邮箱 {email} 插入成功，ID: {email_id}")

                    # 检查成员关联是否已存在
                    check_member_query = """
                    SELECT COUNT(*) FROM autoreport_email_group_members 
                    WHERE group_id = %s AND email_id = %s
                    """
                    cursor.execute(check_member_query, (group_id, email_id))
                    exists = cursor.fetchone()[0] > 0

                    if not exists:
                        # 如果关联不存在，则插入
                        insert_member_query = """
                        INSERT INTO autoreport_email_group_members (group_id, email_id) 
                        VALUES (%s, %s)
                        """
                        cursor.execute(insert_member_query, (group_id, str(email_id)))
                        logger.debug(f"邮箱 {email} (ID: {email_id}) 添加到分组 {group_id}")

        # 提交事务
        conn.commit()
        logger.info(f"邮箱组 {group_name} 添加成功，ID: {group_id}")

        return {
            'status': 'success',
            'message': '邮箱组添加成功',
            'id': group_id
        }
    except Error as e:
        # 回滚事务
        if conn:
            conn.rollback()
        error_msg = str(e)
        logger.error(f"添加邮箱组失败: {error_msg}")
        logger.error(traceback.format_exc())
        return {'status': 'error', 'message': f'添加邮箱组失败: {error_msg}'}
    except Exception as e:
        # 回滚事务
        if conn:
            conn.rollback()
        error_msg = str(e)
        logger.error(f"添加邮箱组时发生未知错误: {error_msg}")
        logger.error(traceback.format_exc())
        return {'status': 'error', 'message': f'添加邮箱组时发生未知错误: {error_msg}'}
    finally:
        # 确保资源被正确关闭
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logger.debug("数据库连接已关闭")

def update_group(group_data):
    """
    更新邮箱组信息
    """
    logger.info(f"开始更新邮箱组: ID={group_data['id']}, Name={group_data['name']}")
    conn = None
    cursor = None
    try:
        conn = connect_db()
        if not conn:
            logger.error("数据库连接失败")
            return {'status': 'error', 'message': '数据库连接失败'}
        
        cursor = conn.cursor()
        
        # 开始事务
        conn.start_transaction()
        
        # 1. 更新邮箱组
        group_id = str(group_data['id'])  # 将 group_id 转换为字符串
        group_name = group_data['name']
        update_group_query = """
        UPDATE autoreport_email_groups 
        SET group_name = %s 
        WHERE id = %s
        """
        cursor.execute(update_group_query, (group_name, group_id))
        logger.debug(f"邮箱组更新成功，ID: {group_id}")
        
        # 2. 处理成员 - 先删除旧成员
        delete_members_query = """
        DELETE FROM autoreport_email_group_members 
        WHERE group_id = %s
        """
        cursor.execute(delete_members_query, (group_id,))
        
        # 添加新成员
        if 'members' in group_data and group_data['members']:
            for member in group_data['members']:
                # 检查成员是否是已有邮箱ID或新邮箱地址
                if isinstance(member, int) or (isinstance(member, str) and member.isdigit()):
                    # 已有邮箱ID
                    email_id = int(member)
                    insert_member_query = """
                    INSERT INTO autoreport_email_group_members (group_id, email_id) 
                    VALUES (%s, %s)
                    """
                    cursor.execute(insert_member_query, (group_id, str(email_id)))
                    logger.debug(f"已有邮箱 {email_id} 添加到分组 {group_id}")
                else:
                    # 新邮箱地址
                    email = member
                    
                    # 先检查邮箱是否已存在
                    check_email_query = """
                    SELECT id FROM autoreport_emails 
                    WHERE email = %s
                    """
                    cursor.execute(check_email_query, (email,))
                    result = cursor.fetchone()
                    
                    if result:
                        # 邮箱已存在，获取ID
                        email_id = str(result[0])  # 将 email_id 转换为字符串
                        logger.debug(f"邮箱 {email} 已存在，ID: {email_id}")
                    else:
                        # 邮箱不存在，插入新邮箱
                        insert_email_query = """
                        INSERT INTO autoreport_emails (email) 
                        VALUES (%s)
                        """
                        cursor.execute(insert_email_query, (email,))
                        email_id = str(cursor.lastrowid)  # 将 email_id 转换为字符串
                        logger.debug(f"新邮箱 {email} 插入成功，ID: {email_id}")
                    
                    # 插入成员关联
                    insert_member_query = """
                    INSERT INTO autoreport_email_group_members (group_id, email_id) 
                    VALUES (%s, %s)
                    """
                    cursor.execute(insert_member_query, (group_id, str(email_id)))
                    logger.debug(f"邮箱 {email} (ID: {email_id}) 添加到分组 {group_id}")
        
        # 提交事务
        conn.commit()
        logger.info(f"邮箱组 {group_name} 更新成功")
        
        return {
            'status': 'success',
            'message': '邮箱组更新成功'
        }
    except Error as e:
        # 回滚事务
        if conn:
            conn.rollback()
        error_msg = str(e)
        logger.error(f"更新邮箱组失败: {error_msg}")
        logger.error(traceback.format_exc())
        return {'status': 'error', 'message': f'更新邮箱组失败: {error_msg}'}
    except Exception as e:
        # 回滚事务
        if conn:
            conn.rollback()
        error_msg = str(e)
        logger.error(f"更新邮箱组时发生未知错误: {error_msg}")
        logger.error(traceback.format_exc())
        return {'status': 'error', 'message': f'更新邮箱组时发生未知错误: {error_msg}'}
    finally:
        # 确保资源被正确关闭
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logger.debug("数据库连接已关闭")

def delete_group(group_id):
    """
    删除邮箱组
    """
    logger.info(f"开始删除邮箱组: ID={group_id}")
    conn = None
    cursor = None
    try:
        conn = connect_db()
        if not conn:
            logger.error("数据库连接失败")
            return {'status': 'error', 'message': '数据库连接失败'}
        
        cursor = conn.cursor()
        
        # 开始事务
        conn.start_transaction()
        
        # 删除邮箱组前，先删除相关的组成员关系
        # 注意：如果表中设置了外键约束和CASCADE删除，这一步可能不是必需的
        
        # 1. 删除邮箱组成员关系
        delete_members_query = """
        DELETE FROM autoreport_email_group_members 
        WHERE group_id = %s
        """
        cursor.execute(delete_members_query, (str(group_id),))  # 将 group_id 转换为字符串
        logger.debug(f"删除邮箱组成员关系成功，组ID: {group_id}")
        
        # 2. 删除邮箱组
        delete_group_query = """
        DELETE FROM autoreport_email_groups 
        WHERE id = %s
        """
        cursor.execute(delete_group_query, (str(group_id),))  # 将 group_id 转换为字符串
        logger.debug(f"删除邮箱组成功，ID: {group_id}")
        
        # 提交事务
        conn.commit()
        logger.info(f"邮箱组删除成功，ID: {group_id}")
        
        return {
            'status': 'success',
            'message': '邮箱组删除成功'
        }
    except Error as e:
        # 回滚事务
        if conn:
            conn.rollback()
        error_msg = str(e)
        logger.error(f"删除邮箱组失败: {error_msg}")
        logger.error(traceback.format_exc())
        return {'status': 'error', 'message': f'删除邮箱组失败: {error_msg}'}
    except Exception as e:
        # 回滚事务
        if conn:
            conn.rollback()
        error_msg = str(e)
        logger.error(f"删除邮箱组时发生未知错误: {error_msg}")
        logger.error(traceback.format_exc())
        return {'status': 'error', 'message': f'删除邮箱组时发生未知错误: {error_msg}'}
    finally:
        # 确保资源被正确关闭
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logger.debug("数据库连接已关闭")

def get_group_members(group_id):
    """
    获取邮箱组的所有成员
    """
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT e.id, e.email
        FROM autoreport_emails e
        JOIN autoreport_email_group_members m ON e.id = m.email_id
        WHERE m.group_id = %s
        ORDER BY e.email
        """
        cursor.execute(query, (str(group_id),))  # 将 group_id 转换为字符串
        members = cursor.fetchall()
        for member in members:
            member['id'] = str(member['id'])  # 将 email_id 转换为字符串
        return {'status': 'success', 'data': members}
    except Error as e:
        logging.error(f"获取邮箱组成员失败: {e}")
        return {'status': 'error', 'message': f'获取邮箱组成员失败: {str(e)}'}
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def update_group_members(group_id, member_ids):
    """
    更新邮箱组成员
    """
    logger.info(f"开始更新邮箱组成员: 组ID={group_id}, 成员数量={len(member_ids)}")
    conn = None
    cursor = None
    try:
        conn = connect_db()
        if not conn:
            logger.error("数据库连接失败")
            return {'status': 'error', 'message': '数据库连接失败'}
        
        cursor = conn.cursor()
        
        # 开始事务
        conn.start_transaction()
        
        # 1. 删除旧的组成员关系
        delete_members_query = """
        DELETE FROM autoreport_email_group_members 
        WHERE group_id = %s
        """
        cursor.execute(delete_members_query, (str(group_id),))  # 将 group_id 转换为字符串
        logger.debug(f"删除旧的组成员关系成功，组ID: {group_id}")
        
        # 2. 添加新的组成员关系
        if member_ids:
            for email_id in member_ids:
                insert_member_query = """
                INSERT INTO autoreport_email_group_members (group_id, email_id) 
                VALUES (%s, %s)
                """
                cursor.execute(insert_member_query, (str(group_id), str(email_id)))  # 将 group_id 和 email_id 转换为字符串
                logger.debug(f"添加新的组成员关系成功，组ID: {group_id}, 邮箱ID: {email_id}")
        
        # 提交事务
        conn.commit()
        logger.info(f"邮箱组成员更新成功，组ID: {group_id}, 成员数量: {len(member_ids)}")
        
        return {
            'status': 'success',
            'message': '邮箱组成员更新成功'
        }
    except Error as e:
        # 回滚事务
        if conn:
            conn.rollback()
        error_msg = str(e)
        logger.error(f"更新邮箱组成员失败: {error_msg}")
        logger.error(traceback.format_exc())
        return {'status': 'error', 'message': f'更新邮箱组成员失败: {error_msg}'}
    except Exception as e:
        # 回滚事务
        if conn:
            conn.rollback()
        error_msg = str(e)
        logger.error(f"更新邮箱组成员时发生未知错误: {error_msg}")
        logger.error(traceback.format_exc())
        return {'status': 'error', 'message': f'更新邮箱组成员时发生未知错误: {error_msg}'}
    finally:
        # 确保资源被正确关闭
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logger.debug("数据库连接已关闭")

def get_report_options():
    """
    获取所有报表选项
    """
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT id, taskName as name
        FROM autoreport_tasks
        ORDER BY taskName
        """
        cursor.execute(query)
        reports = cursor.fetchall()
        for report in reports:
            report['id'] = str(report['id'])  # 将 report_id 转换为字符串
        return {'status': 'success', 'data': reports}
    except Error as e:
        logging.error(f"获取报表选项失败: {e}")
        return {'status': 'error', 'message': f'获取报表选项失败: {str(e)}'}
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
