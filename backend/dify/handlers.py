"""
Handlers for processing Dify requests
"""
import logging
from typing import Dict, Any, List, Optional
import sqlparse

def validate_query(query: str) -> bool:
    """
    验证SQL查询的安全性
    """
    # 检查是否包含危险操作
    dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
    parsed = sqlparse.parse(query.upper())
    
    for statement in parsed:
        # 检查是否是SELECT语句
        if statement.get_type() != 'SELECT':
            return False
        
        # 检查是否包含危险关键字
        for keyword in dangerous_keywords:
            if keyword in statement.value:
                return False
    
    return True

def format_query_result(result: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    格式化查询结果为Dify期望的格式
    """
    if not result:
        return {
            'success': True,
            'data': [],
            'total': 0
        }
    
    return {
        'success': True,
        'data': result,
        'total': len(result)
    }

def handle_error(error: Exception) -> Dict[str, Any]:
    """
    统一的错误处理
    """
    logging.error(f"Error in Dify handler: {str(error)}")
    return {
        'success': False,
        'error': str(error)
    } 