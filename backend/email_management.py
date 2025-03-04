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

def email_exists(cursor, email, exclude_id=None):
    """检查邮箱是否已存在（可选排除特定 ID）"""
    query = "SELECT id FROM autoreport_emails WHERE email = %s"
    params = (email,)
    if exclude_id:
        query += " AND id != %s"
        params += (str(exclude_id),)
    cursor.execute(query, params)
    return cursor.fetchone() is not None

def group_name_exists(cursor, group_name, exclude_id=None):
    """检查邮箱组名是否已存在（可选排除特定 ID）"""
    query = "SELECT id FROM autoreport_email_groups WHERE group_name = %s"
    params = (group_name,)
    if exclude_id:
        query += " AND id != %s"
        params += (str(exclude_id),)
    cursor.execute(query, params)
    return cursor.fetchone() is not None

def get_all_emails(page=1, page_size=10, search_text=None):
    """
    获取所有邮箱地址，支持分页和搜索
    """
    logger.info(f"开始获取邮箱列表: 页码={page}, 每页数量={page_size}, 搜索文本={search_text}")
    conn = None
    cursor = None
    try:
        conn = connect_db()
        if not conn:
            logger.error("数据库连接失败")
            return {'status': 'error', 'message': '数据库连接失败'}
            
        logger.debug("数据库连接成功")
        cursor = conn.cursor(dictionary=True)
        
        # 构建查询条件
        where_clause = ""
        email_filter = ""
        params = []
        if search_text:
            where_clause = "WHERE email LIKE %s"
            email_filter = "AND email LIKE %s"
            params.append(f'%{search_text}%')
        
        # 查询总数
        count_query = f"""
        SELECT COUNT(*) as total FROM autoreport_emails
        {where_clause}
        """
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        logger.debug(f"邮箱总数: {total}")
        
        # 计算分页
        offset = (page - 1) * page_size

        # 使用复杂查询获取邮箱直接关联的报表和通过邮箱组关联的报表
        query = f"""
        WITH email_reports AS (
            -- 邮箱直接关联的报表
            SELECT 
                e.id as email_id, 
                e.email,
                t.id as task_id, 
                t.taskName as task_name
            FROM autoreport_emails e
            LEFT JOIN autoreport_task_recipients tr ON e.id = tr.email_id
            LEFT JOIN autoreport_tasks t ON tr.task_id = t.id
            WHERE tr.email_id IS NOT NULL AND t.id IS NOT NULL
            {email_filter if search_text else ""}
            
            UNION
            
            -- 通过邮箱组关联的报表
            SELECT 
                e.id as email_id, 
                e.email,
                t.id as task_id, 
                t.taskName as task_name
            FROM autoreport_emails e
            JOIN autoreport_email_group_members egm ON e.id = egm.email_id
            JOIN autoreport_task_recipients tr ON egm.group_id = tr.group_id
            JOIN autoreport_tasks t ON tr.task_id = t.id
            WHERE tr.group_id IS NOT NULL AND t.id IS NOT NULL
            {email_filter if search_text else ""}
        ),
        email_groups AS (
            -- 邮箱所属的组
            SELECT 
                e.id as email_id, 
                e.email,
                g.id as group_id, 
                g.group_name
            FROM autoreport_emails e
            LEFT JOIN autoreport_email_group_members egm ON e.id = egm.email_id
            LEFT JOIN autoreport_email_groups g ON egm.group_id = g.id
            WHERE egm.group_id IS NOT NULL
            {email_filter if search_text else ""}
        )
        
        SELECT 
            e.id, 
            e.email,
            GROUP_CONCAT(DISTINCT CONCAT(g.group_id, ':', g.group_name) SEPARATOR ';') as groups,
            GROUP_CONCAT(DISTINCT CONCAT(r.task_id, ':', r.task_name) SEPARATOR ';') as reports
        FROM autoreport_emails e
        LEFT JOIN email_groups g ON e.id = g.email_id
        LEFT JOIN email_reports r ON e.id = r.email_id
        {where_clause}
        GROUP BY e.id, e.email
        ORDER BY e.email
        LIMIT %s OFFSET %s
        """
        
        # 构建参数列表
        query_params = []
        if search_text:
            # 为三个子查询中的email_filter添加参数
            query_params.extend([params[0], params[0], params[0]])
            # 为主查询的where_clause添加参数
            query_params.append(params[0])
        
        # 添加分页参数
        query_params.extend([page_size, offset])
        
        logger.debug(f"执行SQL: {query}, 参数: {query_params}")
        cursor.execute(query, query_params)
        emails = cursor.fetchall()
        logger.debug(f"获取到 {len(emails)} 个邮箱")

        # 处理分组和报表信息
        for email in emails:
            email['id'] = str(email['id'])
            email['groups'] = [{'value': str(g.split(':')[0]), 'label': g.split(':')[1]} for g in email['groups'].split(';') if g] if email['groups'] else []
            email['reports'] = [{'id': str(r.split(':')[0]), 'name': r.split(':')[1]} for r in email['reports'].split(';') if r] if email['reports'] else []

        logger.info("成功获取邮箱列表及其关联信息")
        return {
            'status': 'success',
            'items': emails,
            'total': total,
            'page': page,
            'pageSize': page_size
        }
    except Error as e:
        logger.error(f"获取邮箱列表失败: {e}")
        logger.error(traceback.format_exc())
        return {'status': 'error', 'message': f'获取邮箱列表失败: {str(e)}', 'items': []}
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

