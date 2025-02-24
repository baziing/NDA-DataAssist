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
    """
    try:
        df = pd.read_excel(file_path)
        # 检查是否包含 db_name 和 output_sql 字段（不区分大小写）
        columns = [col.lower() for col in df.columns]
        if 'db_name' not in columns or 'output_sql' not in columns:
            return {"is_valid": False, "message": "Excel 文件必须包含 db_name 和 output_sql 字段（不区分大小写）"}
        return {"is_valid": True, "message": "", "sql_list": []}
    except FileNotFoundError:
        return {"is_valid": False, "message": "文件未找到"}
    except pd.errors.EmptyDataError:
        return {"is_valid": False, "message": "Excel 文件为空"}
    except pd.errors.ParserError:
        return {"is_valid": False, "message": "Excel 文件解析错误"}
    except Exception as e:
        return {"is_valid": False, "message": f"文件读取失败: {str(e)}"}
