# -*- coding: utf-8 -*-
"""Error handling system"""

ERROR_CODES = {
    "DB001": "Database connection failed",
    "DB002": "Table not found",
    "DB003": "Query execution failed",
    "AUTH001": "Authentication failed",
    "AUTH002": "Insufficient permissions",
    "VAL001": "Invalid input data",
    "REP001": "Report generation failed",
    "SYS001": "System configuration error"
}

def handle_error(code, details=""):
    """Handle error with code"""
    return f"[{code}] {ERROR_CODES.get(code, 'Unknown error')}: {details}"
