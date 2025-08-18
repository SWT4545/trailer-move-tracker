"""
Enhanced Inventory PDF Generator with Full Details
Smith & Williams Trucking LLC
All trailer information sections restored
"""

import os
import sqlite3
from datetime import datetime, date
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
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
    """Add company letterhead to EVERY page"""
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

def generate_inventory_pdf():
    """Generate DETAILED inventory report with all sections"""
    
    # Get data
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get ALL trailer data with location names
    cursor.execute("""
        SELECT 
            t.trailer_number,
            t.trailer_type,
            COALESCE(l.location_title, 'Location ' || t.current_location_id) as location,
            l.city,
            l.state,
            t.status,
            t.is_new,
            t.current_location_id
        FROM trailers t
        LEFT JOIN locations l ON t.current_location_id = l.id
        ORDER BY t.is_new DESC, l.location_title, t.trailer_number
    """)
    
    all_trailers = cursor.fetchall()
    
    # Get summary statistics
    cursor.execute("SELECT COUNT(*) FROM trailers")
    total_trailers = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM trailers WHERE is_new = 1")
    new_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM trailers WHERE is_new = 0")
    old_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM trailers WHERE status = 'available'")
    available_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM trailers WHERE status = 'in_use'")
    in_use_count = cursor.fetchone()[0]
    
    # Separate trailers by category
    new_at_fleet = []
    new_at_fedex = []
    old_at_fleet = []
    old_at_fedex = []
    
    for trailer in all_trailers:
        number, type_, location, city, state, status, is_new, loc_id = trailer
        
        if is_new == 1:
            if 'Fleet' in location or 'Memphis' in location and 'FedEx' not in location:
                new_at_fleet.append(trailer)
            elif 'FedEx' in location:
                new_at_fedex.append(trailer)
        else:  # Old trailers
            if 'Fleet' in location or 'Memphis' in location and 'FedEx' not in location:
                old_at_fleet.append(trailer)
            elif 'FedEx' in location:
                old_at_fedex.append(trailer)
    
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
    elements.append(Spacer(1, 0.2*inch))
    
    # Enhanced Summary with all stats
    info_style = ParagraphStyle('Info', fontSize=11, leftIndent=20)
    
    summary_html = f"""
    <b>INVENTORY SUMMARY</b><br/><br/>
    <b>Total Fleet Size:</b> {total_trailers} trailers<br/>
    <b>New Trailers:</b> {new_count} | <b>Old Trailers:</b> {old_count}<br/>
    <b>Available:</b> {available_count} | <b>In Use:</b> {in_use_count}<br/>
    <b>Report Date:</b> {datetime.now().strftime('%B %d, %Y')}
    """
    
    elements.append(Paragraph(summary_html, info_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Section 1: NEW TRAILERS AT FLEET MEMPHIS (Ready for delivery)
    section_style = ParagraphStyle('Section', fontSize=14, textColor=colors.HexColor('#28a745'),
                                  fontName='Helvetica-Bold', spaceAfter=10)
    
    elements.append(Paragraph("NEW TRAILERS AT FLEET MEMPHIS (Ready for Delivery)", section_style))
    
    if new_at_fleet:
        data = [['Trailer #', 'Type', 'Location', 'Status']]
        for trailer in new_at_fleet:
            data.append([trailer[0], trailer[1] or 'Standard', trailer[2], trailer[5]])
        
        table = Table(data, colWidths=[2*inch, 2*inch, 3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No new trailers currently at Fleet Memphis", info_style))
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Section 2: OLD TRAILERS AT FEDEX (Ready for pickup)
    elements.append(Paragraph("OLD TRAILERS AT FEDEX LOCATIONS (Ready for Pickup)", section_style))
    
    if old_at_fedex:
        data = [['Trailer #', 'Type', 'Location', 'City/State', 'Status']]
        for trailer in old_at_fedex:
            city_state = f"{trailer[3]}, {trailer[4]}" if trailer[3] and trailer[4] else "TN"
            data.append([trailer[0], trailer[1] or 'Standard', trailer[2], city_state, trailer[5]])
        
        table = Table(data, colWidths=[1.8*inch, 1.8*inch, 2.5*inch, 1.8*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No old trailers at FedEx locations", info_style))
    
    elements.append(PageBreak())
    
    # Section 3: OLD TRAILERS AT FLEET (Returned)
    elements.append(Paragraph("OLD TRAILERS AT FLEET MEMPHIS (Returned from Swaps)", section_style))
    
    if old_at_fleet:
        data = [['Trailer #', 'Type', 'Location', 'Status']]
        for trailer in old_at_fleet:
            data.append([trailer[0], trailer[1] or 'Standard', trailer[2], trailer[5]])
        
        table = Table(data, colWidths=[2*inch, 2*inch, 3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No old trailers at Fleet Memphis", info_style))
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Section 4: NEW TRAILERS DELIVERED TO FEDEX
    elements.append(Paragraph("NEW TRAILERS DELIVERED TO FEDEX", section_style))
    
    if new_at_fedex:
        data = [['Trailer #', 'Type', 'Location', 'City/State', 'Status']]
        for trailer in new_at_fedex:
            city_state = f"{trailer[3]}, {trailer[4]}" if trailer[3] and trailer[4] else "TN"
            data.append([trailer[0], trailer[1] or 'Standard', trailer[2], city_state, trailer[5]])
        
        table = Table(data, colWidths=[1.8*inch, 1.8*inch, 2.5*inch, 1.8*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffc107')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No new trailers delivered to FedEx", info_style))
    
    elements.append(PageBreak())
    
    # Section 5: COMPLETE TRAILER LIST
    elements.append(Paragraph("COMPLETE TRAILER LIST (ALL LOCATIONS)", section_style))
    
    if all_trailers:
        data = [['Trailer #', 'New/Old', 'Type', 'Location', 'Status']]
        for trailer in all_trailers[:50]:  # Limit to first 50 for space
            new_old = "NEW" if trailer[6] == 1 else "OLD"
            data.append([
                trailer[0],
                new_old,
                trailer[1] or 'Standard',
                trailer[2],
                trailer[5]
            ])
        
        table = Table(data, colWidths=[2*inch, 1.5*inch, 2*inch, 3*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6c757d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        ]))
        elements.append(table)
        
        if len(all_trailers) > 50:
            elements.append(Paragraph(f"<i>... and {len(all_trailers) - 50} more trailers</i>", info_style))
    
    # Build with letterhead
    doc.build(elements, onFirstPage=add_letterhead, onLaterPages=add_letterhead)
    return filename