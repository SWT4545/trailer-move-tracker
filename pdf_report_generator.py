"""
PDF Status Report Generator
Smith and Williams Trucking
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import database as db
import utils
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas
import io
import os

def create_status_report_pdf(start_date=None, end_date=None, include_financial=False):
    """Generate a professional PDF status report"""
    
    # Create PDF buffer
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#DC143C'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#000000'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Add logo and header
    if os.path.exists("swt_logo.png"):
        logo = Image("swt_logo.png", width=1.5*inch, height=1.5*inch)
        logo.hAlign = 'CENTER'
        elements.append(logo)
        elements.append(Spacer(1, 12))
    
    # Title
    elements.append(Paragraph("Smith and Williams Trucking", title_style))
    elements.append(Paragraph("Status Update Report", styles['Heading2']))
    
    # Report info
    report_date = datetime.now().strftime("%B %d, %Y")
    report_time = datetime.now().strftime("%I:%M %p")
    
    info_text = f"Generated: {report_date} at {report_time}"
    elements.append(Paragraph(info_text, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Get data
    moves_df = db.get_all_trailer_moves()
    
    # Apply date filters if provided
    if start_date:
        moves_df = moves_df[pd.to_datetime(moves_df['date_assigned']) >= pd.to_datetime(start_date)]
    if end_date:
        moves_df = moves_df[pd.to_datetime(moves_df['date_assigned']) <= pd.to_datetime(end_date)]
    
    # Completed Routes Section
    elements.append(Paragraph("Completed Routes", heading_style))
    
    completed_moves = moves_df[moves_df['completion_date'].notna()].copy()
    
    if not completed_moves.empty:
        # Prepare data for table
        table_data = [['Route ID', 'Driver', 'From', 'To', 'New Trailer', 'Old Trailer', 'Date', 'Miles']]
        
        for _, move in completed_moves.iterrows():
            table_data.append([
                str(move['id']),
                move['assigned_driver'][:15],  # Truncate long names
                move['pickup_location'][:20],
                move['destination'][:20],
                move['new_trailer'],
                move['old_trailer'] if move['old_trailer'] else 'N/A',
                pd.to_datetime(move['completion_date']).strftime('%m/%d/%Y'),
                f"{move['miles']:,.0f}" if move['miles'] else '0'
            ])
        
        # Create table
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DC143C')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
    else:
        elements.append(Paragraph("No completed routes in this period.", styles['Normal']))
        elements.append(Spacer(1, 20))
    
    # In Process Routes Section
    elements.append(Paragraph("In Process Routes", heading_style))
    
    active_moves = moves_df[moves_df['completion_date'].isna()].copy()
    
    if not active_moves.empty:
        table_data = [['Route ID', 'Driver', 'Status', 'From', 'To', 'Assigned', 'Miles']]
        
        for _, move in active_moves.iterrows():
            table_data.append([
                str(move['id']),
                move['assigned_driver'][:15],
                'In Transit',
                move['pickup_location'][:20],
                move['destination'][:20],
                pd.to_datetime(move['date_assigned']).strftime('%m/%d/%Y'),
                f"{move['miles']:,.0f}" if move['miles'] else '0'
            ])
        
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffc107')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fff3cd')]),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
    else:
        elements.append(Paragraph("No routes currently in process.", styles['Normal']))
        elements.append(Spacer(1, 20))
    
    # Trailer Movement Summary
    elements.append(Paragraph("Trailer Movement Summary", heading_style))
    
    # Get trailer data
    trailers_df = db.get_all_trailers()
    
    if not trailers_df.empty:
        # Count by status
        available_new = len(trailers_df[(trailers_df['trailer_type'] == 'new') & (trailers_df['status'] == 'available')])
        available_old = len(trailers_df[(trailers_df['trailer_type'] == 'old') & (trailers_df['status'] == 'available')])
        assigned = len(trailers_df[trailers_df['status'] == 'assigned'])
        completed = len(trailers_df[trailers_df['status'] == 'completed'])
        
        summary_data = [
            ['Trailer Status', 'Count'],
            ['Available New Trailers', str(available_new)],
            ['Available Old Trailers', str(available_old)],
            ['Assigned Trailers', str(assigned)],
            ['Completed Today', str(completed)]
        ]
        
        table = Table(summary_data, colWidths=[3*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#17a2b8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
    
    # Summary Statistics
    elements.append(Paragraph("Summary Statistics", heading_style))
    
    # Calculate statistics
    total_completed = len(completed_moves)
    total_in_process = len(active_moves)
    total_miles = completed_moves['miles'].sum() if not completed_moves.empty else 0
    
    # Calculate on-time percentage (simplified)
    if not completed_moves.empty:
        completed_moves['date_assigned'] = pd.to_datetime(completed_moves['date_assigned'])
        completed_moves['completion_date'] = pd.to_datetime(completed_moves['completion_date'])
        completed_moves['days_to_complete'] = (completed_moves['completion_date'] - completed_moves['date_assigned']).dt.days
        on_time = len(completed_moves[completed_moves['days_to_complete'] <= 1])
        on_time_percentage = (on_time / total_completed * 100) if total_completed > 0 else 0
    else:
        on_time_percentage = 0
    
    stats_data = [
        ['Metric', 'Value'],
        ['Total Completed Routes', str(total_completed)],
        ['Total In Process', str(total_in_process)],
        ['Total Miles Completed', f"{total_miles:,.0f}"],
        ['On-Time Percentage', f"{on_time_percentage:.1f}%"]
    ]
    
    table = Table(stats_data, colWidths=[3*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 30))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    
    elements.append(Paragraph("This is an automated report from the Trailer Move Tracker system", footer_style))
    elements.append(Paragraph("Smith and Williams Trucking - Powered by Professional Logistics Solutions", footer_style))
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data

def show_pdf_report_page():
    """Streamlit page for generating PDF reports"""
    st.title("📄 PDF Status Report Generator")
    
    st.markdown("""
    Generate professional status reports for operational updates without financial data.
    These reports can be shared with customers and partners.
    """)
    
    # Report options
    col1, col2 = st.columns(2)
    
    with col1:
        report_type = st.selectbox(
            "Report Type",
            ["Status Update", "Trailer Summary", "Driver Performance", "Location Analysis"]
        )
        
        date_range = st.selectbox(
            "Date Range",
            ["Today", "This Week", "Last Week", "This Month", "Last Month", "Custom"]
        )
    
    with col2:
        if date_range == "Custom":
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date")
        else:
            # Calculate dates based on selection
            today = datetime.now()
            if date_range == "Today":
                start_date = today.date()
                end_date = today.date()
            elif date_range == "This Week":
                start_date = (today - timedelta(days=today.weekday())).date()
                end_date = today.date()
            elif date_range == "Last Week":
                start_date = (today - timedelta(days=today.weekday() + 7)).date()
                end_date = (today - timedelta(days=today.weekday() + 1)).date()
            elif date_range == "This Month":
                start_date = datetime(today.year, today.month, 1).date()
                end_date = today.date()
            else:  # Last Month
                last_month = today.replace(day=1) - timedelta(days=1)
                start_date = datetime(last_month.year, last_month.month, 1).date()
                end_date = last_month.date()
        
        st.info(f"Report Period: {start_date} to {end_date}")
    
    # Additional options
    st.markdown("### Report Options")
    col1, col2 = st.columns(2)
    
    with col1:
        include_charts = st.checkbox("Include visual charts", value=True)
        include_summary = st.checkbox("Include executive summary", value=True)
    
    with col2:
        include_details = st.checkbox("Include detailed tables", value=True)
        include_metrics = st.checkbox("Include performance metrics", value=True)
    
    # Generate button
    if st.button("🎯 Generate PDF Report", use_container_width=True):
        with st.spinner("Generating report..."):
            try:
                # Generate PDF based on report type
                if report_type == "Status Update":
                    pdf_data = create_status_report_pdf(start_date, end_date)
                else:
                    # For now, use the same function for all types
                    # In production, create specialized functions for each type
                    pdf_data = create_status_report_pdf(start_date, end_date)
                
                # Save to database
                report_id = db.save_status_report(
                    report_date=datetime.now().date(),
                    report_type=report_type,
                    report_data=f"{start_date} to {end_date}",
                    pdf_data=pdf_data,
                    generated_by=st.session_state.get('username', 'System')
                )
                
                st.success(f"✅ Report generated successfully! Report ID: {report_id}")
                
                # Download button
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_data,
                    file_name=f"status_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
                # Email options
                with st.expander("📧 Email Report"):
                    email_to = st.text_input("Send to email address:")
                    if st.button("Send Email"):
                        st.info("Email functionality will be implemented with email_manager module")
                
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")
    
    # Recent reports
    st.divider()
    st.markdown("### 📋 Recent Reports")
    
    recent_reports = db.get_status_reports(limit=5)
    
    if not recent_reports.empty:
        for _, report in recent_reports.iterrows():
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            with col1:
                st.markdown(f"**{report['report_type']}**")
            with col2:
                st.markdown(f"Generated: {pd.to_datetime(report['generated_at']).strftime('%m/%d/%Y %I:%M %p')}")
            with col3:
                st.markdown(f"By: {report['generated_by']}")
            with col4:
                if report['pdf_data']:
                    st.download_button(
                        "📥 Download",
                        data=report['pdf_data'],
                        file_name=f"report_{report['id']}.pdf",
                        mime="application/pdf",
                        key=f"download_{report['id']}"
                    )
    else:
        st.info("No reports generated yet")

if __name__ == "__main__":
    show_pdf_report_page()