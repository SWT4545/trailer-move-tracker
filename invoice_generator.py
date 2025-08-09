import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
import database as db
import utils
import branding

# Try to import reportlab, but continue without it if not available
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

def show_invoice_page():
    """Main invoice and updates page"""
    st.title("💰 Contractor Updates & Driver Invoices")
    
    tabs = st.tabs(["📄 Contractor Update", "📄 Driver Invoice", "📧 Email Updates", "📊 History"])
    
    with tabs[0]:
        generate_contractor_invoice()
    
    with tabs[1]:
        generate_driver_invoice()
    
    with tabs[2]:
        email_invoices()
    
    with tabs[3]:
        show_invoice_history()

def generate_contractor_invoice():
    """Generate update for contractors showing completed moves"""
    st.subheader("📄 Contractor Move Update & Rate Confirmation Request")
    
    # Explanation of rate confirmation
    with st.expander("ℹ️ What is a Rate Confirmation?", expanded=False):
        st.info("""
        **Rate Confirmation** is a document you need from the contractor that:
        - Confirms the agreed rate per mile for completed loads
        - Validates the total amount based on miles driven
        - Must be coupled with BOL/POD documents
        - Is sent to the factoring company for payment processing
        
        **Purpose of these updates:**
        1. Notify contractor of completed moves and miles
        2. Request written rate confirmation for the calculated amount
        3. Provide documentation needed for factoring company submission
        4. Create audit trail for payment processing
        """)
    
    st.info("📌 **Note:** Rate confirmations are submitted with BOL/POD to the factoring company for payment processing")
    
    # Update frequency settings
    with st.expander("📅 Update Frequency Settings", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            update_frequency = st.selectbox(
                "Update Frequency",
                ["Per Load (Individual)", "Daily Batch", "Weekly Summary", "Custom Date Range"],
                help="Choose how often to send updates to contractors"
            )
        
        with col2:
            if update_frequency == "Per Load (Individual)":
                st.info("📌 Each completed load will generate a separate update")
                send_immediately = st.checkbox("Send immediately upon completion", value=False)
            elif update_frequency == "Daily Batch":
                st.info("📌 All loads completed today will be grouped")
            elif update_frequency == "Weekly Summary":
                st.info("📌 All loads from the past week will be grouped")
                week_start = st.selectbox("Week starts on", ["Monday", "Sunday"])
            else:
                st.info("📌 Select custom date range below")
        
        with col3:
            rate_confirmation_deadline = st.selectbox(
                "Rate Confirmation Needed Within",
                ["24 hours", "48 hours", "3 days", "5 days", "7 days"],
                help="How quickly you need rate confirmation"
            )
    
    # Date range selection
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if update_frequency == "Per Load (Individual)":
            start_date = st.date_input("Date", value=datetime.now())
            end_date = start_date
        elif update_frequency == "Daily Batch":
            start_date = st.date_input("Date", value=datetime.now())
            end_date = start_date
        elif update_frequency == "Weekly Summary":
            # Calculate last week's dates
            today = datetime.now().date()
            if week_start == "Monday":
                days_since_monday = today.weekday()
                last_monday = today - timedelta(days=days_since_monday + 7)
                last_sunday = last_monday + timedelta(days=6)
            else:  # Sunday
                days_since_sunday = (today.weekday() + 1) % 7
                last_sunday = today - timedelta(days=days_since_sunday + 7)
                last_monday = last_sunday - timedelta(days=6)
            start_date = st.date_input("Week Start", value=last_monday if week_start == "Monday" else last_sunday)
            end_date = st.date_input("Week End", value=last_sunday if week_start == "Monday" else last_monday + timedelta(days=6))
        else:  # Custom
            start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=7))
            end_date = st.date_input("End Date", value=datetime.now())
    
    with col2:
        contractor_filter = st.selectbox(
            "Select Contractor",
            ["All"] + db.get_all_drivers()['driver_name'].tolist()
        )
        
        # Load saved preferences if a specific contractor is selected
        if contractor_filter != "All":
            prefs = db.get_contractor_update_preference(contractor_filter)
            st.info(f"📌 Saved preference: {prefs['update_frequency']}")
    
    with col3:
        # Save frequency preference
        if st.button("💾 Save Preferences"):
            if contractor_filter != "All":
                db.save_contractor_update_preference(
                    contractor_filter,
                    update_frequency,
                    rate_confirmation_deadline
                )
                st.success(f"Preferences saved for {contractor_filter}")
            else:
                st.warning("Select a specific contractor to save preferences")
    
    # Get unpaid moves
    moves_df = db.get_all_trailer_moves()
    
    # Filter unpaid and completed moves
    unpaid_moves = moves_df[
        (moves_df['paid'] == False) & 
        (moves_df['completion_date'].notna())
    ].copy()
    
    # Apply date filters
    if not unpaid_moves.empty:
        unpaid_moves['completion_date'] = pd.to_datetime(unpaid_moves['completion_date'])
        mask = (unpaid_moves['completion_date'].dt.date >= start_date) & (unpaid_moves['completion_date'].dt.date <= end_date)
        unpaid_moves = unpaid_moves.loc[mask]
        
        # Apply contractor filter
        if contractor_filter != "All":
            unpaid_moves = unpaid_moves[unpaid_moves['assigned_driver'] == contractor_filter]
    
    if not unpaid_moves.empty:
        # Display based on frequency setting
        st.subheader("📋 Rate Confirmation Requests")
        
        if update_frequency == "Per Load (Individual)":
            # Show each load separately
            st.info(f"📌 Showing individual loads for {contractor_filter if contractor_filter != 'All' else 'all contractors'}")
            
            for _, move in unpaid_moves.iterrows():
                with st.expander(f"🚛 Load #{move['id']} - {move['assigned_driver']} - {utils.format_currency(move['load_pay'])}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Date:** {pd.to_datetime(move['completion_date']).strftime('%m/%d/%Y')}")
                        st.write(f"**Trailer:** {move['new_trailer']}")
                        st.write(f"**Route:** {move['pickup_location']} → {move['destination']}")
                    with col2:
                        st.write(f"**Miles:** {move['miles']:.1f}")
                        st.write(f"**Rate:** ${move['rate']:.2f}/mile")
                        st.write(f"**Amount:** {utils.format_currency(move['load_pay'])}")
                    
                    st.info(f"**Rate Confirmation:** ${move['rate']:.2f}/mile × {move['miles']:.1f} miles = {utils.format_currency(move['load_pay'])}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"📄 Generate Update", key=f"gen_{move['id']}"):
                            pdf_moves = pd.DataFrame([move])
                            pdf = generate_contractor_update_pdf(move['assigned_driver'], pdf_moves, update_frequency, rate_confirmation_deadline)
                            st.download_button(
                                label="💾 Download",
                                data=pdf,
                                file_name=f"rate_confirmation_load_{move['id']}_{datetime.now().strftime('%Y%m%d')}.txt",
                                mime="text/plain",
                                key=f"dl_{move['id']}"
                            )
                    with col2:
                        if st.button(f"✉️ Email", key=f"email_{move['id']}"):
                            st.info("Ready to send rate confirmation request")
                    with col3:
                        if st.button(f"✅ Confirmed", key=f"conf_{move['id']}"):
                            st.success("Rate confirmed!")
        else:
            # Group by contractor for batch updates
            contractor_summary = unpaid_moves.groupby('assigned_driver').agg({
                'id': 'count',
                'miles': 'sum',
                'load_pay': 'sum',
                'rate': 'mean'  # Average rate
            }).reset_index()
            contractor_summary.columns = ['Contractor', 'Total Moves', 'Total Miles', 'Total Amount', 'Avg Rate']
            
            # Display summary
            frequency_label = "Daily" if update_frequency == "Daily Batch" else "Weekly" if update_frequency == "Weekly Summary" else "Period"
            st.info(f"📌 Showing {frequency_label} summary for {contractor_filter if contractor_filter != 'All' else 'all contractors'}")
            
            for _, contractor in contractor_summary.iterrows():
                with st.expander(f"🚛 {contractor['Contractor']} - {contractor['Total Moves']} loads - {utils.format_currency(contractor['Total Amount'])}"):
                    # Show moves for this contractor
                    contractor_moves = unpaid_moves[unpaid_moves['assigned_driver'] == contractor['Contractor']]
                
                    display_df = contractor_moves[['new_trailer', 'pickup_location', 'destination', 'completion_date', 'miles', 'rate', 'load_pay']].copy()
                    display_df['completion_date'] = display_df['completion_date'].dt.strftime('%m/%d/%Y')
                    display_df['load_pay'] = display_df['load_pay'].apply(utils.format_currency)
                    display_df.columns = ['Trailer', 'From', 'To', 'Date', 'Miles', 'Rate/Mile', 'Amount']
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
                    # Show summary for rate confirmation
                    st.info(f"""
                    **Summary for Rate Confirmation:**
                    - Total Moves: {contractor['Total Moves']}
                    - Total Miles: {contractor['Total Miles']:.1f}
                    - Rate: ${contractor['Avg Rate']:.2f}/mile
                    - Total Amount: {utils.format_currency(contractor['Total Amount'])}
                    
                    Rate confirmation requested within {rate_confirmation_deadline}
                    """)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        if st.button(f"📄 Generate Update", key=f"pdf_{contractor['Contractor']}"):
                            pdf = generate_contractor_update_pdf(contractor['Contractor'], contractor_moves, update_frequency, rate_confirmation_deadline)
                            st.download_button(
                                label="💾 Download Update",
                                data=pdf,
                                file_name=f"rate_confirmation_{update_frequency.lower().replace(' ', '_')}_{contractor['Contractor'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.txt",
                                mime="text/plain",
                                key=f"download_{contractor['Contractor']}"
                            )
                    
                    with col2:
                        if st.button(f"✉️ Email Update", key=f"email_{contractor['Contractor']}"):
                            st.session_state[f'email_contractor_{contractor["Contractor"]}'] = True
                            st.rerun()
                    
                    with col3:
                        if st.button(f"✅ Rate Confirmed", key=f"confirmed_{contractor['Contractor']}"):
                            st.success(f"Rate confirmation recorded for {contractor['Contractor']}")
                            # In production, save confirmation: db.save_rate_confirmation(contractor['Contractor'], contractor['Total Amount'])
                    
                    with col4:
                        if st.button(f"💰 Mark as Paid", key=f"paid_{contractor['Contractor']}"):
                            # Mark all moves as paid
                            for _, move in contractor_moves.iterrows():
                                db.update_trailer_move(move['id'], {'paid': True})
                            st.success(f"Marked {len(contractor_moves)} moves as paid for {contractor['Contractor']}")
                            st.rerun()
    else:
        st.info("No unpaid completed moves found for the selected period")

def generate_driver_invoice():
    """Generate invoice for drivers showing net pay after factoring"""
    st.subheader("📄 Generate Driver Invoice")
    st.info("Generate invoices TO drivers showing their pay after factoring fees")
    
    # Date range selection
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=7), key="driver_start")
    
    with col2:
        end_date = st.date_input("End Date", value=datetime.now(), key="driver_end")
    
    with col3:
        driver_filter = st.selectbox(
            "Select Driver",
            ["All"] + db.get_all_drivers()['driver_name'].tolist(),
            key="driver_select"
        )
    
    # Get unpaid moves
    moves_df = db.get_all_trailer_moves()
    
    # Filter unpaid and completed moves
    unpaid_moves = moves_df[
        (moves_df['paid'] == False) & 
        (moves_df['completion_date'].notna())
    ].copy()
    
    # Apply filters
    if not unpaid_moves.empty:
        unpaid_moves['completion_date'] = pd.to_datetime(unpaid_moves['completion_date'])
        mask = (unpaid_moves['completion_date'].dt.date >= start_date) & (unpaid_moves['completion_date'].dt.date <= end_date)
        unpaid_moves = unpaid_moves.loc[mask]
        
        if driver_filter != "All":
            unpaid_moves = unpaid_moves[unpaid_moves['assigned_driver'] == driver_filter]
    
    if not unpaid_moves.empty:
        # Calculate net pay for drivers
        unpaid_moves['gross_pay'] = unpaid_moves['miles'] * unpaid_moves['rate']
        unpaid_moves['factor_fee_amount'] = unpaid_moves['gross_pay'] * unpaid_moves['factor_fee']
        unpaid_moves['net_pay'] = unpaid_moves['gross_pay'] - unpaid_moves['factor_fee_amount']
        
        # Group by driver
        driver_summary = unpaid_moves.groupby('assigned_driver').agg({
            'id': 'count',
            'miles': 'sum',
            'gross_pay': 'sum',
            'factor_fee_amount': 'sum',
            'net_pay': 'sum'
        }).reset_index()
        driver_summary.columns = ['Driver', 'Total Moves', 'Total Miles', 'Gross Pay', 'Factor Fees', 'Net Pay']
        
        # Display summary
        st.subheader("Driver Payment Summary")
        for _, driver in driver_summary.iterrows():
            with st.expander(f"👤 {driver['Driver']} - Net Pay: {utils.format_currency(driver['Net Pay'])}"):
                st.write(f"**Gross Pay:** {utils.format_currency(driver['Gross Pay'])}")
                st.write(f"**Factor Fee:** -{utils.format_currency(driver['Factor Fees'])}")
                st.write(f"**Net Pay:** {utils.format_currency(driver['Net Pay'])}")
                
                # Show detailed moves
                driver_moves = unpaid_moves[unpaid_moves['assigned_driver'] == driver['Driver']]
                
                display_df = driver_moves[['new_trailer', 'pickup_location', 'destination', 'miles', 'gross_pay', 'factor_fee_amount', 'net_pay']].copy()
                display_df['gross_pay'] = display_df['gross_pay'].apply(utils.format_currency)
                display_df['factor_fee_amount'] = display_df['factor_fee_amount'].apply(lambda x: f"-{utils.format_currency(x)}")
                display_df['net_pay'] = display_df['net_pay'].apply(utils.format_currency)
                display_df.columns = ['Trailer', 'From', 'To', 'Miles', 'Gross', 'Fee', 'Net']
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                if st.button(f"📄 Generate Driver Invoice PDF", key=f"driver_pdf_{driver['Driver']}"):
                    pdf = generate_driver_invoice_pdf(driver['Driver'], driver_moves, driver)
                    st.download_button(
                        label="💾 Download Driver Invoice",
                        data=pdf,
                        file_name=f"driver_invoice_{driver['Driver'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        key=f"driver_download_{driver['Driver']}"
                    )
    else:
        st.info("No unpaid moves found for drivers in the selected period")

