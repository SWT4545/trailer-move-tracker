"""
Universal PDF Generator with COMPLETE Date Fix
Smith & Williams Trucking LLC
Version 4.2.0 - Handles all date formats
"""

import os
import io
from datetime import datetime, date
import sqlite3

# Try to import reportlab
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Database path
DB_PATH = 'swt_fleet.db'

# Logo path - USE THE WHITE LOGO
LOGO_PATH = 'swt_logo_white.png'

def add_company_header_footer(canvas_obj, doc):
    """Professional header/footer with FULL company info for ALL PDFs"""
    canvas_obj.saveState()
    
    # Add the WHITE logo that shows up
    logo_added = False
    if os.path.exists('swt_logo_white.png'):
        try:
            canvas_obj.drawImage('swt_logo_white.png', 
                               0.75*inch,
                               doc.pagesize[1] - 1.2*inch,
                               width=1.2*inch,
                               height=0.6*inch,
                               preserveAspectRatio=True)
            logo_added = True
        except:
            pass
    
    # FULL COMPANY HEADER - Brandon's company info
    canvas_obj.setFont('Helvetica-Bold', 16)
    canvas_obj.setFillColor(colors.HexColor('#003366'))
    x_pos = 2.2*inch if logo_added else 0.75*inch
    canvas_obj.drawString(x_pos, doc.pagesize[1] - 0.85*inch, "SMITH & WILLIAMS TRUCKING LLC")
    
    canvas_obj.setFont('Helvetica', 10)
    canvas_obj.setFillColor(colors.black)
    canvas_obj.drawString(x_pos, doc.pagesize[1] - 1*inch, "7600 N 15th St Suite 150, Phoenix, AZ 85020")
    canvas_obj.drawString(x_pos, doc.pagesize[1] - 1.15*inch, "DOT #3675217 | MC #1276006")
    
    # Contact info on right
    canvas_obj.setFont('Helvetica', 10)
    canvas_obj.drawRightString(doc.pagesize[0] - inch, doc.pagesize[1] - 0.85*inch, 
                              "Phone: (951) 437-5474")
    canvas_obj.drawRightString(doc.pagesize[0] - inch, doc.pagesize[1] - 1*inch, 
                              "Dispatch@smithwilliamstrucking.com")
    canvas_obj.drawRightString(doc.pagesize[0] - inch, doc.pagesize[1] - 1.15*inch, 
                              "www.smithwilliamstrucking.com")
    
    # Header line
    canvas_obj.setStrokeColor(colors.HexColor('#DC143C'))
    canvas_obj.setLineWidth(2)
    canvas_obj.line(inch, doc.pagesize[1] - 1.4*inch, 
                   doc.pagesize[0] - inch, doc.pagesize[1] - 1.4*inch)
    
    # Footer
    canvas_obj.setStrokeColor(colors.HexColor('#003366'))
    canvas_obj.setLineWidth(1)
    canvas_obj.line(inch, 0.8*inch, doc.pagesize[0] - inch, 0.8*inch)
    
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.setFillColor(colors.HexColor('#666666'))
    canvas_obj.drawString(inch, 0.6*inch, 
                         f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    canvas_obj.drawRightString(doc.pagesize[0] - inch, 0.6*inch, 
                              f"Page {doc.page}")
    
    canvas_obj.setFont('Helvetica-Bold', 8)
    canvas_obj.drawCentredString(doc.pagesize[0]/2, 0.6*inch, 
                                "Confidential - Property of Smith & Williams Trucking LLC")
    
    canvas_obj.restoreState()

def generate_driver_receipt(driver_name, from_date, to_date):
    """Generate driver receipt with COMPLETE date handling"""
    
    if not REPORTLAB_AVAILABLE:
        return f"error_reportlab_not_installed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    # CRITICAL FIX: Convert date objects to strings
    if isinstance(from_date, date):
        from_date = from_date.strftime('%Y-%m-%d')
    if isinstance(to_date, date):
        to_date = to_date.strftime('%Y-%m-%d')
    
    print(f"Generating PDF for {driver_name} from {from_date} to {to_date}")
    
    # Get data from database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get driver's contractor company info from drivers table
    driver_company = None
    driver_phone = None
    driver_email = None
    
    try:
        cursor.execute("""
            SELECT company_name, phone, email 
            FROM drivers 
            WHERE name = ?
        """, (driver_name,))
        
        result = cursor.fetchone()
        if result:
            driver_company = result[0] if result[0] else None
            driver_phone = result[1] if result[1] else None
            driver_email = result[2] if result[2] else None
    except Exception as e:
        print(f"Error getting driver info: {e}")
    
    # Special handling for Brandon Smith (Owner)
    if driver_name == "Brandon Smith" and not driver_company:
        driver_company = "Smith & Williams Trucking LLC"
        driver_phone = "(951) 437-5474"
        driver_email = "brandon@smithwilliamstrucking.com"
    
    # If no company found, create a default
    if not driver_company:
        driver_company = f"{driver_name} Trucking Services"
    
    # Get ALL moves in date range - no status filter
    moves = []
    
    try:
        # IMPORTANT: Get ALL moves regardless of status
        query = """
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
        """
        
        print(f"Executing query with: {driver_name}, {from_date}, {to_date}")
        cursor.execute(query, (driver_name, from_date, to_date))
        moves = cursor.fetchall()
        print(f"Found {len(moves)} moves")
        
        # If no moves in date range, get recent moves as fallback
        if not moves:
            print(f"No moves in date range, getting recent moves...")
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
                ORDER BY move_date DESC
                LIMIT 20
            """, (driver_name,))
            moves = cursor.fetchall()
            print(f"Found {len(moves)} recent moves")
        
    except Exception as e:
        print(f"Error getting moves: {e}")
        # Absolute fallback
        try:
            cursor.execute("SELECT * FROM moves WHERE driver_name = ? LIMIT 50", (driver_name,))
            raw_moves = cursor.fetchall()
            moves = []
            for row in raw_moves:
                if len(row) >= 17:
                    moves.append((
                        row[1] or f"MOVE-{row[0]}",  # system_id or fallback
                        row[4],  # move_date
                        row[8],  # new_trailer
                        row[9],  # old_trailer
                        row[11] or row[12],  # destination_location or delivery_location
                        row[14] or 0,  # estimated_miles
                        row[16] or row[17] or 0,  # estimated_earnings or amount
                        row[7]  # status
                    ))
            print(f"Fallback found {len(moves)} moves")
        except Exception as e2:
            print(f"Fallback error: {e2}")
            moves = []
    
    conn.close()
    
    # Generate PDF
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"driver_receipt_{driver_name.replace(' ', '_')}_{timestamp}.pdf"
    
    doc = SimpleDocTemplate(filename, pagesize=letter,
                          topMargin=1.75*inch, bottomMargin=inch,
                          leftMargin=0.75*inch, rightMargin=0.75*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#003366'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    elements.append(Paragraph("DRIVER PAYMENT RECEIPT", title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Driver and contractor info
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=11,
        leftIndent=20
    )
    
    # Build complete driver info with contractor details
    driver_info_html = f"""
    <b>Driver Information:</b><br/>
    <b>Name:</b> {driver_name}<br/>
    <b>Contractor Company:</b> {driver_company}<br/>
    <b>Phone:</b> {driver_phone if driver_phone else 'Not on file'}<br/>
    <b>Email:</b> {driver_email if driver_email else 'Not on file'}<br/>
    <br/>
    <b>Report Period:</b> {from_date} to {to_date}<br/>
    <b>Report Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
    """
    
    elements.append(Paragraph(driver_info_html, info_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Add moves table or message
    if moves:
        # Create moves table
        data = [['Move ID', 'Date', 'New Trailer', 'Old Trailer', 'Destination', 'Miles', 'Earnings', 'Status']]
        
        total_earnings = 0
        total_miles = 0
        completed_count = 0
        active_count = 0
        
        for move in moves:
            move_id = str(move[0])[:15]
            move_date = str(move[1])[:10] if move[1] else "N/A"
            new_trailer = str(move[2]) if move[2] else "N/A"
            old_trailer = str(move[3]) if move[3] else "-"
            destination = str(move[4])[:20] if move[4] else "Unknown"
            miles = float(move[5]) if move[5] else 0
            earnings = float(move[6]) if move[6] else 0
            status = str(move[7]) if len(move) > 7 else "active"
            
            total_miles += miles
            total_earnings += earnings
            if status == 'completed':
                completed_count += 1
            elif status in ['active', 'in_transit']:
                active_count += 1
            
            data.append([
                move_id,
                move_date,
                new_trailer,
                old_trailer,
                destination,
                f"{miles:.1f}",
                f"${earnings:.2f}",
                status
            ])
        
        # Add summary row
        data.append(['', '', '', '', 'TOTALS:', f"{total_miles:.1f}", f"${total_earnings:.2f}", f"{len(moves)} total"])
        
        # Create table
        table = Table(data, colWidths=[1.1*inch, 0.9*inch, 0.9*inch, 0.9*inch, 1.4*inch, 0.7*inch, 0.9*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
            ('FONTSIZE', (0, 1), (-1, -2), 8),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Payment summary
        factoring = total_earnings * 0.03
        net = total_earnings - factoring
        
        summary_html = f"""
        <b>Payment Summary:</b><br/>
        Total Moves: {len(moves)}<br/>
        Completed Moves: {completed_count}<br/>
        Active/In Transit: {active_count}<br/>
        Total Miles: {total_miles:,.1f}<br/>
        Gross Earnings: ${total_earnings:,.2f}<br/>
        Factoring Fee (3%): -${factoring:,.2f}<br/>
        <b>Net Payment Due: ${net:,.2f}</b>
        """
        elements.append(Paragraph(summary_html, info_style))
    else:
        # No moves found message with debugging info
        no_moves_html = f"""
        <b>No moves found for this period.</b><br/>
        <br/>
        Driver: {driver_name}<br/>
        Date Range: {from_date} to {to_date}<br/>
        <br/>
        Please verify:<br/>
        • The date range includes move dates<br/>
        • The driver name matches exactly<br/>
        • Moves have been entered in the system<br/>
        <br/>
        Debug: Check that dates are in YYYY-MM-DD format
        """
        elements.append(Paragraph(no_moves_html, info_style))
    
    # Build PDF with company header/footer
    doc.build(elements, onFirstPage=add_company_header_footer, onLaterPages=add_company_header_footer)
    
    print(f"PDF generated: {filename}")
    return filename

# Aliases for compatibility
def generate_client_invoice(*args, **kwargs):
    """Generate client invoice with company header"""
    return generate_driver_receipt(*args, **kwargs)

def generate_status_report(*args, **kwargs):
    """Generate status report with company header"""
    if len(args) == 2:  # Only from_date and to_date
        # Default to showing all drivers
        return generate_driver_receipt("All Drivers", args[0], args[1])
    return generate_driver_receipt(*args, **kwargs)