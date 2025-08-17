"""
Inventory PDF Generator for Trailer Tracking System
Generates comprehensive inventory reports with trailer locations
"""

import sqlite3
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT

class InventoryPDFGenerator:
    def __init__(self):
        self.db_path = 'smith_williams_trucking.db'
        
    def _add_header_footer(self, canvas, doc):
        """Add header and footer to each page"""
        canvas.saveState()
        
        # Try to add logo
        import os
        logo_paths = ['swt_logo.png', 'swt_logo_white.png', 'logo.png']
        logo_added = False
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                try:
                    canvas.drawImage(logo_path, 50, 740, width=60, height=40, preserveAspectRatio=True)
                    logo_added = True
                    break
                except:
                    continue
        
        # Header text - adjust position if logo is present
        x_pos = 120 if logo_added else 50
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawString(x_pos, 750, "Smith & Williams Trucking")
        canvas.setFont("Helvetica", 12)
        canvas.drawString(x_pos, 735, "Trailer Inventory Report")
        canvas.drawRightString(750, 735, datetime.now().strftime("%B %d, %Y"))
        
        # Line under header
        canvas.setStrokeColor(colors.HexColor("#28a745"))
        canvas.setLineWidth(2)
        canvas.line(50, 730, 750, 730)
        
        # Footer
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawCentredString(400, 30, "Data Protected by Vernon - Senior IT Security Manager")
        canvas.setFont("Helvetica", 8)
        canvas.drawString(50, 15, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        canvas.drawRightString(750, 15, f"Page {doc.page}")
        
        canvas.restoreState()
        
    def generate_inventory_report(self):
        """Generate comprehensive inventory PDF"""
        filename = f"trailer_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=landscape(letter), 
                                topMargin=80, bottomMargin=50,
                                leftMargin=30, rightMargin=30)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'InventoryTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#28a745'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        elements.append(Paragraph("COMPLETE TRAILER INVENTORY", title_style))
        elements.append(Spacer(1, 20))
        
        # Connect to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Summary statistics
        cursor.execute('SELECT COUNT(*) FROM trailers')
        total_trailers = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM trailers WHERE is_new = 1')
        new_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM trailers WHERE is_new = 0')
        old_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM trailers WHERE status = "available"')
        available_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM trailers WHERE status = "in_transit"')
        in_transit_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM trailers WHERE status = "delivered"')
        delivered_count = cursor.fetchone()[0]
        
        # Summary section
        summary_style = ParagraphStyle(
            'Summary',
            parent=styles['Normal'],
            fontSize=12,
            leading=14
        )
        
        elements.append(Paragraph("<b>INVENTORY SUMMARY</b>", styles['Heading2']))
        elements.append(Paragraph(f"Total Fleet Size: <b>{total_trailers}</b> trailers", summary_style))
        elements.append(Paragraph(f"New Trailers: <b>{new_count}</b> | Old Trailers: <b>{old_count}</b>", summary_style))
        elements.append(Paragraph(f"Available: <b>{available_count}</b> | In Transit: <b>{in_transit_count}</b> | Delivered: <b>{delivered_count}</b>", summary_style))
        elements.append(Spacer(1, 30))
        
        # NEW TRAILERS AT FLEET MEMPHIS (Available for delivery)
        elements.append(Paragraph("<b>NEW TRAILERS AT FLEET MEMPHIS (Ready for Delivery)</b>", styles['Heading2']))
        cursor.execute('''
            SELECT t.trailer_number, t.trailer_type, l.location_title, t.status
            FROM trailers t
            LEFT JOIN locations l ON t.current_location_id = l.id
            WHERE t.is_new = 1 
            AND l.location_title = 'Fleet Memphis'
            AND t.status = 'available'
            ORDER BY t.trailer_number
        ''')
        new_at_fleet = cursor.fetchall()
        
        if new_at_fleet:
            data = [['Trailer #', 'Type', 'Location', 'Status']]
            for row in new_at_fleet:
                data.append(list(row))
            
            table = Table(data, colWidths=[120, 150, 200, 100])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("No new trailers currently at Fleet Memphis", styles['Normal']))
        
        elements.append(Spacer(1, 20))
        
        # OLD TRAILERS AT FEDEX LOCATIONS (Ready for pickup)
        elements.append(Paragraph("<b>OLD TRAILERS AT FEDEX LOCATIONS (Ready for Pickup)</b>", styles['Heading2']))
        cursor.execute('''
            SELECT t.trailer_number, t.trailer_type, l.location_title, 
                   l.city || ', ' || l.state as location_detail, t.status
            FROM trailers t
            LEFT JOIN locations l ON t.current_location_id = l.id
            WHERE t.is_new = 0 
            AND l.location_title LIKE 'FedEx%'
            ORDER BY l.location_title, t.trailer_number
        ''')
        old_at_fedex = cursor.fetchall()
        
        if old_at_fedex:
            data = [['Trailer #', 'Type', 'Location', 'City/State', 'Status']]
            for row in old_at_fedex:
                data.append(list(row))
            
            table = Table(data, colWidths=[100, 120, 180, 120, 80])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("No old trailers at FedEx locations", styles['Normal']))
        
        elements.append(PageBreak())
        
        # OLD TRAILERS AT FLEET MEMPHIS (Returned from swaps)
        elements.append(Paragraph("<b>OLD TRAILERS AT FLEET MEMPHIS (Returned from Swaps)</b>", styles['Heading2']))
        cursor.execute('''
            SELECT t.trailer_number, t.trailer_type, l.location_title, t.status
            FROM trailers t
            LEFT JOIN locations l ON t.current_location_id = l.id
            WHERE t.is_new = 0 
            AND l.location_title = 'Fleet Memphis'
            ORDER BY t.trailer_number
        ''')
        old_at_fleet = cursor.fetchall()
        
        if old_at_fleet:
            data = [['Trailer #', 'Type', 'Location', 'Status']]
            for row in old_at_fleet:
                data.append(list(row))
            
            table = Table(data, colWidths=[120, 150, 200, 100])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("No old trailers at Fleet Memphis", styles['Normal']))
        
        elements.append(Spacer(1, 20))
        
        # NEW TRAILERS DELIVERED TO FEDEX
        elements.append(Paragraph("<b>NEW TRAILERS DELIVERED TO FEDEX</b>", styles['Heading2']))
        cursor.execute('''
            SELECT t.trailer_number, t.trailer_type, l.location_title, 
                   l.city || ', ' || l.state as location_detail, t.status
            FROM trailers t
            LEFT JOIN locations l ON t.current_location_id = l.id
            WHERE t.is_new = 1 
            AND l.location_title LIKE 'FedEx%'
            ORDER BY l.location_title, t.trailer_number
        ''')
        new_at_fedex = cursor.fetchall()
        
        if new_at_fedex:
            data = [['Trailer #', 'Type', 'Location', 'City/State', 'Status']]
            for row in new_at_fedex:
                data.append(list(row))
            
            table = Table(data, colWidths=[100, 120, 180, 120, 80])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffc107')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("No new trailers delivered to FedEx", styles['Normal']))
        
        elements.append(PageBreak())
        
        # COMPLETE TRAILER LIST
        elements.append(Paragraph("<b>COMPLETE TRAILER LIST (ALL LOCATIONS)</b>", styles['Heading2']))
        cursor.execute('''
            SELECT t.trailer_number, 
                   CASE WHEN t.is_new = 1 THEN 'NEW' ELSE 'OLD' END as age,
                   t.trailer_type, 
                   l.location_title,
                   l.city || ', ' || l.state as location_detail,
                   t.status
            FROM trailers t
            LEFT JOIN locations l ON t.current_location_id = l.id
            ORDER BY t.is_new DESC, l.location_title, t.trailer_number
        ''')
        all_trailers = cursor.fetchall()
        
        data = [['Trailer #', 'New/Old', 'Type', 'Location', 'City/State', 'Status']]
        for row in all_trailers:
            data.append(list(row))
        
        table = Table(data, colWidths=[100, 60, 100, 180, 120, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6c757d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('FONTSIZE', (0, 1), (-1, -1), 9)
        ]))
        elements.append(table)
        
        conn.close()
        
        # Build PDF
        doc.build(elements, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
        
        return filename

# Function to be imported by app.py
def generate_inventory_pdf():
    """Generate inventory PDF with guaranteed logo"""
    """Generate inventory PDF report"""
    generator = InventoryPDFGenerator()
    return generator.generate_inventory_report()

if __name__ == "__main__":
    filename = generate_inventory_pdf()
    print(f"Inventory report generated: {filename}")