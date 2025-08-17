"""
COMPLETE PDF SYSTEM REBUILD
Smith & Williams Trucking LLC
All PDF generation in ONE working file
"""

import os
import sqlite3
from datetime import datetime, date
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas

# DATABASE - Use the same as app.py
DB_PATH = 'smith_williams_trucking.db'

# COMPANY INFO - ONE PLACE
COMPANY = {
    'name': 'SMITH & WILLIAMS TRUCKING LLC',
    'address': '7600 N 15th St Suite 150, Phoenix, AZ 85020',
    'phone': '(951) 437-5474',
    'email': 'Dispatch@smithwilliamstrucking.com',
    'website': 'www.smithwilliamstrucking.com',
    'dot': 'DOT #3675217',
    'mc': 'MC #1276006',
    'owner': 'Brandon Smith'
}

def add_letterhead(canvas, doc):
    """Add company letterhead to EVERY page of EVERY PDF"""
    canvas.saveState()
    
    # Logo
    if os.path.exists('swt_logo_white.png'):
        try:
            canvas.drawImage('swt_logo_white.png', 0.75*inch, doc.pagesize[1] - 1.2*inch,
                           width=1.2*inch, height=0.6*inch, preserveAspectRatio=True)
        except:
            pass
    
    # Company Name
    canvas.setFont('Helvetica-Bold', 16)
    canvas.setFillColor(colors.HexColor('#003366'))
    canvas.drawString(2.2*inch, doc.pagesize[1] - 0.85*inch, COMPANY['name'])
    
    # Address
    canvas.setFont('Helvetica', 10)
    canvas.setFillColor(colors.black)
    canvas.drawString(2.2*inch, doc.pagesize[1] - 1*inch, COMPANY['address'])
    canvas.drawString(2.2*inch, doc.pagesize[1] - 1.15*inch, f"{COMPANY['dot']} | {COMPANY['mc']}")
    
    # Contact
    canvas.drawRightString(doc.pagesize[0] - inch, doc.pagesize[1] - 0.85*inch, f"Phone: {COMPANY['phone']}")
    canvas.drawRightString(doc.pagesize[0] - inch, doc.pagesize[1] - 1*inch, COMPANY['email'])
    canvas.drawRightString(doc.pagesize[0] - inch, doc.pagesize[1] - 1.15*inch, COMPANY['website'])
    
    # Header Line
    canvas.setStrokeColor(colors.HexColor('#DC143C'))
    canvas.setLineWidth(2)
    canvas.line(inch, doc.pagesize[1] - 1.4*inch, doc.pagesize[0] - inch, doc.pagesize[1] - 1.4*inch)
    
    # Footer
    canvas.setStrokeColor(colors.HexColor('#003366'))
    canvas.line(inch, 0.8*inch, doc.pagesize[0] - inch, 0.8*inch)
    
    canvas.setFont('Helvetica', 8)
    canvas.drawString(inch, 0.6*inch, f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    canvas.drawRightString(doc.pagesize[0] - inch, 0.6*inch, f"Page {doc.page}")
    canvas.drawCentredString(doc.pagesize[0]/2, 0.4*inch, f"© {COMPANY['name']}")
    
    canvas.restoreState()

def get_contractor_info(driver_name):
    """Get contractor company info for any driver"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT company_name, phone, email FROM drivers WHERE name = ?", (driver_name,))
        result = cursor.fetchone()
        if result and result[0]:
            conn.close()
            return result[0], result[1] or 'Not on file', result[2] or 'Not on file'
    except:
        pass
    
    conn.close()
    
    # Owner special case
    if driver_name == "Brandon Smith":
        return COMPANY['name'], COMPANY['phone'], COMPANY['email']
    
    return f"{driver_name} Trucking", "Not on file", "Not on file"

def fix_date(date_input):
    """Convert any date format to string"""
    if isinstance(date_input, date):
        return date_input.strftime('%Y-%m-%d')
    return str(date_input)

def generate_driver_receipt(driver_name, from_date, to_date):
    """Generate driver payment receipt with ALL fixes"""
    
    # Fix dates
    from_date = fix_date(from_date)
    to_date = fix_date(to_date)
    
    # Get contractor info
    company_name, phone, email = get_contractor_info(driver_name)
    
    # Get moves from database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COALESCE(system_id, order_number, 'MOVE-' || id) as move_id,
            move_date,
            new_trailer,
            old_trailer,
            COALESCE(destination_location, delivery_location, 'Unknown') as destination,
            COALESCE(estimated_miles, actual_miles, 0) as miles,
            COALESCE(estimated_earnings, amount, 0) as earnings,
            status
        FROM moves
        WHERE driver_name = ?
        AND date(move_date) >= date(?)
        AND date(move_date) <= date(?)
        ORDER BY move_date DESC
    """, (driver_name, from_date, to_date))
    
    moves = cursor.fetchall()
    conn.close()
    
    # Create PDF
    filename = f"driver_receipt_{driver_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter,
                          topMargin=1.75*inch, bottomMargin=inch,
                          leftMargin=0.75*inch, rightMargin=0.75*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle('Title', fontSize=24, textColor=colors.HexColor('#003366'),
                                alignment=TA_CENTER, spaceAfter=30)
    elements.append(Paragraph("DRIVER PAYMENT RECEIPT", title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Driver Info WITH Contractor Company
    info_html = f"""
    <b>DRIVER INFORMATION</b><br/><br/>
    <b>Name:</b> {driver_name}<br/>
    <b>Contractor Company:</b> {company_name}<br/>
    <b>Phone:</b> {phone}<br/>
    <b>Email:</b> {email}<br/>
    <br/>
    <b>Period:</b> {from_date} to {to_date}<br/>
    <b>Generated:</b> {datetime.now().strftime('%B %d, %Y')}
    """
    
    info_style = ParagraphStyle('Info', fontSize=11, leftIndent=20)
    elements.append(Paragraph(info_html, info_style))
    elements.append(Spacer(1, 0.3*inch))
    
    if moves:
        # Table with moves
        data = [['Move ID', 'Date', 'New', 'Old', 'Destination', 'Miles', 'Earnings', 'Status']]
        
        total_earnings = 0
        total_miles = 0
        
        for move in moves:
            earnings = float(move[6]) if move[6] else 0
            miles = float(move[5]) if move[5] else 0
            total_earnings += earnings
            total_miles += miles
            
            data.append([
                str(move[0])[:12],
                str(move[1])[:10],
                str(move[2])[:8] if move[2] else '-',
                str(move[3])[:8] if move[3] else '-',
                str(move[4])[:20],
                f"{miles:.0f}",
                f"${earnings:.2f}",
                move[7]
            ])
        
        # Total row
        data.append(['', '', '', '', 'TOTAL:', f"{total_miles:.0f}", f"${total_earnings:.2f}", ''])
        
        # Create table
        table = Table(data, colWidths=[1.1*inch, 0.9*inch, 0.8*inch, 0.8*inch, 1.5*inch, 0.6*inch, 0.9*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Summary
        factoring = total_earnings * 0.03
        net = total_earnings - factoring
        
        summary_html = f"""
        <b>PAYMENT SUMMARY</b><br/><br/>
        Total Moves: {len(moves)}<br/>
        Total Miles: {total_miles:,.0f}<br/>
        Gross Earnings: ${total_earnings:,.2f}<br/>
        Factoring (3%): -${factoring:,.2f}<br/>
        <b>NET PAYMENT: ${net:,.2f}</b>
        """
        elements.append(Paragraph(summary_html, info_style))
    else:
        elements.append(Paragraph(f"<b>No moves found for {driver_name} from {from_date} to {to_date}</b>", info_style))
    
    # Build with letterhead
    doc.build(elements, onFirstPage=add_letterhead, onLaterPages=add_letterhead)
    return filename

def generate_client_invoice(client_name, from_date, to_date):
    """Generate client invoice - uses same system"""
    return generate_driver_receipt(client_name, from_date, to_date)

def generate_status_report(from_date, to_date):
    """Generate status report with letterhead"""
    
    # Fix dates
    from_date = fix_date(from_date)
    to_date = fix_date(to_date)
    
    # Get data
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'active'")
    active = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'completed'")
    completed = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM trailers")
    trailers = cursor.fetchone()[0]
    
    conn.close()
    
    # Create PDF
    filename = f"status_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter,
                          topMargin=1.75*inch, bottomMargin=inch,
                          leftMargin=0.75*inch, rightMargin=0.75*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle('Title', fontSize=24, textColor=colors.HexColor('#003366'),
                                alignment=TA_CENTER, spaceAfter=30)
    elements.append(Paragraph("FLEET STATUS REPORT", title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Info
    info_html = f"""
    <b>REPORT PERIOD:</b> {from_date} to {to_date}<br/><br/>
    <b>FLEET STATISTICS</b><br/>
    Active Moves: {active}<br/>
    Completed Moves: {completed}<br/>
    Total Trailers: {trailers}<br/>
    """
    
    info_style = ParagraphStyle('Info', fontSize=11, leftIndent=20)
    elements.append(Paragraph(info_html, info_style))
    
    # Build with letterhead
    doc.build(elements, onFirstPage=add_letterhead, onLaterPages=add_letterhead)
    return filename

def generate_inventory_pdf():
    """Generate inventory report with letterhead"""
    
    # Get data
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            t.trailer_number,
            COALESCE(l.location_title, 
                CASE WHEN t.current_location_id = 0 THEN 'Fleet Memphis'
                     WHEN t.current_location_id = 1 THEN 'FedEx Memphis'
                     ELSE 'Location ' || t.current_location_id END) as location,
            t.status
        FROM trailers t
        LEFT JOIN locations l ON t.current_location_id = l.id
        ORDER BY t.current_location_id, t.trailer_number
    """)
    
    trailers = cursor.fetchall()
    conn.close()
    
    # Create PDF
    filename = f"inventory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=landscape(letter),
                          topMargin=1.75*inch, bottomMargin=inch,
                          leftMargin=0.75*inch, rightMargin=0.75*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle('Title', fontSize=24, textColor=colors.HexColor('#003366'),
                                alignment=TA_CENTER, spaceAfter=30)
    elements.append(Paragraph("TRAILER INVENTORY REPORT", title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Summary
    info_html = f"""
    <b>INVENTORY SUMMARY</b><br/>
    Total Trailers: {len(trailers)}<br/>
    Report Date: {datetime.now().strftime('%B %d, %Y')}
    """
    
    info_style = ParagraphStyle('Info', fontSize=11, leftIndent=20)
    elements.append(Paragraph(info_html, info_style))
    elements.append(Spacer(1, 0.3*inch))
    
    if trailers:
        # Table
        data = [['Trailer Number', 'Location', 'Status']]
        for trailer in trailers:
            data.append(list(trailer))
        
        table = Table(data, colWidths=[3*inch, 4*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        ]))
        
        elements.append(table)
    
    # Build with letterhead
    doc.build(elements, onFirstPage=add_letterhead, onLaterPages=add_letterhead)
    return filename