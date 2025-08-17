"""
PDF Generator for Smith & Williams Trucking
Generates professional driver receipts, client invoices, and status reports
"""

import sqlite3
from datetime import datetime, date, timedelta
import os

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Database path
DB_PATH = 'swt_fleet.db'

# Company logo path - use ONLY the transparent logo
LOGO_PATH = 'swt_logo.png'  # Transparent logo, NOT the white one

# Company colors
PRIMARY_COLOR = colors.HexColor('#003366')  # Dark blue
SECONDARY_COLOR = colors.HexColor('#28a745')  # Green
ACCENT_COLOR = colors.HexColor('#f8f9fa')  # Light gray

def add_header_footer(canvas_obj, doc):
    """Add professional header and footer to each page"""
    canvas_obj.saveState()
    
    # Header with transparent logo
    logo_added = False
    if os.path.exists(LOGO_PATH):
        try:
            canvas_obj.drawImage(LOGO_PATH, inch, doc.pagesize[1] - 1.25*inch, 
                               width=1.5*inch, height=0.6*inch, 
                               preserveAspectRatio=True, mask='auto')  # mask='auto' preserves transparency
            logo_added = True
        except:
            pass
    
    canvas_obj.setFont('Helvetica-Bold', 14)
    canvas_obj.drawRightString(doc.pagesize[0] - inch, doc.pagesize[1] - 0.75*inch, 
                              "Smith & Williams Trucking LLC")
    
    # Header line
    canvas_obj.setStrokeColor(PRIMARY_COLOR)
    canvas_obj.setLineWidth(2)
    canvas_obj.line(inch, doc.pagesize[1] - 1.4*inch, 
                   doc.pagesize[0] - inch, doc.pagesize[1] - 1.4*inch)
    
    # Footer
    canvas_obj.setStrokeColor(PRIMARY_COLOR)
    canvas_obj.setLineWidth(1)
    canvas_obj.line(inch, 0.8*inch, doc.pagesize[0] - inch, 0.8*inch)
    
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.setFillColor(colors.HexColor('#666666'))
    canvas_obj.drawString(inch, 0.6*inch, 
                         f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    canvas_obj.drawRightString(doc.pagesize[0] - inch, 0.6*inch, 
                              f"Page {doc.page}")
    
    canvas_obj.drawCentredString(doc.pagesize[0]/2, 0.4*inch, 
                                "Confidential - Property of Smith & Williams Trucking LLC")
    
    canvas_obj.restoreState()

def get_professional_styles():
    """Get customized professional styles for PDFs"""
    styles = getSampleStyleSheet()
    
    # Title style
    styles.add(ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=PRIMARY_COLOR,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))
    
    # Subtitle style
    styles.add(ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#333333'),
        alignment=TA_CENTER,
        fontName='Helvetica'
    ))
    
    # Info style
    styles.add(ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#444444'),
        fontName='Helvetica'
    ))
    
    return styles

def generate_driver_receipt(driver_name, from_date, to_date):
    """Generate a professional driver payment receipt PDF"""
    
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab is not installed. Run: pip install reportlab")
    
    # Create filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"driver_receipt_{driver_name.replace(' ', '_')}_{timestamp}.pdf"
    
    # Create PDF with professional margins
    doc = SimpleDocTemplate(filename, pagesize=letter,
                          topMargin=1.75*inch, bottomMargin=inch,
                          leftMargin=0.75*inch, rightMargin=0.75*inch)
    elements = []
    styles = get_professional_styles()
    
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
    
    # Build PDF with professional header/footer
    doc.build(elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    return filename

def generate_client_invoice(client_name, from_date, to_date):
    """Generate a professional client invoice PDF"""
    
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab is not installed. Run: pip install reportlab")
    
    # Create filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"client_invoice_{client_name.replace(' ', '_')}_{timestamp}.pdf"
    
    # Create PDF with professional margins
    doc = SimpleDocTemplate(filename, pagesize=letter,
                          topMargin=1.75*inch, bottomMargin=inch,
                          leftMargin=0.75*inch, rightMargin=0.75*inch)
    elements = []
    styles = get_professional_styles()
    
    # Invoice number
    invoice_num = f"INV-{datetime.now().strftime('%Y%m')}-{client_name[:3].upper()}"
    
    # Title
    elements.append(Paragraph("INVOICE", styles['CustomTitle']))
    elements.append(Spacer(1, 0.1*inch))
    
    # Invoice details box
    invoice_data = [
        ['INVOICE DETAILS', '', '', ''],
        ['Invoice Number:', invoice_num, 'Invoice Date:', datetime.now().strftime("%B %d, %Y")],
        ['Bill To:', client_name, 'Due Date:', (datetime.now() + timedelta(days=30)).strftime("%B %d, %Y")],
        ['Service Period:', f'{from_date} to {to_date}', 'Terms:', 'Net 30'],
    ]
    
    invoice_table = Table(invoice_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
    invoice_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BACKGROUND', (0, 1), (-1, -1), ACCENT_COLOR),
        ('BOX', (0, 0), (-1, -1), 1, PRIMARY_COLOR),
        ('INNERGRID', (0, 1), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(invoice_table)
    elements.append(Spacer(1, 0.4*inch))
    
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
    
    # Build PDF with professional header/footer
    doc.build(elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    return filename

def generate_status_report(from_date, to_date):
    """Generate a professional comprehensive status report PDF"""
    
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab is not installed. Run: pip install reportlab")
    
    # Create filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"status_report_{timestamp}.pdf"
    
    # Create PDF with professional margins
    doc = SimpleDocTemplate(filename, pagesize=letter,
                          topMargin=1.75*inch, bottomMargin=inch,
                          leftMargin=0.75*inch, rightMargin=0.75*inch)
    elements = []
    styles = get_professional_styles()
    
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
    
    # Build PDF with professional header/footer
    doc.build(elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    return filename