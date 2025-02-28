import re
import datetime
import os
import logging

def format_filename(filename, execution_time=None):
    """
    根据执行时间格式化文件名
    
    参数:
        filename: 原始文件名模板
        execution_time: 执行时间，如果为None则使用当前时间
    
    返回:
        格式化后的文件名和是否进行了替换的标志
    """
    if execution_time is None:
        execution_time = datetime.datetime.now()
    
    # 设置日志记录
    logging.info(f"格式化文件名: {filename}, 执行时间: {execution_time}")
    
    # 处理日期格式化占位符
    formatted_name = filename
    original_name = filename
    has_replacement = False
    
    # 替换简单的日期格式占位符
    date_formats = {
        '%Y': execution_time.strftime('%Y'),  # 四位数年份
        '%y': execution_time.strftime('%y'),  # 两位数年份
        '%m': execution_time.strftime('%m'),  # 两位数月份
        '%d': execution_time.strftime('%d'),  # 两位数日期
        '%H': execution_time.strftime('%H'),  # 小时 (00-23)
        '%I': execution_time.strftime('%I'),  # 小时 (01-12)
        '%M': execution_time.strftime('%M'),  # 分钟
        '%S': execution_time.strftime('%S'),  # 秒
        '%p': execution_time.strftime('%p'),  # AM 或 PM
        '%a': execution_time.strftime('%a'),  # 星期几的简写
        '%A': execution_time.strftime('%A'),  # 星期几的全称
        '%b': execution_time.strftime('%b'),  # 月份的简写
        '%B': execution_time.strftime('%B'),  # 月份的全称
        '%j': execution_time.strftime('%j'),  # 一年中的第几天
        '%W': execution_time.strftime('%W'),  # 一周的星期几（周一为第一天）
        '%w': execution_time.strftime('%w'),  # 星期几 (0-6, 0是星期天)
        '%z': execution_time.strftime('%z'),  # UTC时区偏移
        '%Z': execution_time.strftime('%Z'),  # 时区名称
    }
    
    # 处理 date_add 函数
    # 匹配 {date_add(num,"format")} 或 {date_add(num,'format')}
    date_add_pattern = r'\{date_add\((-?\d+),\s*["\']([^"\']+)["\']\)\}'
    
    def date_add_replacer(match):
        nonlocal has_replacement
        has_replacement = True
        days = int(match.group(1))
        format_str = match.group(2)
        
        # 计算新日期
        new_date = execution_time + datetime.timedelta(days=days)
        
        # 记录日期计算
        logging.info(f"日期计算: 原始日期={execution_time}, 增加天数={days}, 新日期={new_date}")
        
        # 使用指定格式返回日期字符串
        result = new_date.strftime(format_str)
        logging.info(f"格式化结果: 格式={format_str}, 结果={result}")
        return result
    
    # 替换所有 date_add 函数
    if re.search(date_add_pattern, formatted_name):
        formatted_name = re.sub(date_add_pattern, date_add_replacer, formatted_name)
        has_replacement = True
        logging.info(f"替换 date_add 后的文件名: {formatted_name}")
    
    # 替换简单的日期格式占位符
    for placeholder, value in date_formats.items():
        if placeholder in formatted_name:
            formatted_name = formatted_name.replace(placeholder, value)
            has_replacement = True
    
    # 处理简单的大括号格式，如 {2025}
    simple_bracket_pattern = r'\{([^{}]+)\}'
    
    def simple_bracket_replacer(match):
        nonlocal has_replacement
        has_replacement = True
        # 直接返回大括号内的内容，不保留大括号
        return match.group(1)
    
    # 替换所有简单的大括号格式
    if re.search(simple_bracket_pattern, formatted_name):
        formatted_name = re.sub(simple_bracket_pattern, simple_bracket_replacer, formatted_name)
        has_replacement = True
        logging.info(f"替换简单大括号后的文件名: {formatted_name}")
    
    logging.info(f"最终格式化文件名: {formatted_name}, 是否有替换: {has_replacement}")
    return formatted_name, has_replacement

def get_unique_filename(output_dir, filename):
    """
    确保文件名在输出目录中是唯一的，如果存在同名文件，则添加序号
    
    参数:
        output_dir: 输出目录
        filename: 原始文件名
    
    返回:
        唯一的文件名
    """
    base_name, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    
    # 检查文件是否存在，如果存在则添加序号
    while os.path.exists(os.path.join(output_dir, new_filename)):
        new_filename = f"{base_name}({counter}){ext}"
        counter += 1
    
    return new_filename