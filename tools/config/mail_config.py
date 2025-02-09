# 报表邮件配置
MAIL_CONFIG = {
    # 临时报表配置
    'adhoc': {

    },
    
    # 每日报表配置
    'daily': {

    },
    
    # 每周报表配置
    'weekly': {

    },
    
    # 每月报表配置
    'monthly': {

    }
}

def replace_date_variables(text):
    """替换邮件内容中的日期变量"""
    from datetime import datetime, timedelta
    import re
    
    today = datetime.now()
    
    def replace_match(match):
        date_str = match.group(1)
        if date_str == 'today':
            return today.strftime('%Y-%m-%d')
        elif '+' in date_str or '-' in date_str:
            delta = int(date_str.split('today')[1])
            return (today + timedelta(days=delta)).strftime('%Y-%m-%d')
        return date_str
    
    return re.sub(r'\$([^$]+)\$', replace_match, text)

def get_mail_config(file_name, report_type):
    """根据文件名和报表类型获取邮件配置"""
    config = MAIL_CONFIG.get(report_type, {})
    for key in config:
        if key in file_name:  # 支持部分匹配
            return config[key]
    return None
