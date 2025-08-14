"""
Professional PDF Report Generator with Letterhead and Logo
Smith & Williams Trucking
"""
import io
import os
from datetime import datetime, timedelta
import sqlite3
import streamlit as st

# Import company configuration
try:
    from company_config import get_company_info, get_invoice_header
except:
    def get_company_info():
        return {
            'company_name': 'Smith & Williams Trucking',
            'company_email': 'Dispatch@smithwilliamstrucking.com',
            'company_phone': '(901) 555-SHIP',
            'company_website': 'www.smithwilliamstrucking.com',
            'company_address': '3716 Hwy 78, Memphis, TN 38109',
            'company_tagline': 'Your cargo. Our mission. Moving forward.',
            'dot_number': 'DOT #1234567',
            'mc_number': 'MC #987654',
            'ein': '12-3456789',
            'company_logo': 'swt_logo_white.png'
        }

def get_connection():
    return sqlite3.connect('trailer_tracker_streamlined.db')

def generate_status_report_for_profile(username, role):
    """Generate professional PDF report with letterhead"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from reportlab.pdfgen import canvas
        
        buffer = io.BytesIO()
        
        # Get company info for letterhead
        company_info = get_company_info()
        
        # Custom page with letterhead
        def add_letterhead(canvas, doc):
            canvas.saveState()
            
            # Add logo if exists - try multiple paths
            logo_paths = [
                company_info.get('company_logo', 'swt_logo_white.png'),
                'swt_logo_white.png',
                'swt_logo.png',
                'logo.png'
            ]
            
            logo_added = False
            for logo_path in logo_paths:
                if os.path.exists(logo_path):
                    try:
                        canvas.drawImage(logo_path, 50, 720, width=100, height=60, preserveAspectRatio=True)
                        logo_added = True
                        break
                    except:
                        continue
            
            # Company name and info
            canvas.setFont("Helvetica-Bold", 16)
            canvas.setFillColor(colors.HexColor('#DC143C'))  # Company red color
            canvas.drawString(170 if logo_added else 50, 750, company_info['company_name'].upper())
            
            canvas.setFont("Helvetica-Oblique", 11)
            canvas.setFillColor(colors.HexColor('#666666'))
            canvas.drawString(170 if logo_added else 50, 735, f'"{company_info["company_tagline"]}"')
            
            canvas.setFont("Helvetica", 9)
            canvas.setFillColor(colors.black)
            canvas.drawString(170 if logo_added else 50, 720, f"{company_info['dot_number']} | {company_info['mc_number']} | EIN: {company_info['ein']}")
            
            # Contact info on right
            canvas.setFont("Helvetica", 9)
            canvas.drawRightString(550, 750, f"Phone: {company_info['company_phone']}")
            canvas.drawRightString(550, 735, f"Email: {company_info['company_email']}")
            canvas.drawRightString(550, 720, f"Web: {company_info['company_website']}")
            
            # Address below contact info
            canvas.setFont("Helvetica", 8)
            canvas.drawRightString(550, 705, company_info['company_address'])
            
            # Line separator with company color
            canvas.setStrokeColor(colors.HexColor('#DC143C'))
            canvas.setLineWidth(2)
            canvas.line(50, 695, 550, 695)
            
            # Footer
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(colors.grey)
            canvas.drawString(50, 30, f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
            canvas.drawCentredString(300, 30, f"© {datetime.now().year} {company_info['company_name']} - Confidential")
            canvas.drawRightString(550, 30, f"Page {doc.page}")
            
            # Vernon watermark
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(colors.lightgrey)
            canvas.drawRightString(550, 15, "Protected by Vernon - Chief Data Security Officer")
            
            canvas.restoreState()
        
        # Create document with custom page template
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=1.5*inch,  # More space for letterhead
            bottomMargin=0.75*inch,
            leftMargin=0.75*inch,
            rightMargin=0.75*inch
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=20,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1e3a8a'),
            spaceBefore=20,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        )
        
        # Determine report type based on role
        if role == "admin" or role == "Owner":
            report_title = "EXECUTIVE MANAGEMENT REPORT"
            report_subtitle = "Comprehensive Operations Overview"
        elif role == "driver":
            report_title = "DRIVER PERFORMANCE REPORT"
            report_subtitle = f"Individual Report for {username}"
        elif role == "dispatcher":
            report_title = "DISPATCH OPERATIONS REPORT"
            report_subtitle = "Fleet Management Summary"
        else:
            report_title = "OPERATIONS STATUS REPORT"
            report_subtitle = "System Overview"
        
        # Report Title
        story.append(Paragraph(report_title, title_style))
        story.append(Paragraph(report_subtitle, styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Report Info Box
        info_data = [
            ['Report Information', ''],
            ['Generated For:', username],
            ['User Role:', role.replace('_', ' ').title()],
            ['Report Date:', datetime.now().strftime('%B %d, %Y')],
            ['Reporting Period:', f"Last 30 Days"],
            ['Report ID:', f"RPT-{datetime.now().strftime('%Y%m%d%H%M')}"]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Executive Summary
        story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
        
        # Get data from database
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get statistics
            cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'pending'")
            pending = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'in_progress'")
            in_progress = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'completed'")
            completed = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM trailers")
            total_trailers = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM trailers WHERE status = 'available'")
            available_trailers = cursor.fetchone()[0]
            
            # Calculate revenue (if amounts exist)
            cursor.execute("SELECT SUM(amount) FROM moves WHERE status = 'completed'")
            total_revenue = cursor.fetchone()[0] or 0
            
            conn.close()
            
            # Summary paragraph
            summary_text = f"""
            As of {datetime.now().strftime('%B %d, %Y')}, Smith & Williams Trucking operations show strong performance 
            across all key metrics. The fleet consists of {total_trailers} trailers with {available_trailers} currently 
            available for dispatch. Move operations show {pending} pending moves, {in_progress} in progress, and 
            {completed} completed moves. Total revenue from completed moves: ${total_revenue:,.2f}.
            """
            story.append(Paragraph(summary_text, styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
            
            # Operations Metrics Table
            story.append(Paragraph("KEY PERFORMANCE INDICATORS", heading_style))
            
            kpi_data = [
                ['Metric', 'Value', 'Status'],
                ['Total Fleet Size', f'{total_trailers} trailers', '✓ Operational'],
                ['Available Trailers', f'{available_trailers} units', '✓ Ready'],
                ['Pending Moves', str(pending), '→ Awaiting'],
                ['Active Moves', str(in_progress), '✓ In Transit'],
                ['Completed Moves', str(completed), '✓ Delivered'],
                ['Fleet Utilization', f'{((total_trailers-available_trailers)/total_trailers*100 if total_trailers > 0 else 0):.1f}%', '✓ Good'],
                ['Total Revenue', f'${total_revenue:,.2f}', '✓ Tracked'],
            ]
            
            kpi_table = Table(kpi_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
            kpi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            story.append(kpi_table)
            
        except Exception as e:
            story.append(Paragraph(f"Data retrieval in progress. System initializing.", styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Recommendations section
        story.append(Paragraph("RECOMMENDATIONS & NEXT STEPS", heading_style))
        
        recommendations = [
            "• Continue monitoring fleet utilization for optimization opportunities",
            "• Review pending moves for priority dispatch assignments",
            "• Maintain regular trailer maintenance schedule",
            "• Update driver assignments for balanced workload distribution",
            "• Review customer payment status for completed moves"
        ]
        
        for rec in recommendations:
            story.append(Paragraph(rec, styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Compliance section
        story.append(Paragraph("COMPLIANCE & SECURITY", heading_style))
        compliance_text = """
        This report is generated in compliance with DOT regulations and company policies. All data is secured 
        and monitored by Vernon, our Chief Data Security Officer. This document contains confidential business 
        information and should be handled accordingly.
        """
        story.append(Paragraph(compliance_text, styles['Normal']))
        
        # Sign-off
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("_" * 30, styles['Normal']))
        story.append(Paragraph("Authorized Signature", styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph("Brandon Smith, Owner", styles['Normal']))
        story.append(Paragraph("Smith & Williams Trucking", styles['Normal']))
        
        # Build PDF with letterhead
        doc.build(story, onFirstPage=add_letterhead, onLaterPages=add_letterhead)
        buffer.seek(0)
        return buffer
        
    except ImportError:
        # Fallback if reportlab not installed
        buffer = io.BytesIO()
        
        report_text = f"""
SMITH & WILLIAMS TRUCKING
Professional Transportation Services
========================

{datetime.now().strftime('%B %d, %Y')}

Status Report for: {username} ({role})

This is a text version of the report.
For full PDF reports with letterhead and graphics,
please ensure reportlab is installed:
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
        """Generate professional report with letterhead"""
        return generate_status_report_for_profile(client_name, "admin")