def search_emails(search_text, page=1, page_size=10):
    """
    搜索邮箱地址，支持分页
    """
    logger.info(f"开始搜索邮箱: 搜索文本={search_text}, 页码={page}, 每页数量={page_size}")
    conn = None
    cursor = None
    try:
        conn = connect_db()
        if not conn:
            logger.error("数据库连接失败")
            return {'status': 'error', 'message': '数据库连接失败'}
            
        cursor = conn.cursor(dictionary=True)
        
        # 查询总数
        count_query = """
        SELECT COUNT(*) as total FROM autoreport_emails
        WHERE email LIKE %s
        """
        cursor.execute(count_query, (f'%{search_text}%',))
        total = cursor.fetchone()['total']
        logger.debug(f"匹配邮箱总数: {total}")
        
        # 计算分页
        offset = (page - 1) * page_size

        # 使用复杂查询获取邮箱直接关联的报表和通过邮箱组关联的报表
        query = """
        WITH email_reports AS (
            -- 邮箱直接关联的报表
            SELECT 
                e.id as email_id, 
                e.email,
                t.id as task_id, 
                t.taskName as task_name
            FROM autoreport_emails e
            LEFT JOIN autoreport_task_recipients tr ON e.id = tr.email_id
            LEFT JOIN autoreport_tasks t ON tr.task_id = t.id
            WHERE tr.email_id IS NOT NULL AND t.id IS NOT NULL
            AND e.email LIKE %s
            
            UNION
            
            -- 通过邮箱组关联的报表
            SELECT 
                e.id as email_id, 
                e.email,
                t.id as task_id, 
                t.taskName as task_name
            FROM autoreport_emails e
            JOIN autoreport_email_group_members egm ON e.id = egm.email_id
            JOIN autoreport_task_recipients tr ON egm.group_id = tr.group_id
            JOIN autoreport_tasks t ON tr.task_id = t.id
            WHERE tr.group_id IS NOT NULL AND t.id IS NOT NULL
            AND e.email LIKE %s
        ),
        email_groups AS (
            -- 邮箱所属的组
            SELECT 
                e.id as email_id, 
                e.email,
                g.id as group_id, 
                g.group_name
            FROM autoreport_emails e
            LEFT JOIN autoreport_email_group_members egm ON e.id = egm.email_id
            LEFT JOIN autoreport_email_groups g ON egm.group_id = g.id
            WHERE egm.group_id IS NOT NULL
            AND e.email LIKE %s
        )
        
        SELECT 
            e.id, 
            e.email,
            GROUP_CONCAT(DISTINCT CONCAT(g.group_id, ':', g.group_name) SEPARATOR ';') as groups,
            GROUP_CONCAT(DISTINCT CONCAT(r.task_id, ':', r.task_name) SEPARATOR ';') as reports
        FROM autoreport_emails e
        LEFT JOIN email_groups g ON e.id = g.email_id
        LEFT JOIN email_reports r ON e.id = r.email_id
        WHERE e.email LIKE %s
        GROUP BY e.id, e.email
        ORDER BY e.email
        LIMIT %s OFFSET %s
        """
        search_param = f'%{search_text}%'
        cursor.execute(query, (search_param, search_param, search_param, search_param, page_size, offset))
        emails = cursor.fetchall()
        logger.debug(f"获取到 {len(emails)} 个邮箱")

        # 处理分组和报表信息
        for email in emails:
            email['id'] = str(email['id'])
            email['groups'] = [{'value': str(g.split(':')[0]), 'label': g.split(':')[1]} for g in email['groups'].split(';') if g] if email['groups'] else []
            email['reports'] = [{'id': str(r.split(':')[0]), 'name': r.split(':')[1]} for r in email['reports'].split(';') if r] if email['reports'] else []

        logger.info(f"成功搜索邮箱，找到 {total} 个匹配结果")
        return {
            'status': 'success',
            'items': emails,
            'total': total,
            'page': page,
            'pageSize': page_size
        }
    except Error as e:
        logger.error(f"搜索邮箱失败: {e}")
        logger.error(traceback.format_exc())
        return {'status': 'error', 'message': f'搜索邮箱失败: {str(e)}'}
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
        if email_exists(cursor, email_data['email']):
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

        # 检查更新后的邮箱是否与其他邮箱冲突
        if email_exists(cursor, email_data['email'], email_data['id']):
            conn.rollback()
            logger.warning(f"邮箱 {email_data['email']} 已存在，更新失败")
            return {'status': 'error', 'message': '邮箱已存在，更新失败'}
        
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
        cursor.execute(delete_group_member_query, (str(email_id),))  # 确保 email_id 是字符串
        logger.debug(f"删除邮箱组成员关系成功，邮箱ID: {email_id}")

        # 2. 删除报表接收者关系
        delete_recipient_query = """
        DELETE FROM autoreport_task_recipients 
        WHERE email_id = %s
        """
        cursor.execute(delete_recipient_query, (str(email_id),))  # 确保 email_id 是字符串
        logger.debug(f"删除报表接收者关系成功，邮箱ID: {email_id}")

        # 3. 删除邮箱
        delete_email_query = """
        DELETE FROM autoreport_emails 
        WHERE id = %s
        """
        cursor.execute(delete_email_query, (str(email_id),))  # 确保 email_id 是字符串
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

