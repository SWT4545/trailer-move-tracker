"""
Universal PDF Generator with Guaranteed Logo Support
Smith & Williams Trucking LLC
Handles all PDF generation with fallback support
"""

import os
import io
from datetime import datetime
import sqlite3

# Try to import reportlab, but don't fail if not available
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

# Database paths - try multiple options
DB_PATHS = ['swt_fleet.db', 'smith_williams_trucking.db', 'trailer_tracker_streamlined.db', 'trailer_tracker.db']
DB_PATH = None
for path in DB_PATHS:
    if os.path.exists(path):
        DB_PATH = path
        break
if not DB_PATH:
    DB_PATH = 'swt_fleet.db'  # Default

# Logo path - ONLY use the transparent logo (not the white one)
LOGO_PATH = 'swt_logo.png'  # The transparent logo without "white" in name

def add_universal_header_footer(canvas_obj, doc):
    """Universal header/footer with logo for ALL PDFs"""
    canvas_obj.saveState()
    
    # Add the transparent logo
    logo_added = False
    if os.path.exists(LOGO_PATH):
        try:
            # Add logo to header - properly sized and positioned
            canvas_obj.drawImage(LOGO_PATH, 
                               0.75*inch,  # Left margin
                               doc.pagesize[1] - 1.2*inch,  # From top
                               width=1.2*inch,  # Logo width
                               height=0.6*inch,  # Logo height
                               preserveAspectRatio=True, 
                               mask='auto')  # Preserve transparency
            logo_added = True
        except Exception as e:
            print(f"Logo error: {e}")
    
    # If no logo file, create a text-based logo
    if not logo_added:
        canvas_obj.setFont('Helvetica-Bold', 18)
        canvas_obj.setFillColor(colors.HexColor('#DC143C'))
        canvas_obj.drawString(inch, doc.pagesize[1] - 0.9*inch, "SWT")
        canvas_obj.setFont('Helvetica', 10)
        canvas_obj.setFillColor(colors.black)
        canvas_obj.drawString(inch, doc.pagesize[1] - 1.1*inch, "Smith & Williams")
    
    # Company name and info (properly positioned next to logo)
    canvas_obj.setFont('Helvetica-Bold', 14)
    canvas_obj.setFillColor(colors.HexColor('#003366'))
    x_pos = 2.2*inch if logo_added else 0.75*inch
    canvas_obj.drawString(x_pos, doc.pagesize[1] - 0.85*inch, "SMITH & WILLIAMS TRUCKING LLC")
    
    canvas_obj.setFont('Helvetica', 9)
    canvas_obj.setFillColor(colors.black)
    canvas_obj.drawString(x_pos, doc.pagesize[1] - 1*inch, "Your cargo. Our mission. Moving forward.")
    canvas_obj.drawString(x_pos, doc.pagesize[1] - 1.15*inch, "DOT #3675217 | MC #1276006")
    
    # Contact info on right
    canvas_obj.setFont('Helvetica', 9)
    canvas_obj.drawRightString(doc.pagesize[0] - inch, doc.pagesize[1] - 0.85*inch, 
                              "Phone: (951) 437-5474")
    canvas_obj.drawRightString(doc.pagesize[0] - inch, doc.pagesize[1] - 1*inch, 
                              "Dispatch@smithwilliamstrucking.com")
    canvas_obj.drawRightString(doc.pagesize[0] - inch, doc.pagesize[1] - 1.15*inch, 
                              "7600 N 15th St Suite 150, Phoenix, AZ 85020")
    
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
    
    # Vernon watermark
    canvas_obj.setFont('Helvetica', 7)
    canvas_obj.setFillColor(colors.lightgrey)
    canvas_obj.drawCentredString(doc.pagesize[0]/2, 0.4*inch, 
                                "Data Protected by Vernon - Senior IT Security Manager")
    
    canvas_obj.restoreState()

