"""
Driver Invoice/Receipt Generation System
Generates professional PDF invoices for drivers showing moves and payment summary
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from io import BytesIO
import os

def get_connection():
    """Get database connection"""
    try:
        return sqlite3.connect('trailer_moves.db')
    except:
        return sqlite3.connect('trailer_tracker_streamlined.db')

def generate_driver_invoice(driver_name, start_date, end_date, invoice_type="summary"):
    """
    Generate professional driver invoice/receipt PDF
    
    Args:
        driver_name: Name of the driver
        start_date: Start date for the period
        end_date: End date for the period
        invoice_type: 'summary' or 'detailed'
    
    Returns:
        BytesIO buffer containing the PDF
    """
    
    # Create PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e3d59'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1e3d59'),
        spaceAfter=12
    )
    
    # Company header
    elements.append(Paragraph("SMITH & WILLIAMS TRUCKING LLC", title_style))
    
    company_info = """
    <para align=center>
    3195 Airways Blvd, Memphis, TN 38116<br/>
    Phone: (901) 555-1234 | Email: dispatch@swtrucking.com<br/>
    MC: 1234567 | DOT: 7654321
    </para>
    """
    elements.append(Paragraph(company_info, styles['Normal']))
    elements.append(Spacer(1, 0.5*inch))
    
    # Invoice header
    invoice_num = f"INV-{datetime.now().strftime('%Y%m%d')}-{driver_name.split()[0].upper()}"
    
    invoice_header_data = [
        ['CONTRACTOR PAYMENT STATEMENT', ''],
        ['Invoice Number:', invoice_num],
        ['Invoice Date:', datetime.now().strftime('%B %d, %Y')],
        ['Period:', f"{start_date.strftime('%m/%d/%Y')} - {end_date.strftime('%m/%d/%Y')}"],
        ['', '']
    ]
    
    invoice_header_table = Table(invoice_header_data, colWidths=[3*inch, 3*inch])
    invoice_header_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 16),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (1, 0), 12),
    ]))
    
    elements.append(invoice_header_table)
    elements.append(Spacer(1, 0.25*inch))
    
    # Get driver information from database
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get driver profile
    cursor.execute("""
        SELECT full_name, company_name, company_address, 
               company_phone, mc_number, dot_number
        FROM driver_profiles
        WHERE full_name = ? OR full_name LIKE ?
        LIMIT 1
    """, (driver_name, f"%{driver_name}%"))
    
    driver_info = cursor.fetchone()
    
    if driver_info:
        contractor_data = [
            ['CONTRACTOR INFORMATION', ''],
            ['Name:', driver_info[0] or driver_name],
            ['Company:', driver_info[1] or 'Independent Contractor'],
            ['Address:', driver_info[2] or 'On File'],
            ['Phone:', driver_info[3] or 'On File'],
            ['MC #:', driver_info[4] or 'N/A'],
            ['DOT #:', driver_info[5] or 'N/A']
        ]
    else:
        contractor_data = [
            ['CONTRACTOR INFORMATION', ''],
            ['Name:', driver_name],
            ['Company:', 'Independent Contractor'],
            ['Status:', 'Active']
        ]
    
    contractor_table = Table(contractor_data, colWidths=[1.5*inch, 4.5*inch])
    contractor_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#f0f0f0')),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    
    elements.append(contractor_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Get moves for the period
    cursor.execute("""
        SELECT 
            order_number,
            DATE(completed_date) as date,
            old_trailer || ' → ' || new_trailer as route,
            delivery_location,
            amount,
            service_fee,
            driver_net_earnings
        FROM moves
        WHERE driver_name = ?
        AND DATE(completed_date) BETWEEN ? AND ?
        AND status IN ('completed', 'paid')
        ORDER BY completed_date
    """, (driver_name, start_date, end_date))
    
    moves = cursor.fetchall()
    
    if moves:
        # Moves table
        elements.append(Paragraph("COMPLETED MOVES", header_style))
        
        moves_data = [['Date', 'Order #', 'Route', 'Location', 'Gross', 'Fees', 'Net']]
        
        total_gross = 0
        total_fees = 0
        total_net = 0
        
        for move in moves:
            date_str = move[1] if move[1] else 'N/A'
            gross = move[4] or 0
            service_fee = move[5] or 2.00  # Default $2 service fee
            
            # Calculate fees (service + processing)
            processing_fee = gross * 0.03 * 0.30  # Driver's share of 3%
            total_fee = service_fee + processing_fee
            
            # Net earnings
            driver_gross = gross * 0.30
            net = driver_gross - total_fee
            
            total_gross += gross
            total_fees += total_fee
            total_net += net
            
            moves_data.append([
                date_str,
                move[0],
                move[2][:20],  # Truncate route if too long
                move[3][:15],  # Truncate location
                f"${gross:,.2f}",
                f"${total_fee:.2f}",
                f"${net:.2f}"
            ])
        
        # Add totals row
        moves_data.append(['', '', '', 'TOTALS:', 
                          f"${total_gross:,.2f}", 
                          f"${total_fees:.2f}", 
                          f"${total_net:,.2f}"])
        
        moves_table = Table(moves_data, colWidths=[0.8*inch, 1*inch, 1.5*inch, 1.2*inch, 0.9*inch, 0.8*inch, 0.9*inch])
        moves_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3d59')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 9),
            ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
            
            # Totals row
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(moves_table)
        elements.append(Spacer(1, 0.5*inch))
        
        # Payment summary
        elements.append(Paragraph("PAYMENT SUMMARY", header_style))
        
        summary_data = [
            ['Gross Earnings (Total Move Value):', f"${total_gross:,.2f}"],
            ['Driver Share (30% of Gross):', f"${total_gross * 0.30:,.2f}"],
            ['', ''],
            ['Less: Service Fees:', f"-${len(moves) * 2.00:.2f}"],
            ['Less: Processing Fees (3%):', f"-${total_gross * 0.03 * 0.30:.2f}"],
            ['', ''],
            ['NET PAYMENT DUE:', f"${total_net:,.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3.5*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (1, -1), 12),
            ('LINEABOVE', (0, -1), (1, -1), 2, colors.black),
            ('BACKGROUND', (0, -1), (1, -1), colors.HexColor('#e8f4f8')),
            ('TOPPADDING', (0, -1), (1, -1), 8),
            ('BOTTOMPADDING', (0, -1), (1, -1), 8),
        ]))
        
        elements.append(summary_table)
        
        # Payment details
        elements.append(Spacer(1, 0.5*inch))
        
        payment_info = """
        <para align=center>
        <b>PAYMENT METHOD: Navy Federal Account Transfer</b><br/>
        Payment will be processed within 24-48 hours to your account on file.<br/>
        For questions, contact accounting@swtrucking.com or (901) 555-1234
        </para>
        """
        elements.append(Paragraph(payment_info, styles['Normal']))
        
    else:
        elements.append(Paragraph("No completed moves found for this period.", styles['Normal']))
    
    # Footer
    elements.append(Spacer(1, 1*inch))
    
    footer_text = """
    <para align=center fontSize=9>
    This statement is for your records. Please retain for tax purposes.<br/>
    Thank you for your service to Smith & Williams Trucking.
    </para>
    """
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF value
    pdf = buffer.getvalue()
    buffer.close()
    
    conn.close()
    
    return pdf, invoice_num, total_net if moves else 0

def show_invoice_management():
    """Invoice management interface for generating driver invoices"""
    st.header("📄 Driver Invoice Management")
    
    tabs = st.tabs([
        "📋 Generate Invoice",
        "📊 Batch Processing",
        "📂 Invoice History"
    ])
    
    with tabs[0]:  # Generate Invoice
        st.markdown("### Generate Driver Invoice/Receipt")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Select driver
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT driver_name 
                FROM moves 
                WHERE driver_name IS NOT NULL
                ORDER BY driver_name
            """)
            drivers = [d[0] for d in cursor.fetchall()]
            
            selected_driver = st.selectbox("Select Driver", drivers)
            
            # Date range
            date_range = st.date_input(
                "Select Period",
                value=(date.today() - timedelta(days=7), date.today()),
                key="invoice_dates"
            )
        
        with col2:
            # Invoice options
            include_unpaid = st.checkbox("Include Unpaid Moves", value=False)
            show_details = st.checkbox("Show Detailed Breakdown", value=True)
            
            # Preview stats
            if selected_driver and len(date_range) == 2:
                cursor.execute("""
                    SELECT COUNT(*), SUM(amount), SUM(driver_net_earnings)
                    FROM moves
                    WHERE driver_name = ?
                    AND DATE(completed_date) BETWEEN ? AND ?
                    AND status IN ('completed', 'paid')
                """, (selected_driver, date_range[0], date_range[1]))
                
                stats = cursor.fetchone()
                if stats and stats[0]:
                    st.info(f"**{stats[0]} moves** found")
                    st.info(f"**Gross:** ${stats[1] or 0:,.2f}")
                    st.info(f"**Net:** ${stats[2] or 0:,.2f}")
        
        # Generate button
        if st.button("📄 Generate Invoice", type="primary", use_container_width=True):
            if selected_driver and len(date_range) == 2:
                with st.spinner("Generating invoice..."):
                    pdf_data, invoice_num, total_amount = generate_driver_invoice(
                        selected_driver,
                        date_range[0],
                        date_range[1],
                        "detailed" if show_details else "summary"
                    )
                    
                    if pdf_data:
                        st.success(f"✅ Invoice {invoice_num} generated successfully!")
                        
                        # Download button
                        st.download_button(
                            label="📥 Download Invoice PDF",
                            data=pdf_data,
                            file_name=f"{invoice_num}_{selected_driver.replace(' ', '_')}.pdf",
                            mime="application/pdf"
                        )
                        
                        # Show summary
                        st.metric("Total Amount Due", f"${total_amount:,.2f}")
    
    with tabs[1]:  # Batch Processing
        st.markdown("### Batch Invoice Generation")
        st.info("Generate invoices for all drivers at once")
        
        batch_dates = st.date_input(
            "Select Period for All Drivers",
            value=(date.today().replace(day=1), date.today()),
            key="batch_dates"
        )
        
        if st.button("📋 Generate All Driver Invoices", type="primary"):
            if len(batch_dates) == 2:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                generated_invoices = []
                
                for i, driver in enumerate(drivers):
                    status_text.text(f"Generating invoice for {driver}...")
                    progress_bar.progress((i + 1) / len(drivers))
                    
                    try:
                        pdf_data, invoice_num, amount = generate_driver_invoice(
                            driver,
                            batch_dates[0],
                            batch_dates[1]
                        )
                        
                        if amount > 0:  # Only save if there are moves
                            # Save to file system
                            invoice_dir = Path("invoices") / batch_dates[1].strftime("%Y-%m")
                            invoice_dir.mkdir(parents=True, exist_ok=True)
                            
                            file_path = invoice_dir / f"{invoice_num}_{driver.replace(' ', '_')}.pdf"
                            with open(file_path, 'wb') as f:
                                f.write(pdf_data)
                            
                            generated_invoices.append({
                                'driver': driver,
                                'invoice': invoice_num,
                                'amount': amount,
                                'path': str(file_path)
                            })
                    except Exception as e:
                        st.error(f"Error generating invoice for {driver}: {e}")
                
                progress_bar.progress(1.0)
                status_text.text("Batch processing complete!")
                
                if generated_invoices:
                    st.success(f"✅ Generated {len(generated_invoices)} invoices")
                    
                    # Show summary table
                    summary_df = pd.DataFrame(generated_invoices)
                    st.dataframe(summary_df[['driver', 'invoice', 'amount']])
                    
                    # Total
                    total = summary_df['amount'].sum()
                    st.metric("Total Payroll", f"${total:,.2f}")
    
    with tabs[2]:  # Invoice History
        st.markdown("### Invoice History")
        
        # Check for saved invoices
        invoice_dir = Path("invoices")
        if invoice_dir.exists():
            all_invoices = list(invoice_dir.rglob("*.pdf"))
            
            if all_invoices:
                st.success(f"📂 {len(all_invoices)} invoices on file")
                
                # Group by month
                invoices_by_month = {}
                for inv_path in all_invoices:
                    month = inv_path.parent.name
                    if month not in invoices_by_month:
                        invoices_by_month[month] = []
                    invoices_by_month[month].append(inv_path)
                
                for month, invoices in sorted(invoices_by_month.items(), reverse=True):
                    with st.expander(f"📅 {month} ({len(invoices)} invoices)"):
                        for inv_path in invoices:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(inv_path.name)
                            with col2:
                                with open(inv_path, 'rb') as f:
                                    st.download_button(
                                        "📥 Download",
                                        f.read(),
                                        inv_path.name,
                                        "application/pdf",
                                        key=str(inv_path)
                                    )
            else:
                st.info("No invoices generated yet")
        else:
            st.info("No invoice history found")
    
    conn.close()

if __name__ == "__main__":
    print("Driver Invoice System Ready")
    print("Features:")
    print("- Professional PDF generation with letterhead")
    print("- Period selection for custom date ranges")
    print("- Detailed move breakdown with fees")
    print("- Net earnings calculation")
    print("- Batch processing for all drivers")
    print("- Invoice history tracking")