def batch_delete_emails(email_ids):
    """
    批量删除邮箱
    
    Args:
        email_ids: 要删除的邮箱ID列表
    """
    logger.info(f"开始批量删除邮箱: IDs={email_ids}")
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

        # 确保所有ID都是字符串
        email_ids = [str(email_id) for email_id in email_ids]
        
        # 构建IN子句的参数占位符
        placeholders = ', '.join(['%s'] * len(email_ids))
        
        # 1. 删除邮箱组成员关系
        delete_group_member_query = f"""
        DELETE FROM autoreport_email_group_members 
        WHERE email_id IN ({placeholders})
        """
        cursor.execute(delete_group_member_query, email_ids)
        logger.debug(f"删除邮箱组成员关系成功，邮箱IDs: {email_ids}")

        # 2. 删除报表接收者关系
        delete_recipient_query = f"""
        DELETE FROM autoreport_task_recipients 
        WHERE email_id IN ({placeholders})
        """
        cursor.execute(delete_recipient_query, email_ids)
        logger.debug(f"删除报表接收者关系成功，邮箱IDs: {email_ids}")

        # 3. 删除邮箱
        delete_email_query = f"""
        DELETE FROM autoreport_emails 
        WHERE id IN ({placeholders})
        """
        cursor.execute(delete_email_query, email_ids)
        logger.debug(f"删除邮箱成功，IDs: {email_ids}")

        # 提交事务
        conn.commit()
        logger.info(f"批量删除邮箱成功，共 {len(email_ids)} 个")
        
        return {
            'status': 'success',
            'message': f'成功删除 {len(email_ids)} 个邮箱'
        }
    except Error as e:
        # 回滚事务
        if conn:
            conn.rollback()
        error_msg = str(e)
        logger.error(f"批量删除邮箱失败: {error_msg}")
        logger.error(traceback.format_exc())
        return {'status': 'error', 'message': f'批量删除邮箱失败: {error_msg}'}
    except Exception as e:
        # 回滚事务
        if conn:
            conn.rollback()
        error_msg = str(e)
        logger.error(f"批量删除邮箱时发生未知错误: {error_msg}")
        logger.error(traceback.format_exc())
        return {'status': 'error', 'message': f'批量删除邮箱时发生未知错误: {error_msg}'}
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

