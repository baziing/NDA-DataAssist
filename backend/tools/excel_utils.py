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
        # 读取所有工作表
        all_sheets_data = pd.read_excel(file_path, sheet_name=None)

        # 检查是否包含 db_name 和 output_sql 字段（不区分大小写）
        sql_list = []
        sheet_order = 1
        
        # 先检查是否存在setting工作表
        setting_sheet = None
        for sheet_name in all_sheets_data.keys():
            if '{setting}' in sheet_name.lower():
                setting_sheet = sheet_name
                break
        
        for sheet_name, df in all_sheets_data.items():
            # 跳过setting工作表
            if sheet_name == setting_sheet:
                continue
                
            # 将列名转换为小写以进行不区分大小写的比较
            df.columns = df.columns.str.lower()
            columns = df.columns.tolist()
            
            if 'db_name' not in columns or 'output_sql' not in columns:
                return {"is_valid": False, "message": f"工作表 '{sheet_name}' 必须包含 db_name 和 output_sql 字段（不区分大小写）"}

            # 获取每一行的数据
            for index, row in df.iterrows():
                sql_dict = {
                    'db_name': row['db_name'],
                    'output_sql': row['output_sql'],
                    'sql_order': index + 1,
                    'sheet_name': sheet_name,
                    'sheet_order': sheet_order
                }
                
                # 检查并添加 sql1, sql2, sql3 等字段
                i = 1
                while f'sql{i}' in columns:
                    if pd.notna(row[f'sql{i}']):  # 检查值是否为空
                        sql_dict[f'sql{i}'] = row[f'sql{i}']
                    i += 1
                
                # 添加其他可选字段
                if 'format' in columns and pd.notna(row['format']):
                    sql_dict['format'] = row['format']
                if 'pos' in columns and pd.notna(row['pos']):
                    sql_dict['pos'] = row['pos']
                if 'transpose' in columns and pd.notna(row['transpose']):
                    sql_dict['transpose'] = row['transpose']
                
                sql_list.append(sql_dict)
            sheet_order += 1
            
        return {"is_valid": True, "message": "", "sql_list": sql_list}
    except FileNotFoundError:
        return {"is_valid": False, "message": "文件未找到"}
    except pd.errors.EmptyDataError:
        return {"is_valid": False, "message": "Excel 文件为空"}
    except pd.errors.ParserError:
        return {"is_valid": False, "message": "Excel 文件解析错误"}
    except Exception as e:
        return {"is_valid": False, "message": f"文件读取失败: {str(e)}"}
