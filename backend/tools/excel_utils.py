import pandas as pd

def check_excel_file(file_path):
    """
    检查 Excel 文件是否有效，并且包含 db_name 和 output_sql 字段（不区分大小写）。

    Args:
        file_path (str): Excel 文件路径。

    Returns:
        dict: 包含校验结果和错误信息的字典。
            - is_valid (bool): True 表示文件有效，False 表示文件无效。
            - message (str): 错误信息，如果文件有效则为空字符串。
            - sql_list: list[dict]: 包含每一行数据的字典列表
    """
    try:
        df = pd.read_excel(file_path)
        # 检查是否包含 db_name 和 output_sql 字段（不区分大小写）
        columns = [col.lower() for col in df.columns]
        if 'db_name' not in columns or 'output_sql' not in columns:
            return {"is_valid": False, "message": "Excel 文件必须包含 db_name 和 output_sql 字段（不区分大小写）"}

        # 获取每一行的 db_name 和 output_sql
        sql_list = []
        for index, row in df.iterrows():
            sql_dict = {
                'db_name': row['db_name'],
                'output_sql': row['output_sql'],
                'sql_order': index + 1
            }
            if 'format' in row and row['format'] != '':
                sql_dict['format'] = row['format']
            if 'pos' in row and row['pos'] != '':
                sql_dict['pos'] = row['pos']
            if 'transpose' in row and row['transpose'] != '':
                sql_dict['transpose'] = row['transpose']
            sql_list.append(sql_dict)
        return {"is_valid": True, "message": "", "sql_list": sql_list}
    except FileNotFoundError:
        return {"is_valid": False, "message": "文件未找到"}
    except pd.errors.EmptyDataError:
        return {"is_valid": False, "message": "Excel 文件为空"}
    except pd.errors.ParserError:
        return {"is_valid": False, "message": "Excel 文件解析错误"}
    except Exception as e:
        return {"is_valid": False, "message": f"文件读取失败: {str(e)}"}
