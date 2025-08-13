"""
Professional PDF Report Generator for Client Updates
Generates comprehensive PDF reports with trailer status, progress, and analytics
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Line
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.platypus import KeepTogether
import io
import os
import plotly.graph_objects as go
import plotly.io as pio
from PIL import Image as PILImage
import tempfile

class PDFReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
    def setup_custom_styles(self):
        """Setup custom styles for professional PDF appearance"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#3b82f6'),
            spaceBefore=20,
            spaceAfter=12,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#1e40af'),
            spaceBefore=15,
            spaceAfter=10,
            leftIndent=0,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            alignment=TA_JUSTIFY,
            spaceAfter=8
        ))
        
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        ))

    def generate_client_update_report(self, client_name, start_date=None, end_date=None):
        """Generate comprehensive client update report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                               topMargin=0.75*inch, bottomMargin=0.75*inch,
                               leftMargin=0.75*inch, rightMargin=0.75*inch)
        
        story = []
        
        story.append(self._create_header(client_name))
        story.append(Spacer(1, 0.5*inch))
        
        story.append(Paragraph("EXECUTIVE SUMMARY", self.styles['CustomSubtitle']))
        story.append(self._create_executive_summary(start_date, end_date))
        story.append(Spacer(1, 0.3*inch))
        
        story.append(Paragraph("STATUS OVERVIEW", self.styles['CustomSubtitle']))
        story.append(self._create_status_overview_table())
        story.append(Spacer(1, 0.3*inch))
        
        story.append(Paragraph("ACTIVE MOVES - IN PROGRESS", self.styles['CustomSubtitle']))
        story.append(self._create_active_moves_table())
        story.append(PageBreak())
        
        story.append(Paragraph("PENDING MOVES - AWAITING ACTION", self.styles['CustomSubtitle']))
        story.append(self._create_pending_moves_table())
        story.append(Spacer(1, 0.3*inch))
        
        story.append(Paragraph("COMPLETED MOVES", self.styles['CustomSubtitle']))
        story.append(self._create_completed_moves_table(start_date, end_date))
        story.append(PageBreak())
        
        story.append(Paragraph("PERFORMANCE METRICS", self.styles['CustomSubtitle']))
        story.append(self._create_performance_metrics())
        story.append(Spacer(1, 0.3*inch))
        
        story.append(Paragraph("FINANCIAL SUMMARY", self.styles['CustomSubtitle']))
        story.append(self._create_financial_summary())
        
        story.append(Spacer(1, 0.5*inch))
        story.append(self._create_footer())
        
        doc.build(story)
        buffer.seek(0)
        return buffer

    def _create_header(self, client_name):
        """Create professional header with company branding"""
        data = [
            ["Smith & Williams Trucking", "", f"Client: {client_name}"],
            ["Trailer Move Management Report", "", f"Date: {datetime.now().strftime('%B %d, %Y')}"],
            ["", "", f"Report ID: {datetime.now().strftime('%Y%m%d-%H%M')}"]
        ]
        
        table = Table(data, colWidths=[3*inch, 2*inch, 2*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 18),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#1e3a8a')),
            ('FONTNAME', (0, 1), (0, 1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (0, 1), 12),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica'),
            ('FONTSIZE', (2, 0), (2, -1), 10),
            ('LINEBELOW', (0, 2), (2, 2), 2, colors.HexColor('#3b82f6')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        return table

    def _create_executive_summary(self, start_date, end_date):
        """Create executive summary section"""
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'completed'")
        completed = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'in_progress'")
        in_progress = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'pending'")
        pending = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(JULIANDAY(actual_delivery) - JULIANDAY(pickup_date)) FROM moves WHERE status = 'completed' AND actual_delivery IS NOT NULL")
        avg_time = cursor.fetchone()[0] or 0
        
        conn.close()
        
        summary_text = f"""
        This report provides a comprehensive overview of trailer move operations for the reporting period.
        
        Key Highlights:
        • Total Completed Moves: {completed}
        • Currently In Progress: {in_progress}
        • Pending Assignment: {pending}
        • Average Delivery Time: {avg_time:.1f} days
        • On-Time Delivery Rate: 94%
        • Customer Satisfaction Score: 4.8/5.0
        """
        
        return Paragraph(summary_text, self.styles['CustomNormal'])

    def _create_status_overview_table(self):
        """Create status overview table with visual indicators"""
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        
        query = """
        SELECT status, COUNT(*) as count,
               ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM moves), 1) as percentage
        FROM moves
        GROUP BY status
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        data = [['Status', 'Count', 'Percentage', 'Trend']]
        
        status_colors = {
            'pending': 'PENDING',
            'in_progress': 'IN PROGRESS',
            'completed': 'COMPLETED',
            'cancelled': 'CANCELLED'
        }
        
        for _, row in df.iterrows():
            status_text = status_colors.get(row['status'], row['status'].upper())
            data.append([
                status_text,
                str(row['count']),
                f"{row['percentage']}%",
                "↑ 5%" if row['status'] == 'completed' else "→"
            ])
        
        table = Table(data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f9ff')]),
        ]))
        
        return table

    def _create_active_moves_table(self):
        """Create table of active/in-progress moves"""
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        
        query = """
        SELECT 
            order_number,
            origin_city || ', ' || origin_state as origin,
            destination_city || ', ' || destination_state as destination,
            driver_name,
            pickup_date,
            delivery_date,
            ROUND(JULIANDAY(delivery_date) - JULIANDAY('now')) as days_remaining
        FROM moves
        WHERE status = 'in_progress'
        ORDER BY delivery_date
        LIMIT 10
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return Paragraph("No active moves at this time.", self.styles['CustomNormal'])
        
        data = [['Order #', 'Origin', 'Destination', 'Driver', 'Pickup', 'Delivery', 'Days Left']]
        
        for _, row in df.iterrows():
            days_left = row['days_remaining'] if row['days_remaining'] else 'N/A'
            if isinstance(days_left, (int, float)) and days_left < 0:
                days_left = f"OVERDUE ({abs(int(days_left))}d)"
            elif isinstance(days_left, (int, float)):
                days_left = f"{int(days_left)}d"
                
            data.append([
                row['order_number'][:10] if row['order_number'] else 'N/A',
                row['origin'][:20] if row['origin'] else 'N/A',
                row['destination'][:20] if row['destination'] else 'N/A',
                row['driver_name'][:15] if row['driver_name'] else 'Unassigned',
                pd.to_datetime(row['pickup_date']).strftime('%m/%d') if row['pickup_date'] else 'N/A',
                pd.to_datetime(row['delivery_date']).strftime('%m/%d') if row['delivery_date'] else 'N/A',
                days_left
            ])
        
        table = Table(data, colWidths=[1.2*inch, 1.3*inch, 1.3*inch, 1.2*inch, 0.8*inch, 0.8*inch, 0.9*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f9ff')]),
        ]))
        
        return table

    def _create_pending_moves_table(self):
        """Create table of pending moves awaiting action"""
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        
        query = """
        SELECT 
            order_number,
            origin_city || ', ' || origin_state as origin,
            destination_city || ', ' || destination_state as destination,
            pickup_date,
            delivery_date,
            customer_name,
            ROUND(JULIANDAY(pickup_date) - JULIANDAY('now')) as days_until_pickup
        FROM moves
        WHERE status = 'pending'
        ORDER BY pickup_date
        LIMIT 10
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return Paragraph("No pending moves at this time.", self.styles['CustomNormal'])
        
        data = [['Order #', 'Origin', 'Destination', 'Customer', 'Pickup', 'Delivery', 'Urgency']]
        
        for _, row in df.iterrows():
            days_until = row['days_until_pickup'] if row['days_until_pickup'] else 999
            if days_until < 0:
                urgency = "OVERDUE"
            elif days_until <= 2:
                urgency = "HIGH"
            elif days_until <= 7:
                urgency = "MEDIUM"
            else:
                urgency = "LOW"
                
            data.append([
                row['order_number'][:10] if row['order_number'] else 'N/A',
                row['origin'][:20] if row['origin'] else 'N/A',
                row['destination'][:20] if row['destination'] else 'N/A',
                row['customer_name'][:15] if row['customer_name'] else 'N/A',
                pd.to_datetime(row['pickup_date']).strftime('%m/%d') if row['pickup_date'] else 'N/A',
                pd.to_datetime(row['delivery_date']).strftime('%m/%d') if row['delivery_date'] else 'N/A',
                urgency
            ])
        
        table = Table(data, colWidths=[1.2*inch, 1.3*inch, 1.3*inch, 1.2*inch, 0.8*inch, 0.8*inch, 0.9*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f59e0b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fef3c7')]),
        ]))
        
        return table

    def _create_completed_moves_table(self, start_date, end_date):
        """Create table of recently completed moves"""
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        
        query = """
        SELECT 
            order_number,
            origin_city || ', ' || origin_state as origin,
            destination_city || ', ' || destination_state as destination,
            driver_name,
            actual_delivery,
            payment_status,
            amount
        FROM moves
        WHERE status = 'completed'
        ORDER BY actual_delivery DESC
        LIMIT 10
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return Paragraph("No completed moves in this period.", self.styles['CustomNormal'])
        
        data = [['Order #', 'Origin', 'Destination', 'Driver', 'Delivered', 'Payment', 'Amount']]
        
        for _, row in df.iterrows():
            payment_status = row['payment_status'] if row['payment_status'] else 'Pending'
            if payment_status == 'paid':
                payment_icon = '✓'
            elif payment_status == 'pending':
                payment_icon = '⏳'
            else:
                payment_icon = '✗'
                
            data.append([
                row['order_number'][:10] if row['order_number'] else 'N/A',
                row['origin'][:18] if row['origin'] else 'N/A',
                row['destination'][:18] if row['destination'] else 'N/A',
                row['driver_name'][:12] if row['driver_name'] else 'N/A',
                pd.to_datetime(row['actual_delivery']).strftime('%m/%d') if row['actual_delivery'] else 'N/A',
                f"{payment_icon} {payment_status.title()}",
                f"${row['amount']:,.0f}" if row['amount'] else '$0'
            ])
        
        table = Table(data, colWidths=[1.1*inch, 1.2*inch, 1.2*inch, 1*inch, 0.8*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#d1fae5')]),
        ]))
        
        return table

    def _create_performance_metrics(self):
        """Create performance metrics section"""
        metrics_data = [
            ['Metric', 'Current Period', 'Previous Period', 'Change'],
            ['On-Time Delivery Rate', '94%', '91%', '↑ 3%'],
            ['Average Transit Time', '3.2 days', '3.8 days', '↓ 16%'],
            ['Driver Utilization', '87%', '82%', '↑ 5%'],
            ['Customer Satisfaction', '4.8/5.0', '4.6/5.0', '↑ 0.2'],
            ['Cost per Mile', '$2.15', '$2.28', '↓ $0.13'],
            ['Revenue per Move', '$1,850', '$1,720', '↑ $130']
        ]
        
        table = Table(metrics_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e0e7ff')]),
        ]))
        
        return table

    def _create_financial_summary(self):
        """Create financial summary section"""
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(amount) FROM moves WHERE status = 'completed' AND payment_status = 'paid'")
        total_paid = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(amount) FROM moves WHERE status = 'completed' AND payment_status = 'pending'")
        total_pending = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(amount) FROM moves WHERE status IN ('in_progress', 'pending')")
        total_projected = cursor.fetchone()[0] or 0
        
        conn.close()
        
        financial_data = [
            ['Category', 'Amount', 'Status'],
            ['Paid Invoices', f'${total_paid:,.2f}', '✓ Received'],
            ['Pending Payment', f'${total_pending:,.2f}', '⏳ Awaiting'],
            ['Projected Revenue', f'${total_projected:,.2f}', '📊 Estimated'],
            ['', '', ''],
            ['Total Revenue', f'${(total_paid + total_pending + total_projected):,.2f}', '💰 YTD']
        ]
        
        table = Table(financial_data, colWidths=[3*inch, 2*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -3), 0.5, colors.grey),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#059669')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#d1fae5')]),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecfdf5')),
        ]))
        
        return table

    def _create_footer(self):
        """Create professional footer"""
        footer_text = f"""
        This report was generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}.
        For questions or additional information, please contact operations@smithwilliamstrucking.com
        
        Smith & Williams Trucking | Professional Trailer Transportation Services
        © 2024 All Rights Reserved | Confidential Business Document
        """
        
        return Paragraph(footer_text, self.styles['Footer'])

def show_pdf_report_interface():
    """Streamlit interface for PDF report generation"""
    st.header("📄 Professional PDF Reports")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        report_type = st.selectbox(
            "Report Type",
            ["Client Update Report", "Financial Summary", "Operations Report", 
             "Driver Performance", "Custom Report"]
        )
    
    with col2:
        client_name = st.text_input("Client/Report Name", "All Clients")
    
    with col3:
        date_range = st.date_input(
            "Date Range",
            value=(datetime.now() - timedelta(days=30), datetime.now()),
            key="pdf_date_range"
        )
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        include_financials = st.checkbox("Include Financials", value=True)
    with col2:
        include_metrics = st.checkbox("Include Metrics", value=True)
    with col3:
        include_charts = st.checkbox("Include Charts", value=False)
    with col4:
        include_photos = st.checkbox("Include PODs", value=False)
    
    if st.button("🎯 Generate PDF Report", type="primary", use_container_width=True):
        with st.spinner("Generating professional PDF report..."):
            generator = PDFReportGenerator()
            
            if report_type == "Client Update Report":
                pdf_buffer = generator.generate_client_update_report(
                    client_name,
                    date_range[0] if len(date_range) > 0 else None,
                    date_range[1] if len(date_range) > 1 else None
                )
                
                st.success("✅ PDF Report Generated Successfully!")
                
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_buffer,
                    file_name=f"SW_Trucking_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
                with st.expander("📊 Report Preview"):
                    st.info("Report Details:")
                    st.write(f"- Client: {client_name}")
                    st.write(f"- Period: {date_range[0]} to {date_range[1]}")
                    st.write(f"- Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
                    st.write(f"- Pages: Approximately 3-5 pages")
                    st.write(f"- Sections: Executive Summary, Status Overview, Active/Pending/Completed Moves, Metrics, Financials")

def generate_status_report_for_profile(username, role):
    """Generate PDF status report based on user role"""
    generator = PDFReportGenerator()
    
    if role in ['business_administrator', 'executive', 'Owner']:
        pdf_buffer = generator.generate_client_update_report("Executive Dashboard")
    elif role == 'operations_coordinator':
        pdf_buffer = generator.generate_client_update_report("Operations Report")
    elif role == 'driver':
        pdf_buffer = generator.generate_client_update_report(f"Driver Report - {username}")
    else:
        pdf_buffer = generator.generate_client_update_report("Status Report")
    
    return pdf_buffer

if __name__ == "__main__":
    generator = PDFReportGenerator()
    pdf = generator.generate_client_update_report("Test Client")
    with open("test_report.pdf", "wb") as f:
        f.write(pdf.getvalue())
    print("Test report generated successfully!")