def get_all_groups(page=1, page_size=10, search_text=None):
    """
    获取所有邮箱组，支持分页和搜索
    """
    logger.info(f"开始获取邮箱组列表: 页码={page}, 每页数量={page_size}, 搜索文本={search_text}")
    conn = None
    cursor = None
    try:
        conn = connect_db()
        if not conn:
            logger.error("数据库连接失败")
            return {'status': 'error', 'message': '数据库连接失败'}
            
        cursor = conn.cursor(dictionary=True)
        
        # 构建查询条件
        where_clause = ""
        params = []
        if search_text:
            where_clause = "WHERE g.group_name LIKE %s"
            params.append(f'%{search_text}%')
        
        # 查询总数
        count_query = f"""
        SELECT COUNT(*) as total FROM autoreport_email_groups g
        {where_clause}
        """
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        logger.debug(f"邮箱组总数: {total}")
        
        # 计算分页
        offset = (page - 1) * page_size
        
        # 查询邮箱组列表
        query = f"""
        SELECT g.id, g.group_name, 
               COUNT(m.email_id) as memberCount
        FROM autoreport_email_groups g
        LEFT JOIN autoreport_email_group_members m ON g.id = m.group_id
        {where_clause}
        GROUP BY g.id
        ORDER BY g.group_name
        LIMIT %s OFFSET %s
        """
        query_params = params + [page_size, offset]
        logger.debug(f"执行SQL: {query}, 参数: {query_params}")
        cursor.execute(query, query_params)
        groups = cursor.fetchall()
        logger.debug(f"获取到 {len(groups)} 个邮箱组")
        
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
        
        logger.info("成功获取邮箱组列表及其成员信息")
        return {
            'status': 'success', 
            'items': groups,
            'total': total,
            'page': page,
            'pageSize': page_size
        }
    except Error as e:
        logger.error(f"获取邮箱组列表失败: {e}")
        logger.error(traceback.format_exc())
        return {'status': 'error', 'message': f'获取邮箱组列表失败: {str(e)}'}
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