def generate_text_fallback(title, content_dict, filename_prefix):
    """Generate text file when PDF not available"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write(f"{title}\n")
        f.write("SMITH & WILLIAMS TRUCKING LLC\n")
        f.write("=" * 60 + "\n\n")
        
        for key, value in content_dict.items():
            f.write(f"{key}: {value}\n")
        
        f.write("\n" + "-" * 60 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("Data Protected by Vernon - Senior IT Security Manager\n")
        f.write("© Smith & Williams Trucking LLC\n")
    
    return filename

def generate_driver_receipt(driver_name, from_date, to_date):
    """Generate driver receipt with guaranteed output"""
    
    # Get data from database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get driver company info
    driver_company = None
    driver_phone = None
    driver_email = None
    try:
        cursor.execute("PRAGMA table_info(drivers)")
        driver_cols = [col[1] for col in cursor.fetchall()]
        
        if 'company_name' in driver_cols:
            cursor.execute('''
                SELECT company_name, phone, email 
                FROM drivers 
                WHERE driver_name = ?
            ''', (driver_name,))
            result = cursor.fetchone()
            if result:
                driver_company = result[0]
                driver_phone = result[1] if len(result) > 1 else None
                driver_email = result[2] if len(result) > 2 else None
    except:
        pass
    
    # Get moves with comprehensive query that works with any schema
    moves = []
    
    # First check what columns exist
    cursor.execute("PRAGMA table_info(moves)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Build dynamic query based on available columns
    try:
        select_parts = []
        
        # ID field
        if 'order_number' in columns:
            select_parts.append('order_number as id')
        elif 'system_id' in columns:
            select_parts.append('system_id as id')
        else:
            select_parts.append("'MOVE-' || rowid as id")
        
        # Date field
        date_fields = ['move_date', 'pickup_date', 'completed_date', 'created_at']
        date_field = next((f for f in date_fields if f in columns), "date('now')")
        select_parts.append(f"COALESCE({date_field}, date('now')) as move_date")
        
        # New trailer
        if 'new_trailer' in columns:
            select_parts.append("COALESCE(new_trailer, 'N/A') as new_trailer")
        else:
            select_parts.append("'N/A' as new_trailer")
        
        # Old trailer
        if 'old_trailer' in columns:
            select_parts.append("COALESCE(old_trailer, '-') as old_trailer")
        else:
            select_parts.append("'-' as old_trailer")
        
        # Destination
        dest_fields = ['destination_location', 'delivery_location', 'drop_location']
        dest_field = next((f for f in dest_fields if f in columns), "'Unknown'")
        select_parts.append(f"COALESCE({dest_field}, 'Unknown') as destination")
        
        # Miles
        if 'estimated_miles' in columns:
            select_parts.append("COALESCE(estimated_miles, 0) as miles")
        elif 'miles' in columns:
            select_parts.append("COALESCE(miles, 0) as miles")
        else:
            select_parts.append("0 as miles")
        
        # Earnings
        earnings_fields = ['estimated_earnings', 'amount', 'earnings', 'pay']
        earnings_field = next((f for f in earnings_fields if f in columns), "0")
        select_parts.append(f"COALESCE({earnings_field}, 0) as earnings")
        
        # Build and execute query
        query = f"""
            SELECT {', '.join(select_parts)}
            FROM moves
            WHERE driver_name = ?
            AND status IN ('completed', 'paid')
            ORDER BY move_date DESC
        """
        
        cursor.execute(query, (driver_name,))
        moves = cursor.fetchall()
        
    except Exception as e:
        # Ultimate fallback - just get basic info
        try:
            cursor.execute('''
                SELECT rowid, date('now'), 'N/A', '-', 'Unknown', 0, 0
                FROM moves
                WHERE driver_name = ?
                LIMIT 50
            ''', (driver_name,))
            moves = cursor.fetchall()
        except:
            moves = []
    
    conn.close()
    
    if not REPORTLAB_AVAILABLE:
        # Generate text fallback
        content = {
            "Driver": driver_name,
        }
        
        if driver_company:
            content["Company"] = driver_company
        if driver_phone:
            content["Phone"] = driver_phone
        if driver_email:
            content["Email"] = driver_email
            
        content.update({
            "Period": f"{from_date} to {to_date}",
            "Total Moves": len(moves),
            "Total Earnings": f"${sum(m[6] for m in moves if m[6]):,.2f}" if moves else "$0.00"
        })
        return generate_text_fallback("DRIVER RECEIPT", content, f"driver_receipt_{driver_name}")
    
    # Generate PDF with reportlab
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"driver_receipt_{driver_name.replace(' ', '_')}_{timestamp}.pdf"
    
    doc = SimpleDocTemplate(filename, pagesize=letter,
                          topMargin=1.75*inch, bottomMargin=inch,
                          leftMargin=0.75*inch, rightMargin=0.75*inch)
    
    # Build PDF content
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
    
    # Driver info with company details
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=11,
        leftIndent=20
    )
    
    # Build driver info including company details
    driver_info_parts = [
        f"<b>Driver:</b> {driver_name}"
    ]
    
    if driver_company:
        driver_info_parts.append(f"<b>Company:</b> {driver_company}")
    
    if driver_phone:
        driver_info_parts.append(f"<b>Phone:</b> {driver_phone}")
    
    if driver_email:
        driver_info_parts.append(f"<b>Email:</b> {driver_email}")
    
    driver_info_parts.extend([
        f"<b>Period:</b> {from_date} to {to_date}",
        f"<b>Report Date:</b> {datetime.now().strftime('%B %d, %Y')}"
    ])
    
    driver_info = "<br/>".join(driver_info_parts)
    
    elements.append(Paragraph(driver_info, info_style))
    elements.append(Spacer(1, 0.3*inch))
    
    if moves:
        # Create moves table with better formatting
        data = [['Move ID', 'Date', 'Trailers', 'Route', 'Earnings']]
        
        total_earnings = 0
        total_miles = 0
        for move in moves:
            earnings = float(move[6]) if move[6] else 0
            miles = float(move[5]) if move[5] else 0
            total_earnings += earnings
            total_miles += miles
            
            # Format trailers column
            trailer_info = f"{move[2] if move[2] and move[2] != '-' else 'N/A'}"
            if move[3] and move[3] != '-':
                trailer_info += f" / {move[3]}"
            
            # Format route
            route = str(move[4])[:30] if move[4] else "Unknown"
            
            # Add row with properly formatted data
            data.append([
                str(move[0])[:20],  # Move ID
                str(move[1])[:10] if move[1] else "N/A",  # Date
                trailer_info,  # Combined trailers
                route,  # Route
                f"${earnings:,.2f}"  # Earnings
            ])
        
        # Add summary row
        data.append(['', '', '', 'TOTAL:', f"${total_earnings:,.2f}"])
        
        # Create and style table with better column widths
        table = Table(data, colWidths=[1.3*inch, 1*inch, 1.8*inch, 2.2*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Summary section
        factoring = total_earnings * 0.03
        net = total_earnings - factoring
        
        summary_text = f"""
        <b>Earnings Summary:</b><br/>
        Gross Earnings: ${total_earnings:,.2f}<br/>
        Factoring Fee (3%): -${factoring:,.2f}<br/>
        <b>Net Payment: ${net:,.2f}</b>
        """
        elements.append(Paragraph(summary_text, info_style))
    else:
        elements.append(Paragraph("No completed moves found for this period.", styles['Normal']))
    
    # Build PDF with header/footer
    doc.build(elements, onFirstPage=add_universal_header_footer, onLaterPages=add_universal_header_footer)
    
    return filename

# Make this the default for all PDF generation
def generate_client_invoice(*args, **kwargs):
    """Alias for driver receipt"""
    return generate_driver_receipt(*args, **kwargs)

def generate_status_report(*args, **kwargs):
    """Alias for driver receipt"""
    return generate_driver_receipt(*args, **kwargs)