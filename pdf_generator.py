"""
PDF Generator for Smith & Williams Trucking
Generates driver receipts, client invoices, and status reports
"""

import sqlite3
from datetime import datetime, date
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
import os

# Database path
DB_PATH = 'swt_fleet.db'

def generate_driver_receipt(driver_name, from_date, to_date):
    """Generate a driver payment receipt PDF"""
    
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab is not installed. Run: pip install reportlab")
    
    # Create filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"driver_receipt_{driver_name.replace(' ', '_')}_{timestamp}.pdf"
    
    # Create PDF
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    elements.append(Paragraph("DRIVER PAYMENT RECEIPT", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Company info
    company_info = """
    <para align=center>
    <b>Smith & Williams Trucking LLC</b><br/>
    Memphis, TN<br/>
    </para>
    """
    elements.append(Paragraph(company_info, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Driver info
    driver_info = f"""
    <para>
    <b>Driver:</b> {driver_name}<br/>
    <b>Period:</b> {from_date} to {to_date}<br/>
    <b>Generated:</b> {datetime.now().strftime("%Y-%m-%d %H:%M")}
    </para>
    """
    elements.append(Paragraph(driver_info, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Get moves from database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check database structure
    cursor.execute("PRAGMA table_info(moves)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Query moves based on available columns
    if 'system_id' in columns:
        cursor.execute('''
            SELECT system_id, move_date, 
                   COALESCE(new_trailer, '-') as new_trailer,
                   COALESCE(old_trailer, '-') as old_trailer,
                   COALESCE(destination_location_id, delivery_location, '-') as destination,
                   COALESCE(estimated_miles, 0) as miles,
                   COALESCE(estimated_earnings, amount, 0) as earnings
            FROM moves
            WHERE driver_name = ?
            AND move_date BETWEEN ? AND ?
            AND status = 'completed'
            ORDER BY move_date DESC
        ''', (driver_name, from_date, to_date))
    else:
        cursor.execute('''
            SELECT order_number, 
                   COALESCE(completed_date, pickup_date, move_date) as move_date,
                   order_number as new_trailer,
                   '-' as old_trailer,
                   COALESCE(delivery_location, 'Unknown') as destination,
                   0 as miles,
                   COALESCE(amount, 0) as earnings
            FROM moves
            WHERE driver_name = ?
            AND status = 'completed'
            ORDER BY move_date DESC
        ''', (driver_name,))
    
    moves = cursor.fetchall()
    conn.close()
    
    if moves:
        # Create table data
        data = [['Move ID', 'Date', 'New Trailer', 'Old Trailer', 'Destination', 'Miles', 'Earnings']]
        
        total_miles = 0
        total_earnings = 0
        
        for move in moves:
            move_id, move_date, new_trailer, old_trailer, destination, miles, earnings = move
            total_miles += miles if miles else 0
            total_earnings += earnings if earnings else 0
            
            data.append([
                move_id,
                move_date,
                new_trailer,
                old_trailer,
                destination if isinstance(destination, str) else 'FedEx',
                f"{miles:,.2f}" if miles else "0",
                f"${earnings:,.2f}" if earnings else "$0.00"
            ])
        
        # Add totals row
        data.append(['', '', '', '', 'TOTALS:', f"{total_miles:,.2f}", f"${total_earnings:,.2f}"])
        
        # Create table
        table = Table(data, colWidths=[1.2*inch, 1*inch, 1*inch, 1*inch, 1.5*inch, 0.8*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, -1), (-1, -1), colors.grey),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Calculate factoring
        factoring_fee = total_earnings * 0.03
        after_factoring = total_earnings - factoring_fee
        
        # Summary
        summary = f"""
        <para>
        <b>Summary:</b><br/>
        Total Miles: {total_miles:,.2f}<br/>
        Gross Earnings: ${total_earnings:,.2f}<br/>
        Factoring Fee (3%): -${factoring_fee:,.2f}<br/>
        <b>Net Amount: ${after_factoring:,.2f}</b>
        </para>
        """
        elements.append(Paragraph(summary, styles['Normal']))
    else:
        elements.append(Paragraph("No completed moves found for this period.", styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    return filename

def generate_client_invoice(client_name, from_date, to_date):
    """Generate a client invoice PDF"""
    
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab is not installed. Run: pip install reportlab")
    
    # Create filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"client_invoice_{client_name.replace(' ', '_')}_{timestamp}.pdf"
    
    # Create PDF
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    elements.append(Paragraph("INVOICE", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Company info
    company_info = """
    <para align=center>
    <b>Smith & Williams Trucking LLC</b><br/>
    Memphis, TN<br/>
    </para>
    """
    elements.append(Paragraph(company_info, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Client info
    client_info = f"""
    <para>
    <b>Bill To:</b> {client_name}<br/>
    <b>Period:</b> {from_date} to {to_date}<br/>
    <b>Invoice Date:</b> {datetime.now().strftime("%Y-%m-%d")}
    </para>
    """
    elements.append(Paragraph(client_info, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Get moves from database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check database structure
    cursor.execute("PRAGMA table_info(moves)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Query moves
    if 'client' in columns:
        cursor.execute('''
            SELECT system_id, move_date, driver_name,
                   COALESCE(new_trailer, '-') as new_trailer,
                   COALESCE(estimated_miles, 0) as miles,
                   COALESCE(estimated_earnings, 0) as amount
            FROM moves
            WHERE client = ?
            AND move_date BETWEEN ? AND ?
            AND status = 'completed'
            ORDER BY move_date DESC
        ''', (client_name, from_date, to_date))
    else:
        # Fallback for simpler schema
        cursor.execute('''
            SELECT order_number, 
                   COALESCE(completed_date, pickup_date) as move_date,
                   driver_name,
                   order_number as trailer,
                   0 as miles,
                   COALESCE(amount, 0) as amount
            FROM moves
            WHERE status = 'completed'
            ORDER BY move_date DESC
        ''', (from_date,))
    
    moves = cursor.fetchall()
    conn.close()
    
    if moves:
        # Create table data
        data = [['Move ID', 'Date', 'Driver', 'Trailer', 'Miles', 'Amount']]
        
        total_amount = 0
        
        for move in moves:
            move_id, move_date, driver, trailer, miles, amount = move
            total_amount += amount if amount else 0
            
            data.append([
                move_id,
                move_date,
                driver,
                trailer,
                f"{miles:,.2f}" if miles else "0",
                f"${amount:,.2f}" if amount else "$0.00"
            ])
        
        # Add total row
        data.append(['', '', '', '', 'TOTAL:', f"${total_amount:,.2f}"])
        
        # Create table
        table = Table(data, colWidths=[1.5*inch, 1*inch, 1.5*inch, 1*inch, 0.8*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, -1), (-1, -1), colors.grey),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Total
        total_text = f"""
        <para align=right>
        <b>Total Amount Due: ${total_amount:,.2f}</b>
        </para>
        """
        elements.append(Paragraph(total_text, styles['Normal']))
    else:
        elements.append(Paragraph("No completed moves found for this period.", styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    return filename

def generate_status_report(from_date, to_date):
    """Generate a comprehensive status report PDF"""
    
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab is not installed. Run: pip install reportlab")
    
    # Create filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"status_report_{timestamp}.pdf"
    
    # Create PDF
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    elements.append(Paragraph("FLEET STATUS REPORT", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Report info
    report_info = f"""
    <para align=center>
    <b>Smith & Williams Trucking LLC</b><br/>
    Period: {from_date} to {to_date}<br/>
    Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
    </para>
    """
    elements.append(Paragraph(report_info, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Get data from database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get summary statistics
    cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'active'")
    active_moves = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'completed'")
    completed_moves = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM trailers WHERE status = 'available'")
    available_trailers = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT driver_name) FROM moves")
    active_drivers = cursor.fetchone()[0]
    
    # Summary section
    summary = f"""
    <para>
    <b>Summary Statistics:</b><br/>
    Active Moves: {active_moves}<br/>
    Completed Moves: {completed_moves}<br/>
    Available Trailers: {available_trailers}<br/>
    Active Drivers: {active_drivers}
    </para>
    """
    elements.append(Paragraph(summary, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Active moves table
    elements.append(Paragraph("<b>Active Moves:</b>", styles['Normal']))
    elements.append(Spacer(1, 0.1*inch))
    
    # Check database structure
    cursor.execute("PRAGMA table_info(moves)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'system_id' in columns:
        cursor.execute('''
            SELECT system_id, driver_name, move_date, status
            FROM moves
            WHERE status IN ('active', 'in_transit', 'at_destination')
            ORDER BY move_date DESC
            LIMIT 20
        ''')
    else:
        cursor.execute('''
            SELECT order_number, driver_name, 
                   COALESCE(pickup_date, move_date, completed_date), status
            FROM moves
            WHERE status IN ('active', 'in_transit', 'at_destination')
            ORDER BY order_number DESC
            LIMIT 20
        ''')
    
    active_data = cursor.fetchall()
    
    if active_data:
        data = [['Move ID', 'Driver', 'Date', 'Status']]
        for row in active_data:
            data.append(list(row))
        
        table = Table(data, colWidths=[2*inch, 2*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(table)
    else:
        elements.append(Paragraph("No active moves.", styles['Normal']))
    
    conn.close()
    
    # Build PDF
    doc.build(elements)
    return filename