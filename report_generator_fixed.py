# -*- coding: utf-8 -*-
"""Fixed Report Generator"""

import sqlite3
import pandas as pd
from datetime import datetime

def generate_client_report():
    """Generate client report with delivery data"""
    conn = sqlite3.connect('trailer_tracker_streamlined.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            t.trailer_number,
            t.trailer_type,
            CASE WHEN t.is_new = 1 THEN 'New' ELSE 'Old' END as condition,
            t.current_location,
            t.origin_location,
            m.delivery_status,
            m.delivery_location
        FROM trailers t
        LEFT JOIN moves m ON t.trailer_number = m.new_trailer
        ORDER BY t.current_location
    """)
    
    data = cursor.fetchall()
    conn.close()
    
    df = pd.DataFrame(data, columns=[
        'Trailer', 'Type', 'Condition', 'Location',
        'Origin', 'Delivery Status', 'Delivery Location'
    ])
    
    return df

def generate_driver_report():
    """Generate driver report"""
    conn = sqlite3.connect('trailer_tracker_streamlined.db')
    cursor = conn.cursor()
    
    # Initialize driver_data first
    driver_data = []
    
    try:
        cursor.execute("""
            SELECT 
                d.driver_name,
                COUNT(m.id) as moves,
                SUM(m.driver_pay) as pay
            FROM drivers d
            LEFT JOIN moves m ON d.driver_name = m.driver_name
            GROUP BY d.id
        """)
        driver_data = cursor.fetchall()
    except:
        pass
    
    conn.close()
    
    if driver_data:
        return pd.DataFrame(driver_data, columns=['Driver', 'Moves', 'Total Pay'])
    return pd.DataFrame()