def generate_contractor_update_pdf(contractor_name, moves_df, update_frequency="Weekly Summary", deadline="48 hours"):
    """Generate move update for contractor with rate confirmation request"""
    buffer = BytesIO()
    
    # Determine update type label
    if update_frequency == "Per Load (Individual)":
        update_type = "MOVE COMPLETION UPDATE"
        period_text = f"Date: {pd.to_datetime(moves_df.iloc[0]['completion_date']).strftime('%B %d, %Y')}"
    elif update_frequency == "Daily Batch":
        update_type = "DAILY MOVE UPDATE"
        period_text = f"Date: {pd.to_datetime(moves_df.iloc[0]['completion_date']).strftime('%B %d, %Y')}"
    elif update_frequency == "Weekly Summary":
        update_type = "WEEKLY MOVE SUMMARY"
        start = pd.to_datetime(moves_df['completion_date'].min()).strftime('%m/%d/%Y')
        end = pd.to_datetime(moves_df['completion_date'].max()).strftime('%m/%d/%Y')
        period_text = f"Period: {start} to {end}"
    else:
        update_type = "MOVE UPDATE"
        start = pd.to_datetime(moves_df['completion_date'].min()).strftime('%m/%d/%Y')
        end = pd.to_datetime(moves_df['completion_date'].max()).strftime('%m/%d/%Y')
        period_text = f"Period: {start} to {end}"
    
    text = f"""
{branding.COMPANY_NAME}
{update_type}

{period_text}
Contractor: {contractor_name}
Reference: {datetime.now().strftime('%Y%m%d')}-{contractor_name[:3].upper()}

Dear {contractor_name},

Please find below the completed moves for your review and rate confirmation.

COMPLETED MOVES:
{"="*75}
Date       | Trailer | Route                                    | Miles | Amount
{"="*75}
"""
    total_miles = 0
    total_amount = 0
    move_count = 0
    
    for _, move in moves_df.iterrows():
        date_str = pd.to_datetime(move['completion_date']).strftime('%m/%d/%Y')
        route = f"{move['pickup_location']} → {move['destination']}"
        # Truncate route if too long
        if len(route) > 40:
            route = route[:37] + "..."
        
        text += f"{date_str} | {move['new_trailer']:<7} | {route:<40} | {move['miles']:>5.1f} | {utils.format_currency(move['load_pay']):>10}\n"
        total_miles += move['miles']
        total_amount += move['load_pay']
        move_count += 1
    
    # Calculate average rate
    avg_rate = total_amount / total_miles if total_miles > 0 else 0
    
    text += f"""{"="*75}
TOTAL: {move_count} {'load' if move_count == 1 else 'loads'}                                             {total_miles:>5.1f} | {utils.format_currency(total_amount):>10}

Rate: ${avg_rate:.2f} per mile

Please provide rate confirmation for {utils.format_currency(total_amount)} based on {total_miles:.1f} miles.

If you have any questions, please contact us.

Thank you,
{branding.COMPANY_NAME}

Reference: {datetime.now().strftime('%Y%m%d')}-{contractor_name[:3].upper()}
"""
    buffer.write(text.encode('utf-8'))
    buffer.seek(0)
    return buffer.getvalue()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#DC143C'),
        alignment=TA_CENTER
    )
    
    # Header
    elements.append(Paragraph(branding.COMPANY_NAME, title_style))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("CONTRACTOR INVOICE", styles['Heading2']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Invoice details
    invoice_num = f"INV-{datetime.now().strftime('%Y%m%d')}-{contractor_name[:3].upper()}"
    details = f"""
    <para>
    <b>Invoice Number:</b> {invoice_num}<br/>
    <b>Invoice Date:</b> {datetime.now().strftime('%B %d, %Y')}<br/>
    <b>Contractor:</b> {contractor_name}<br/>
    <b>Payment Terms:</b> Net 30 Days
    </para>
    """
    elements.append(Paragraph(details, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Table data
    data = [['Date', 'Trailer', 'Route', 'Miles', 'Amount']]
    total_amount = 0
    
    for _, move in moves_df.iterrows():
        data.append([
            pd.to_datetime(move['completion_date']).strftime('%m/%d/%Y'),
            move['new_trailer'],
            f"{move['pickup_location']} → {move['destination']}",
            f"{move['miles']:.1f}",
            utils.format_currency(move['load_pay'])
        ])
        total_amount += move['load_pay']
    
    # Add total row
    data.append(['', '', '', 'TOTAL:', utils.format_currency(total_amount)])
    
    # Create table
    table = Table(data, colWidths=[1*inch, 1*inch, 3*inch, 0.8*inch, 1.2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DC143C')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Footer
    footer = f"""
    <para alignment="center">
    Thank you for your business!<br/>
    {branding.COMPANY_NAME}<br/>
    Please remit payment within 30 days
    </para>
    """
    elements.append(Paragraph(footer, styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def generate_driver_invoice_pdf(driver_name, moves_df, summary):
    """Generate PDF invoice for driver showing net pay"""
    if not REPORTLAB_AVAILABLE:
        # Generate a simple text version if reportlab is not available
        buffer = BytesIO()
        text = f"""
{branding.COMPANY_NAME}
DRIVER PAYMENT STATEMENT

Statement Number: DRV-{datetime.now().strftime('%Y%m%d')}-{driver_name[:3].upper()}
Statement Date: {datetime.now().strftime('%B %d, %Y')}
Driver: {driver_name}

PAYMENT SUMMARY:
Gross Pay: {utils.format_currency(summary['Gross Pay'])}
Factoring Fee: -{utils.format_currency(summary['Factor Fees'])}
NET PAY: {utils.format_currency(summary['Net Pay'])}

DETAILED MOVES:
{"="*80}
"""
        for _, move in moves_df.iterrows():
            text += f"{pd.to_datetime(move['completion_date']).strftime('%m/%d/%Y')} | "
            text += f"{move['new_trailer']} | "
            text += f"{move['pickup_location']} → {move['destination']} | "
            text += f"{move['miles']:.1f} mi | "
            text += f"Gross: {utils.format_currency(move['gross_pay'])} | "
            text += f"Fee: -{utils.format_currency(move['factor_fee_amount'])} | "
            text += f"Net: {utils.format_currency(move['net_pay'])}\n"
        
        text += f"""{"="*80}
TOTALS: Gross: {utils.format_currency(summary['Gross Pay'])} | Fee: -{utils.format_currency(summary['Factor Fees'])} | Net: {utils.format_currency(summary['Net Pay'])}

{branding.COMPANY_NAME}
This statement shows your net pay after factoring fees
Payment will be processed according to standard terms
"""
        buffer.write(text.encode('utf-8'))
        buffer.seek(0)
        return buffer.getvalue()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#DC143C'),
        alignment=TA_CENTER
    )
    
    # Header
    elements.append(Paragraph(branding.COMPANY_NAME, title_style))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("DRIVER PAYMENT STATEMENT", styles['Heading2']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Invoice details
    statement_num = f"DRV-{datetime.now().strftime('%Y%m%d')}-{driver_name[:3].upper()}"
    details = f"""
    <para>
    <b>Statement Number:</b> {statement_num}<br/>
    <b>Statement Date:</b> {datetime.now().strftime('%B %d, %Y')}<br/>
    <b>Driver:</b> {driver_name}<br/>
    </para>
    """
    elements.append(Paragraph(details, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Summary section
    summary_text = f"""
    <para>
    <b>Payment Summary:</b><br/>
    Gross Pay: {utils.format_currency(summary['Gross Pay'])}<br/>
    Factoring Fee: -{utils.format_currency(summary['Factor Fees'])}<br/>
    <b>Net Pay: {utils.format_currency(summary['Net Pay'])}</b>
    </para>
    """
    elements.append(Paragraph(summary_text, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Detailed moves table
    data = [['Date', 'Trailer', 'Route', 'Miles', 'Gross', 'Fee', 'Net']]
    
    for _, move in moves_df.iterrows():
        data.append([
            pd.to_datetime(move['completion_date']).strftime('%m/%d/%Y'),
            move['new_trailer'],
            f"{move['pickup_location']} → {move['destination']}",
            f"{move['miles']:.1f}",
            utils.format_currency(move['gross_pay']),
            f"-{utils.format_currency(move['factor_fee_amount'])}",
            utils.format_currency(move['net_pay'])
        ])
    
    # Add total row
    data.append(['', '', '', 'TOTALS:', 
                 utils.format_currency(summary['Gross Pay']),
                 f"-{utils.format_currency(summary['Factor Fees'])}",
                 utils.format_currency(summary['Net Pay'])])
    
    # Create table
    table = Table(data, colWidths=[0.8*inch, 0.8*inch, 2.5*inch, 0.6*inch, 0.9*inch, 0.9*inch, 0.9*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DC143C')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 10),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Footer
    footer = f"""
    <para alignment="center">
    {branding.COMPANY_NAME}<br/>
    This statement shows your net pay after factoring fees<br/>
    Payment will be processed according to standard terms
    </para>
    """
    elements.append(Paragraph(footer, styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def email_invoices():
    """Email updates management"""
    st.subheader("📧 Email Updates")
    
    # Email type selection
    email_type = st.radio("Select Email Type", ["Contractor Move Update", "Driver Payment Statement"])
    
    # Email form
    with st.form("email_update_form"):
        recipient_email = st.text_input("To Email Address", placeholder="contractor@example.com" if email_type == "Contractor Move Update" else "driver@example.com")
        cc_email = st.text_input("CC (Optional)", placeholder="cc@example.com")
        
        if email_type == "Contractor Move Update":
            subject = st.text_input("Subject", value="Move Update - Smith and Williams Trucking")
            body = st.text_area(
                "Email Body",
                value="""Dear Contractor,

Please find attached the move update for your review.

Please provide rate confirmation for the amount shown.

Thank you,
Smith and Williams Trucking""",
                height=200
            )
        else:
            subject = st.text_input("Subject", value="Payment Statement - Smith and Williams Trucking")
            body = st.text_area(
                "Email Body",
                value="""Dear Driver,

Please find attached your payment statement showing completed moves.

This statement shows your gross pay, factoring fees, and net pay amount.
Payment will be processed according to standard terms.

If you have any questions, please contact us.

Best regards,
Smith and Williams Trucking
Driver Relations""",
                height=250
            )
        
        if st.form_submit_button("📤 Send Email"):
            # Add to email history
            db.add_email_history(
                recipients=recipient_email,
                cc=cc_email,
                subject=subject,
                body=body,
                attachments="invoice.pdf"
            )
            st.success("Email sent successfully!")

def show_invoice_history():
    """Show invoice generation history"""
    st.subheader("📊 Invoice History")
    
    # This would typically come from a database
    st.info("Invoice generation history will be displayed here")
    
    # Sample history display
    history_data = {
        'Date': [datetime.now() - timedelta(days=i) for i in range(5)],
        'Type': ['Contractor Invoice', 'Driver Invoice', 'Contractor Invoice', 'Driver Invoice', 'Contractor Invoice'],
        'Recipient': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown', 'Charlie Wilson'],
        'Amount': [2500.00, 1800.00, 3200.00, 2100.00, 2800.00],
        'Status': ['Sent', 'Sent', 'Pending', 'Sent', 'Paid']
    }
    
    history_df = pd.DataFrame(history_data)
    history_df['Date'] = history_df['Date'].dt.strftime('%m/%d/%Y')
    history_df['Amount'] = history_df['Amount'].apply(utils.format_currency)
    
    st.dataframe(history_df, use_container_width=True, hide_index=True)