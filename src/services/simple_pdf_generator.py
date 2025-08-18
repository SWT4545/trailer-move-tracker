"""
Simple PDF Report Generator - Works with or without reportlab
"""
import io
from datetime import datetime, timedelta
import sqlite3

def get_connection():
    return sqlite3.connect('trailer_tracker_streamlined.db')

def generate_status_report_for_profile(username, role):
    """Generate a simple PDF report or fallback to bytes if reportlab not available"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title = f"Smith & Williams Trucking Report"
        story.append(Paragraph(title, styles['Title']))
        story.append(Spacer(1, 0.3*inch))
        
        # User info
        story.append(Paragraph(f"Generated for: {username} ({role})", styles['Normal']))
        story.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Get data from database
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get move statistics
            cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'pending'")
            pending = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'in_progress'")
            in_progress = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'completed'")
            completed = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM trailers")
            total_trailers = cursor.fetchone()[0]
            
            conn.close()
            
            # Add statistics section
            story.append(Paragraph("Move Statistics", styles['Heading2']))
            stats_data = [
                ['Status', 'Count'],
                ['Pending', str(pending)],
                ['In Progress', str(in_progress)],
                ['Completed', str(completed)],
                ['Total Trailers', str(total_trailers)]
            ]
            
            stats_table = Table(stats_data)
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(stats_table)
            
        except Exception as e:
            story.append(Paragraph(f"No data available yet", styles['Normal']))
        
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("© 2025 Smith & Williams Trucking", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
        
    except ImportError:
        # Fallback if reportlab not installed - create a simple text report
        buffer = io.BytesIO()
        
        report_text = f"""
SMITH & WILLIAMS TRUCKING
========================
Status Report

Generated for: {username} ({role})
Date: {datetime.now().strftime('%B %d, %Y %I:%M %p')}

SYSTEM STATUS
-------------
The system is operational and tracking moves and trailers.

For a full PDF report, please install reportlab:
pip install reportlab

© 2025 Smith & Williams Trucking
Protected by Vernon - Chief Data Security Officer
        """
        
        buffer.write(report_text.encode())
        buffer.seek(0)
        return buffer

class PDFReportGenerator:
    """Compatibility class for existing code"""
    def generate_client_update_report(self, client_name, start_date=None, end_date=None):
        """Generate a simple report"""
        return generate_status_report_for_profile(client_name, "admin")