"""
Enhanced Payment Processing System
Allows management to manually enter service fees based on factoring amounts
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import io

def get_connection():
    return sqlite3.connect('trailer_tracker_streamlined.db')

def show_payment_processing():
    """Payment processing interface for management"""
    st.markdown("## 💰 Payment Processing & Factoring")
    
    tabs = st.tabs([
        "📝 Process Payments",
        "📄 Documents",
        "💳 Factoring Submission", 
        "📄 Generate Receipts",
        "📊 Payment History",
        "⚙️ Fee Configuration"
    ])
    
    with tabs[0]:  # Process Payments
        st.markdown("### Process Driver Payments")
        st.info("Enter actual service fees after factoring submission")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get completed moves with documents that haven't been paid
        cursor.execute('''SELECT m.id, m.move_id, m.driver_name, m.total_miles, 
                                m.driver_pay, m.payment_status, m.completed_date,
                                m.new_trailer, m.old_trailer, m.delivery_location,
                                dr.rate_confirmation, dr.bol, dr.pod, dr.all_docs_complete
                         FROM moves m
                         LEFT JOIN document_requirements dr ON m.move_id = dr.move_id
                         WHERE m.status = 'completed' 
                         AND (m.payment_status != 'paid' OR m.payment_status IS NULL)
                         ORDER BY m.completed_date''')
        unpaid_moves = cursor.fetchall()
        
        if unpaid_moves:
            st.markdown("#### Pending Payments")
            
            for move in unpaid_moves:
                move_id_db, move_id, driver, miles, gross_pay, pay_status, comp_date, new_t, old_t, location, has_rc, has_bol, has_pod, docs_complete = move
                
                # Check if ready for payment
                if not docs_complete:
                    docs_status = []
                    if not has_rc: docs_status.append("Rate Conf")
                    if not has_bol: docs_status.append("BOL")
                    if not has_pod: docs_status.append("POD")
                    
                    st.warning(f"⚠️ {move_id} - Missing documents: {', '.join(docs_status)}")
                    continue
                
                with st.expander(f"💵 {move_id} - {driver} - ${gross_pay:.2f}", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown(f"""
                        **Move Details:**
                        - Route: Fleet Memphis → {location}
                        - Trailers: {new_t} ↔ {old_t}
                        - Miles: {miles}
                        - Completed: {comp_date}
                        """)
                    
                    with col2:
                        st.markdown(f"""
                        **Payment Calculation:**
                        - Gross Pay: ${gross_pay:.2f}
                        - Rate: ${gross_pay/miles:.2f}/mile
                        """)
                        
                        # Manual service fee entry - default to 3% of gross
                        default_fee = gross_pay * 0.03  # 3% factoring fee
                        service_fee = st.number_input(
                            "Service Fee ($)",
                            min_value=0.00,
                            max_value=500.00,
                            value=round(default_fee, 2),
                            step=0.01,
                            key=f"fee_{move_id_db}",
                            help=f"Default: 3% of ${gross_pay:.2f} = ${default_fee:.2f}"
                        )
                        
                        net_pay = gross_pay - service_fee
                        st.metric("Net Pay", f"${net_pay:.2f}")
                    
                    with col3:
                        st.markdown("**Factoring Info:**")
                        
                        factoring_amount = st.number_input(
                            "Amount Submitted",
                            value=gross_pay,
                            key=f"fact_amt_{move_id_db}"
                        )
                        
                        factoring_ref = st.text_input(
                            "Factoring Reference",
                            placeholder="Invoice/Ref #",
                            key=f"fact_ref_{move_id_db}"
                        )
                        
                        st.markdown("**Payment Method:**")
                        payment_method = st.selectbox(
                            "Transfer via",
                            ["Navy Federal Transfer", "Check", "Other"],
                            key=f"method_{move_id_db}"
                        )
                        
                        transfer_ref = st.text_input(
                            "Transfer Reference",
                            placeholder="Navy Federal confirmation #",
                            key=f"transfer_{move_id_db}"
                        )
                        
                        if st.button("Process Payment", key=f"process_{move_id_db}", type="primary"):
                            # Update move with payment info
                            cursor.execute('''UPDATE moves 
                                           SET payment_status = 'paid',
                                               payment_date = ?,
                                               payment_method = ?,
                                               service_fee = ?,
                                               net_pay = ?,
                                               factoring_amount = ?,
                                               factoring_reference = ?
                                           WHERE id = ?''',
                                         (datetime.now(), payment_method, service_fee, net_pay,
                                          factoring_amount, factoring_ref, move_id_db))
                            
                            # Create payment record with transfer info
                            cursor.execute('''INSERT INTO payments 
                                           (driver_name, amount, service_fee, miles, 
                                            status, notes, payment_date, move_id)
                                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                                         (driver, net_pay, service_fee, miles,
                                          'paid', f'Move {move_id} - {payment_method} - Ref: {transfer_ref}',
                                          datetime.now(), move_id))
                            
                            # Generate and store invoice receipt
                            receipt = generate_payment_receipt(driver, 
                                (0, datetime.now().strftime('%Y-%m-%d'), net_pay, service_fee, miles, move_id, 
                                 f'{payment_method} - {transfer_ref}'), gross_pay)
                            
                            # Store receipt in documents
                            cursor.execute('''INSERT INTO factoring_documents 
                                           (move_id, document_type, file_name, file_data, 
                                            uploaded_by, verified)
                                           VALUES (?, ?, ?, ?, ?, ?)''',
                                         (move_id, 'Payment Receipt', 
                                          f'receipt_{move_id}_{datetime.now().strftime("%Y%m%d")}.pdf',
                                          receipt, st.session_state.get('user', 'System'), 1))
                            
                            conn.commit()
                            st.success(f"✅ Payment processed: ${net_pay:.2f} to {driver}")
                            st.rerun()
        else:
            st.info("No pending payments to process")
        
        conn.close()
    
    with tabs[1]:  # Documents Tab
        try:
            from factoring_document_manager import show_document_management
            show_document_management()
        except Exception as e:
            st.error(f"Document manager loading error: {e}")
    
    with tabs[2]:  # Factoring Submission
        st.markdown("### Factoring Submission Tracking")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get moves ready for factoring
        cursor.execute('''SELECT move_id, driver_name, total_miles, driver_pay, 
                                completed_date, pod_uploaded
                         FROM moves 
                         WHERE status = 'completed' 
                         AND (submitted_to_factoring IS NULL OR submitted_to_factoring = '')
                         ORDER BY completed_date''')
        ready_for_factoring = cursor.fetchall()
        
        if ready_for_factoring:
            st.markdown("#### Ready for Factoring Submission")
            
            # Batch selection
            selected_moves = []
            for move in ready_for_factoring:
                move_id, driver, miles, pay, comp_date, pod = move
                
                col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
                with col1:
                    if st.checkbox("", key=f"select_{move_id}"):
                        selected_moves.append(move_id)
                with col2:
                    st.write(f"{move_id} - {driver}")
                with col3:
                    st.write(f"${pay:.2f}")
                with col4:
                    if pod:
                        st.success("POD ✓")
                    else:
                        st.warning("No POD")
            
            if selected_moves:
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                with col1:
                    batch_ref = st.text_input(
                        "Batch Reference",
                        value=f"BATCH-{datetime.now().strftime('%Y%m%d')}",
                        help="Reference number for this factoring submission"
                    )
                
                with col2:
                    factoring_company = st.selectbox(
                        "Factoring Company",
                        ["Primary Factoring Co.", "Secondary Factoring Co.", "Other"]
                    )
                
                if st.button("Submit to Factoring", type="primary"):
                    for move_id in selected_moves:
                        cursor.execute('''UPDATE moves 
                                       SET submitted_to_factoring = ?,
                                           factoring_batch = ?,
                                           factoring_company = ?
                                       WHERE move_id = ?''',
                                     (datetime.now(), batch_ref, factoring_company, move_id))
                    
                    conn.commit()
                    st.success(f"✅ {len(selected_moves)} moves submitted to factoring")
                    st.info(f"Batch Reference: {batch_ref}")
                    st.rerun()
        else:
            st.info("No moves ready for factoring submission")
        
        # Show factoring history
        st.markdown("#### Recent Factoring Submissions")
        
        df = pd.read_sql_query('''SELECT move_id, driver_name, driver_pay,
                                         submitted_to_factoring, factoring_batch
                                  FROM moves 
                                  WHERE submitted_to_factoring IS NOT NULL
                                  ORDER BY submitted_to_factoring DESC
                                  LIMIT 20''', conn)
        
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        conn.close()
    
    with tabs[2]:  # Generate Receipts
        st.markdown("### Generate Payment Receipts")
        st.info("Receipts will show actual net pay after service fees")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get paid moves
        cursor.execute('''SELECT DISTINCT driver_name 
                         FROM payments 
                         ORDER BY driver_name''')
        drivers = [d[0] for d in cursor.fetchall()]
        
        selected_driver = st.selectbox("Select Driver", [""] + drivers)
        
        if selected_driver:
            # Get driver's payments
            cursor.execute('''SELECT p.id, p.payment_date, p.amount, p.service_fee, 
                                   p.miles, p.move_id, p.notes
                            FROM payments p
                            WHERE p.driver_name = ?
                            ORDER BY p.payment_date DESC''',
                          (selected_driver,))
            payments = cursor.fetchall()
            
            if payments:
                st.markdown(f"#### Payments for {selected_driver}")
                
                for payment in payments:
                    pay_id, pay_date, net_amount, fee, miles, move_id, notes = payment
                    gross_amount = net_amount + fee
                    
                    with st.expander(f"Payment {pay_date} - ${net_amount:.2f}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"""
                            **Payment Details:**
                            - Date: {pay_date}
                            - Move: {move_id}
                            - Miles: {miles}
                            - Gross Pay: ${gross_amount:.2f}
                            - Service Fee: ${fee:.2f}
                            - **Net Pay: ${net_amount:.2f}**
                            """)
                        
                        with col2:
                            if st.button(f"Generate Receipt", key=f"receipt_{pay_id}"):
                                receipt = generate_payment_receipt(
                                    selected_driver, payment, gross_amount
                                )
                                st.download_button(
                                    "📥 Download Receipt",
                                    receipt,
                                    f"receipt_{selected_driver}_{pay_date}.pdf",
                                    "application/pdf"
                                )
        
        conn.close()
    
    with tabs[3]:  # Payment History
        st.markdown("### Payment History")
        
        conn = get_connection()
        
        # Summary metrics
        cursor = conn.cursor()
        cursor.execute('''SELECT COUNT(*), SUM(amount), SUM(service_fee), SUM(miles)
                         FROM payments WHERE status = 'paid' ''')
        total_count, total_paid, total_fees, total_miles = cursor.fetchone()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Payments", total_count or 0)
        with col2:
            st.metric("Total Paid Out", f"${total_paid or 0:,.2f}")
        with col3:
            st.metric("Total Fees", f"${total_fees or 0:,.2f}")
        with col4:
            st.metric("Total Miles", f"{int(total_miles or 0):,}")
        
        # Detailed history
        df = pd.read_sql_query('''SELECT payment_date as Date, 
                                         driver_name as Driver,
                                         amount as 'Net Pay',
                                         service_fee as 'Service Fee',
                                         miles as Miles,
                                         move_id as 'Move ID',
                                         notes as Notes
                                  FROM payments 
                                  ORDER BY payment_date DESC''', conn)
        
        if not df.empty:
            # Format currency columns
            df['Net Pay'] = df['Net Pay'].apply(lambda x: f"${x:.2f}")
            df['Service Fee'] = df['Service Fee'].apply(lambda x: f"${x:.2f}")
            
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Export option
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Export Payment History",
                csv,
                "payment_history.csv",
                "text/csv"
            )
        
        conn.close()
    
    with tabs[4]:  # Fee Configuration
        st.markdown("### Service Fee Configuration")
        st.warning("⚠️ Service fees should match factoring company charges")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get recent fee patterns
        cursor.execute('''SELECT AVG(service_fee), MIN(service_fee), MAX(service_fee)
                         FROM payments WHERE payment_date > date('now', '-30 days')''')
        avg_fee, min_fee, max_fee = cursor.fetchone()
        
        if avg_fee:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average Fee (30 days)", f"${avg_fee:.2f}")
            with col2:
                st.metric("Minimum Fee", f"${min_fee:.2f}")
            with col3:
                st.metric("Maximum Fee", f"${max_fee:.2f}")
        
        st.markdown("### Fee Guidelines")
        st.info("""
        **Service Fee Calculation:**
        - Standard moves: $6.00
        - High-value loads: May vary based on factoring percentage
        - Rush deliveries: Additional fees may apply
        - Always confirm with factoring company before processing payment
        
        **Important:** The service fee is deducted from the gross driver pay to calculate net pay.
        This fee covers factoring costs and administrative expenses.
        """)
        
        conn.close()

def generate_payment_receipt(driver_name, payment_data, gross_amount):
    """Generate professional payment receipt with actual fees"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from company_config import get_company_info
        
        buffer = io.BytesIO()
        company_info = get_company_info()
        
        # Unpack payment data
        pay_id, pay_date, net_amount, fee, miles, move_id, notes = payment_data
        
        # Create PDF
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Header
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#DC143C'),
            alignment=1  # Center
        )
        
        story.append(Paragraph(company_info['company_name'], header_style))
        story.append(Paragraph("PAYMENT RECEIPT", styles['Heading2']))
        story.append(Spacer(1, 0.3*inch))
        
        # Receipt details
        receipt_data = [
            ['Receipt Information', ''],
            ['Receipt Date:', datetime.now().strftime('%B %d, %Y')],
            ['Payment Date:', pay_date],
            ['Driver:', driver_name],
            ['Move ID:', move_id or 'N/A'],
            ['', ''],
            ['Payment Breakdown', ''],
            ['Miles Driven:', f'{miles}'],
            ['Rate per Mile:', f'${gross_amount/miles:.2f}' if miles else 'N/A'],
            ['Gross Amount:', f'${gross_amount:.2f}'],
            ['Service Fee:', f'-${fee:.2f}'],
            ['', ''],
            ['NET PAY:', f'${net_amount:.2f}']
        ]
        
        table = Table(receipt_data, colWidths=[2.5*inch, 2.5*inch])
        table.setStyle(TableStyle([
            # Headers
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('BACKGROUND', (0, 6), (-1, 6), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('TEXTCOLOR', (0, 6), (-1, 6), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 6), (-1, 6), 'Helvetica-Bold'),
            # Net pay row
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#DC143C')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            # General
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.5*inch))
        
        # Notes
        if notes:
            story.append(Paragraph("Notes:", styles['Heading3']))
            story.append(Paragraph(notes, styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # Footer
        footer_text = f"""
        {company_info['company_address']}<br/>
        Phone: {company_info['company_phone']} | Email: {company_info['company_email']}<br/>
        {company_info['dot_number']} | {company_info['mc_number']}
        """
        story.append(Paragraph(footer_text, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        return buffer.getvalue()
        
    except ImportError:
        # Fallback text receipt
        return f"""
PAYMENT RECEIPT

Driver: {driver_name}
Date: {payment_data[1]}
Move: {payment_data[5]}

Gross Pay: ${gross_amount:.2f}
Service Fee: -${payment_data[3]:.2f}
NET PAY: ${payment_data[2]:.2f}

{company_info['company_name']}
        """.encode()

# Function to check if payment can be processed
def can_process_payment(move_id):
    """Check if a move is ready for payment processing"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''SELECT status, pod_uploaded, submitted_to_factoring
                     FROM moves WHERE move_id = ?''', (move_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        status, pod, factoring = result
        return status == 'completed' and pod == 1
    return False