def search_groups(search_text, page=1, page_size=10):
    """
    搜索邮箱组，支持分页
    """
    logger.info(f"开始搜索邮箱组: 搜索文本={search_text}, 页码={page}, 每页数量={page_size}")
    conn = None
    cursor = None
    try:
        conn = connect_db()
        if not conn:
            logger.error("数据库连接失败")
            return {'status': 'error', 'message': '数据库连接失败'}
            
        cursor = conn.cursor(dictionary=True)
        
        # 查询总数
        count_query = """
        SELECT COUNT(*) as total FROM autoreport_email_groups
        WHERE group_name LIKE %s
        """
        cursor.execute(count_query, (f'%{search_text}%',))
        total = cursor.fetchone()['total']
        logger.debug(f"匹配邮箱组总数: {total}")
        
        # 计算分页
        offset = (page - 1) * page_size
        
        # 搜索邮箱组
        query = """
        SELECT g.id, g.group_name, 
               COUNT(m.email_id) as memberCount
        FROM autoreport_email_groups g
        LEFT JOIN autoreport_email_group_members m ON g.id = m.group_id
        WHERE g.group_name LIKE %s
        GROUP BY g.id
        ORDER BY g.group_name
        LIMIT %s OFFSET %s
        """
        cursor.execute(query, (f'%{search_text}%', page_size, offset))
        groups = cursor.fetchall()
        logger.debug(f"获取到 {len(groups)} 个邮箱组")
        
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
        
        logger.info(f"成功搜索邮箱组，找到 {total} 个匹配结果")
        return {
            'status': 'success', 
            'items': groups,
            'total': total,
            'page': page,
            'pageSize': page_size
        }
    except Error as e:
        logger.error(f"搜索邮箱组失败: {e}")
        logger.error(traceback.format_exc())
        return {'status': 'error', 'message': f'搜索邮箱组失败: {str(e)}'}
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
        if group_name_exists(cursor, group_data['name']):
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

        # 检查更新后的邮箱组名是否与其他邮箱组冲突
        if group_name_exists(cursor, group_data['name'], group_data['id']):
            conn.rollback()
            logger.warning(f"邮箱组 {group_data['name']} 已存在，更新失败")
            return {'status': 'error', 'message': '邮箱组已存在，更新失败'}
        
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

def batch_delete_groups(group_ids):
    """
    批量删除邮箱组
    
    Args:
        group_ids: 要删除的邮箱组ID列表
    """
    logger.info(f"开始批量删除邮箱组: IDs={group_ids}")
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

        # 确保所有ID都是字符串
        group_ids = [str(group_id) for group_id in group_ids]
        
        # 构建IN子句的参数占位符
        placeholders = ', '.join(['%s'] * len(group_ids))
        
        # 1. 删除邮箱组成员关系
        delete_members_query = f"""
        DELETE FROM autoreport_email_group_members 
        WHERE group_id IN ({placeholders})
        """
        cursor.execute(delete_members_query, group_ids)
        logger.debug(f"删除邮箱组成员关系成功，组IDs: {group_ids}")
        
        # 2. 删除邮箱组
        delete_group_query = f"""
        DELETE FROM autoreport_email_groups 
        WHERE id IN ({placeholders})
        """
        cursor.execute(delete_group_query, group_ids)
        logger.debug(f"删除邮箱组成功，IDs: {group_ids}")
        
        # 提交事务
        conn.commit()
        logger.info(f"批量删除邮箱组成功，共 {len(group_ids)} 个")
        
        return {
            'status': 'success',
            'message': f'成功删除 {len(group_ids)} 个邮箱组'
        }
    except Error as e:
        # 回滚事务
        if conn:
            conn.rollback()
        error_msg = str(e)
        logger.error(f"批量删除邮箱组失败: {error_msg}")
        logger.error(traceback.format_exc())
        return {'status': 'error', 'message': f'批量删除邮箱组失败: {error_msg}'}
    except Exception as e:
        # 回滚事务
        if conn:
            conn.rollback()
        error_msg = str(e)
        logger.error(f"批量删除邮箱组时发生未知错误: {error_msg}")
        logger.error(traceback.format_exc())
        return {'status': 'error', 'message': f'批量删除邮箱组时发生未知错误: {error_msg}'}
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
