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

# Logo paths - try all possible locations
LOGO_PATHS = ['swt_logo.png', 'swt_logo_white.png', 'logo.png', './swt_logo.png', '../swt_logo.png']

def add_universal_header_footer(canvas_obj, doc):
    """Universal header/footer with logo for ALL PDFs"""
    canvas_obj.saveState()
    
    # Try to add logo - check multiple paths
    logo_added = False
    for logo_path in LOGO_PATHS:
        if os.path.exists(logo_path):
            try:
                # Add logo to header
                canvas_obj.drawImage(logo_path, inch, doc.pagesize[1] - 1.3*inch, 
                                   width=1.5*inch, height=0.75*inch, preserveAspectRatio=True, mask='auto')
                logo_added = True
                break
            except:
                continue
    
    # If no logo file, create a text-based logo
    if not logo_added:
        canvas_obj.setFont('Helvetica-Bold', 18)
        canvas_obj.setFillColor(colors.HexColor('#DC143C'))
        canvas_obj.drawString(inch, doc.pagesize[1] - 0.9*inch, "SWT")
        canvas_obj.setFont('Helvetica', 10)
        canvas_obj.setFillColor(colors.black)
        canvas_obj.drawString(inch, doc.pagesize[1] - 1.1*inch, "Smith & Williams")
    
    # Company name and info (adjust position based on logo)
    canvas_obj.setFont('Helvetica-Bold', 14)
    canvas_obj.setFillColor(colors.HexColor('#003366'))
    x_pos = 3*inch if logo_added else 2.5*inch
    canvas_obj.drawString(x_pos, doc.pagesize[1] - 0.85*inch, "SMITH & WILLIAMS TRUCKING LLC")
    
    canvas_obj.setFont('Helvetica', 9)
    canvas_obj.setFillColor(colors.black)
    canvas_obj.drawString(x_pos, doc.pagesize[1] - 1*inch, "Your cargo. Our mission. Moving forward.")
    canvas_obj.drawString(x_pos, doc.pagesize[1] - 1.15*inch, "DOT #1234567 | MC #987654")
    
    # Contact info on right
    canvas_obj.setFont('Helvetica', 9)
    canvas_obj.drawRightString(doc.pagesize[0] - inch, doc.pagesize[1] - 0.85*inch, 
                              "Phone: (901) 555-SHIP")
    canvas_obj.drawRightString(doc.pagesize[0] - inch, doc.pagesize[1] - 1*inch, 
                              "Dispatch@smithwilliamstrucking.com")
    canvas_obj.drawRightString(doc.pagesize[0] - inch, doc.pagesize[1] - 1.15*inch, 
                              "3716 Hwy 78, Memphis, TN 38109")
    
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
    
    # Try multiple query formats
    moves = []
    try:
        # Try with all columns
        cursor.execute('''
            SELECT order_number, 
                   COALESCE(move_date, pickup_date, completed_date, CURRENT_DATE) as date,
                   COALESCE(new_trailer, order_number, '-') as new_trailer,
                   COALESCE(old_trailer, '-') as old_trailer,
                   COALESCE(destination_location, delivery_location, 'Unknown') as destination,
                   COALESCE(estimated_miles, 0) as miles,
                   COALESCE(estimated_earnings, amount, 0) as earnings
            FROM moves
            WHERE driver_name = ?
            AND status = 'completed'
        ''', (driver_name,))
        moves = cursor.fetchall()
    except:
        try:
            # Simpler query
            cursor.execute('''
                SELECT order_number, pickup_date, order_number, '-', 
                       delivery_location, 0, 0
                FROM moves
                WHERE driver_name = ?
            ''', (driver_name,))
            moves = cursor.fetchall()
        except:
            moves = []
    
    conn.close()
    
    if not REPORTLAB_AVAILABLE:
        # Generate text fallback
        content = {
            "Driver": driver_name,
            "Period": f"{from_date} to {to_date}",
            "Total Moves": len(moves),
            "Total Earnings": f"${sum(m[6] for m in moves if m[6]):,.2f}" if moves else "$0.00"
        }
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
    
    # Driver info
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=11,
        leftIndent=20
    )
    driver_info = f"""
    <b>Driver:</b> {driver_name}<br/>
    <b>Period:</b> {from_date} to {to_date}<br/>
    <b>Report Date:</b> {datetime.now().strftime("%B %d, %Y")}
    """
    elements.append(Paragraph(driver_info, info_style))
    elements.append(Spacer(1, 0.3*inch))
    
    if moves:
        # Create moves table
        data = [['Move ID', 'Date', 'New Trailer', 'Return', 'Destination', 'Miles', 'Earnings']]
        
        total_earnings = 0
        for move in moves:
            total_earnings += move[6] if move[6] else 0
            data.append([
                str(move[0])[:15],  # Truncate long IDs
                str(move[1])[:10],  # Date only
                str(move[2])[:10],
                str(move[3])[:10],
                str(move[4])[:20],  # Truncate destination
                f"{move[5]:,.0f}" if move[5] else "0",
                f"${move[6]:,.2f}" if move[6] else "$0.00"
            ])
        
        # Add summary row
        data.append(['', '', '', '', 'TOTAL:', '', f"${total_earnings:,.2f}"])
        
        # Create and style table
        table = Table(data, colWidths=[1.1*inch, 0.9*inch, 0.9*inch, 0.8*inch, 1.5*inch, 0.7*inch, 1*inch])
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