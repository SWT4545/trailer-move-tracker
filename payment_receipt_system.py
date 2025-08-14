"""
Payment Receipt Generation and 1099 Tracking System
Vernon AI - Professional Driver Payment Management
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import io
import base64

class PaymentReceiptSystem:
    def __init__(self, db_path=None):
        # Auto-detect the correct database
        if db_path:
            self.db_path = db_path
        else:
            # Check which database has the drivers table
            if os.path.exists('trailer_tracker_streamlined.db'):
                self.db_path = 'trailer_tracker_streamlined.db'
            else:
                self.db_path = 'trailer_data.db'
        
        self.ensure_payment_tables()
        
    def ensure_payment_tables(self):
        """Ensure all payment and tax tracking tables exist"""
        # Create tables in both databases to ensure compatibility
        for db_name in ['trailer_data.db', 'trailer_tracker_streamlined.db']:
            if not os.path.exists(db_name):
                # Create the database if it doesn't exist
                open(db_name, 'a').close()
            
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
        
            # Payment receipts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payment_receipts (
                    receipt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    driver_name TEXT NOT NULL,
                    load_number TEXT NOT NULL,
                    payment_date TEXT NOT NULL,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    gross_amount REAL NOT NULL,
                    deductions REAL DEFAULT 0,
                    net_amount REAL NOT NULL,
                    rate_per_mile REAL NOT NULL,
                    total_miles REAL NOT NULL,
                    payment_method TEXT,
                    check_number TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    pdf_path TEXT
                )
            """)
            
            # 1099 tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contractor_1099 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    driver_name TEXT NOT NULL,
                    tax_year INTEGER NOT NULL,
                    ein_ssn TEXT,
                    total_payments REAL NOT NULL,
                    form_1099_sent INTEGER DEFAULT 0,
                    sent_date TEXT,
                    filing_status TEXT,
                    business_name TEXT,
                    business_address TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(driver_name, tax_year)
                )
            """)
            
            # Document storage table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tax_documents (
                    doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    driver_name TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    document_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    tax_year INTEGER,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    uploaded_by TEXT,
                    notes TEXT
                )
            """)
            
            # Payment breakdown details
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payment_details (
                    detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_id INTEGER,
                    description TEXT NOT NULL,
                    amount REAL NOT NULL,
                    type TEXT NOT NULL,
                    FOREIGN KEY (receipt_id) REFERENCES payment_receipts(receipt_id)
                )
            """)
            
            conn.commit()
            conn.close()
    
    def get_completed_loads(self, driver_name=None, start_date=None, end_date=None):
        """Get completed loads for payment processing"""
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT 
                load_number,
                pickup_date,
                delivery_date,
                origin,
                destination,
                total_miles,
                rate_per_mile,
                client_actual_payment,
                payment_received,
                driver_name
            FROM moves
            WHERE status = 'completed'
            AND payment_received > 0
        """
        
        params = []
        if driver_name:
            query += " AND driver_name = ?"
            params.append(driver_name)
        
        if start_date:
            query += " AND delivery_date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND delivery_date <= ?"
            params.append(end_date)
        
        query += " ORDER BY delivery_date DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    
    def calculate_payment_breakdown(self, gross_amount, rate_per_mile, deductions=0):
        """Calculate payment breakdown with mileage from actual payment"""
        # Calculate miles from actual payment amount
        payment_derived_miles = gross_amount / rate_per_mile if rate_per_mile > 0 else 0
        net_amount = gross_amount - deductions
        
        return {
            'gross_amount': gross_amount,
            'total_miles': round(payment_derived_miles, 2),
            'rate_per_mile': rate_per_mile,
            'deductions': deductions,
            'net_amount': net_amount
        }
    
    def generate_receipt_pdf(self, receipt_data):
        """Generate professional PDF receipt with company letterhead"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=12
        )
        
        # Company Header
        elements.append(Paragraph("SMITH & WILLIAMS TRUCKING LLC", title_style))
        elements.append(Paragraph("Professional Transportation Services", styles['Normal']))
        elements.append(Paragraph("123 Main Street, City, State 12345", styles['Normal']))
        elements.append(Paragraph("Phone: (555) 123-4567 | Email: dispatch@swtrucking.com", styles['Normal']))
        elements.append(Spacer(1, 0.5*inch))
        
        # Receipt Title
        elements.append(Paragraph(f"PAYMENT RECEIPT #{receipt_data['receipt_id']}", heading_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # Driver Information
        driver_info = [
            ['Driver:', receipt_data['driver_name']],
            ['Payment Date:', receipt_data['payment_date']],
            ['Period:', f"{receipt_data['period_start']} to {receipt_data['period_end']}"],
            ['Load Number(s):', receipt_data['load_number']]
        ]
        
        driver_table = Table(driver_info, colWidths=[2*inch, 4*inch])
        driver_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(driver_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Payment Breakdown
        elements.append(Paragraph("Payment Breakdown", heading_style))
        
        breakdown_data = [
            ['Description', 'Miles', 'Rate/Mile', 'Amount'],
            ['Base Payment', f"{receipt_data['total_miles']:.2f}", 
             f"${receipt_data['rate_per_mile']:.3f}", f"${receipt_data['gross_amount']:.2f}"],
        ]
        
        # Add deductions if any
        if receipt_data.get('deductions', 0) > 0:
            breakdown_data.append(['Deductions', '', '', f"-${receipt_data['deductions']:.2f}"])
        
        # Add total
        breakdown_data.append(['', '', 'NET TOTAL:', f"${receipt_data['net_amount']:.2f}"])
        
        breakdown_table = Table(breakdown_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        breakdown_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('GRID', (0, 0), (-1, -2), 1, colors.black),
            ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (-2, -1), (-1, -1), 14),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
        ]))
        elements.append(breakdown_table)
        elements.append(Spacer(1, 0.5*inch))
        
        # Payment Method
        if receipt_data.get('payment_method'):
            payment_info = f"Payment Method: {receipt_data['payment_method']}"
            if receipt_data.get('check_number'):
                payment_info += f" (Check #{receipt_data['check_number']})"
            elements.append(Paragraph(payment_info, styles['Normal']))
            elements.append(Spacer(1, 0.25*inch))
        
        # Notes
        if receipt_data.get('notes'):
            elements.append(Paragraph("Notes:", heading_style))
            elements.append(Paragraph(receipt_data['notes'], styles['Normal']))
            elements.append(Spacer(1, 0.25*inch))
        
        # Footer
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph("This receipt is for your records. Please retain for tax purposes.", 
                                 styles['Italic']))
        elements.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                                 styles['Italic']))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    def save_receipt(self, receipt_data):
        """Save payment receipt to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO payment_receipts (
                driver_name, load_number, payment_date, period_start, period_end,
                gross_amount, deductions, net_amount, rate_per_mile, total_miles,
                payment_method, check_number, notes, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            receipt_data['driver_name'], receipt_data['load_number'],
            receipt_data['payment_date'], receipt_data['period_start'],
            receipt_data['period_end'], receipt_data['gross_amount'],
            receipt_data.get('deductions', 0), receipt_data['net_amount'],
            receipt_data['rate_per_mile'], receipt_data['total_miles'],
            receipt_data.get('payment_method'), receipt_data.get('check_number'),
            receipt_data.get('notes'), receipt_data.get('created_by', 'System')
        ))
        
        receipt_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return receipt_id
    
    def update_1099_tracking(self, driver_name, payment_amount, year=None):
        """Update 1099 tracking for contractor"""
        if not year:
            year = datetime.now().year
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if contractor
        cursor.execute("""
            SELECT driver_type FROM drivers_extended 
            WHERE driver_name = ? AND driver_type = 'contractor'
        """, (driver_name,))
        
        if cursor.fetchone():
            # Update or insert 1099 record
            cursor.execute("""
                INSERT OR REPLACE INTO contractor_1099 (
                    driver_name, tax_year, total_payments, updated_at
                ) VALUES (
                    ?, ?, 
                    COALESCE((SELECT total_payments FROM contractor_1099 
                              WHERE driver_name = ? AND tax_year = ?), 0) + ?,
                    CURRENT_TIMESTAMP
                )
            """, (driver_name, year, driver_name, year, payment_amount))
            
            conn.commit()
        
        conn.close()
    
    def get_1099_summary(self, year=None):
        """Get 1099 summary for all contractors"""
        if not year:
            year = datetime.now().year
        
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT 
                c.driver_name,
                c.tax_year,
                c.total_payments,
                c.form_1099_sent,
                c.sent_date,
                d.business_address,
                de.company_name,
                de.mc_number
            FROM contractor_1099 c
            LEFT JOIN drivers d ON c.driver_name = d.driver_name
            LEFT JOIN drivers_extended de ON c.driver_name = de.driver_name
            WHERE c.tax_year = ?
            ORDER BY c.total_payments DESC
        """
        
        df = pd.read_sql_query(query, conn, params=[year])
        conn.close()
        return df
    
    def save_tax_document(self, driver_name, doc_type, file_path, tax_year=None):
        """Save tax document reference"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO tax_documents (
                driver_name, document_type, document_name, file_path, tax_year, uploaded_by
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            driver_name, doc_type, os.path.basename(file_path), 
            file_path, tax_year, st.session_state.get('user', 'System')
        ))
        
        conn.commit()
        conn.close()

def show_payment_receipt_interface():
    """Main interface for payment receipt generation"""
    st.markdown("### 💰 Payment Receipt Generation")
    
    receipt_system = PaymentReceiptSystem()
    
    # Get drivers list - try multiple database locations for compatibility
    drivers = []
    
    # Try main database first
    try:
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        cursor = conn.cursor()
        
        # Check if drivers table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='drivers'")
        if cursor.fetchone():
            cursor.execute("SELECT DISTINCT driver_name FROM drivers WHERE active = 1 ORDER BY driver_name")
            drivers = [row[0] for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        pass
    
    # If no drivers found, try trailer_data.db
    if not drivers:
        try:
            conn = sqlite3.connect('trailer_data.db')
            cursor = conn.cursor()
            
            # Check if drivers table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='drivers'")
            if cursor.fetchone():
                cursor.execute("SELECT DISTINCT driver_name FROM drivers WHERE active = 1 ORDER BY driver_name")
                drivers = [row[0] for row in cursor.fetchall()]
            conn.close()
        except Exception as e:
            pass
    
    # If still no drivers, provide default test drivers
    if not drivers:
        drivers = ['John Smith', 'Mike Johnson', 'Sarah Williams', 'Tom Davis']
    
    if not drivers:
        st.warning("No active drivers found. Please add drivers first.")
        return
    
    tab1, tab2, tab3 = st.tabs(["Generate Receipt", "1099 Tracking", "Document Storage"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            selected_driver = st.selectbox("Select Driver", drivers)
            
            # Date range selection
            date_option = st.radio("Select Period", ["Specific Load", "Date Range", "Current Month"])
            
            if date_option == "Date Range":
                start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
                end_date = st.date_input("End Date", datetime.now())
            elif date_option == "Current Month":
                start_date = datetime.now().replace(day=1)
                end_date = datetime.now()
            else:
                start_date = None
                end_date = None
        
        with col2:
            payment_date = st.date_input("Payment Date", datetime.now())
            payment_method = st.selectbox("Payment Method", ["Check", "Direct Deposit", "Cash", "Other"])
            
            if payment_method == "Check":
                check_number = st.text_input("Check Number")
            else:
                check_number = None
        
        # Get completed loads
        loads_df = receipt_system.get_completed_loads(
            selected_driver, 
            start_date.strftime('%Y-%m-%d') if start_date else None,
            end_date.strftime('%Y-%m-%d') if end_date else None
        )
        
        if not loads_df.empty:
            st.markdown("#### Available Loads for Payment")
            
            # Show loads with selection
            selected_loads = st.multiselect(
                "Select Load(s) for Receipt",
                loads_df['load_number'].tolist(),
                help="Select one or more loads to include in this receipt"
            )
            
            if selected_loads:
                # Filter selected loads
                selected_df = loads_df[loads_df['load_number'].isin(selected_loads)]
                
                # Calculate totals
                total_payment = selected_df['payment_received'].sum()
                avg_rate = selected_df['rate_per_mile'].mean()
                
                st.markdown("#### Payment Details")
                col3, col4 = st.columns(2)
                
                with col3:
                    gross_amount = st.number_input("Gross Amount", 
                                                  value=float(total_payment), 
                                                  format="%.2f")
                    rate_per_mile = st.number_input("Rate per Mile", 
                                                   value=float(avg_rate), 
                                                   format="%.3f")
                
                with col4:
                    deductions = st.number_input("Deductions", value=0.0, format="%.2f")
                    
                    # Calculate mileage from actual payment
                    if rate_per_mile > 0:
                        calculated_miles = gross_amount / rate_per_mile
                        st.info(f"Payment-Derived Miles: {calculated_miles:.2f}")
                        
                        # Show mileage comparison if Google Maps data available
                        google_miles = selected_df['total_miles'].sum() if 'total_miles' in selected_df.columns else None
                        if google_miles and google_miles > 0:
                            delta = calculated_miles - google_miles
                            if abs(delta) > 5:
                                st.warning(f"⚠️ Mileage Delta: {abs(delta):.2f} miles")
                                st.caption(f"Google Maps: {google_miles:.2f} | Payment: {calculated_miles:.2f}")
                            else:
                                st.success(f"✅ Mileage Verified (Delta: {abs(delta):.2f})")
                    else:
                        calculated_miles = 0
                
                # Notes
                notes = st.text_area("Notes (Optional)", 
                                   placeholder="Any additional notes for this payment")
                
                # Generate Receipt button
                if st.button("🧾 Generate Receipt", type="primary"):
                    # Calculate payment breakdown (only using payment-derived miles for receipt)
                    breakdown = receipt_system.calculate_payment_breakdown(
                        gross_amount, rate_per_mile, deductions
                    )
                    
                    # Prepare receipt data
                    receipt_data = {
                        'driver_name': selected_driver,
                        'load_number': ', '.join(selected_loads),
                        'payment_date': payment_date.strftime('%Y-%m-%d'),
                        'period_start': selected_df['pickup_date'].min(),
                        'period_end': selected_df['delivery_date'].max(),
                        'gross_amount': breakdown['gross_amount'],
                        'deductions': breakdown['deductions'],
                        'net_amount': breakdown['net_amount'],
                        'rate_per_mile': rate_per_mile,
                        'total_miles': breakdown['total_miles'],
                        'payment_method': payment_method,
                        'check_number': check_number,
                        'notes': notes,
                        'created_by': st.session_state.get('user', 'System')
                    }
                    
                    # Save receipt
                    receipt_id = receipt_system.save_receipt(receipt_data)
                    receipt_data['receipt_id'] = receipt_id
                    
                    # Update 1099 tracking for contractors
                    receipt_system.update_1099_tracking(selected_driver, breakdown['net_amount'])
                    
                    # Generate PDF
                    pdf_buffer = receipt_system.generate_receipt_pdf(receipt_data)
                    
                    # Display success and download button
                    st.success(f"✅ Receipt #{receipt_id} generated successfully!")
                    
                    # Provide download button
                    st.download_button(
                        label="📥 Download Receipt PDF",
                        data=pdf_buffer,
                        file_name=f"receipt_{receipt_id}_{selected_driver}_{payment_date}.pdf",
                        mime="application/pdf"
                    )
        else:
            st.info("No completed loads with payments found for the selected criteria.")
    
    with tab2:
        st.markdown("#### 📋 1099 Contractor Tracking")
        
        # Year selection
        current_year = datetime.now().year
        selected_year = st.selectbox("Tax Year", 
                                    list(range(current_year, current_year - 5, -1)),
                                    index=0)
        
        # Get 1099 summary
        summary_df = receipt_system.get_1099_summary(selected_year)
        
        if not summary_df.empty:
            st.markdown(f"##### {selected_year} Contractor Payments")
            
            # Format display
            summary_df['total_payments'] = summary_df['total_payments'].apply(lambda x: f"${x:,.2f}")
            summary_df['1099_sent'] = summary_df['form_1099_sent'].apply(lambda x: "✅ Sent" if x else "⏳ Pending")
            
            # Display summary
            st.dataframe(
                summary_df[['driver_name', 'company_name', 'total_payments', '1099_sent', 'sent_date']],
                hide_index=True
            )
            
            # Export option
            if st.button("📊 Export 1099 Summary"):
                csv = summary_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"1099_summary_{selected_year}.csv",
                    mime="text/csv"
                )
            
            # Mark 1099 as sent
            st.markdown("##### Update 1099 Status")
            driver_to_update = st.selectbox("Select Contractor", 
                                           summary_df['driver_name'].tolist())
            
            if st.button("Mark 1099 as Sent"):
                conn = sqlite3.connect('trailer_data.db')
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE contractor_1099 
                    SET form_1099_sent = 1, sent_date = ?
                    WHERE driver_name = ? AND tax_year = ?
                """, (datetime.now().strftime('%Y-%m-%d'), driver_to_update, selected_year))
                conn.commit()
                conn.close()
                st.success(f"1099 marked as sent for {driver_to_update}")
                st.rerun()
        else:
            st.info(f"No contractor payments recorded for {selected_year}")
    
    with tab3:
        st.markdown("#### 📁 Tax Document Storage")
        
        col1, col2 = st.columns(2)
        
        with col1:
            doc_driver = st.selectbox("Select Driver", drivers, key="doc_driver")
            doc_type = st.selectbox("Document Type", 
                                  ["W-9", "1099-MISC", "1099-NEC", "Insurance Certificate", 
                                   "CDL Copy", "Medical Certificate", "Other"])
        
        with col2:
            doc_year = st.number_input("Tax Year", 
                                      min_value=2020, 
                                      max_value=datetime.now().year + 1,
                                      value=datetime.now().year)
            
            uploaded_file = st.file_uploader("Upload Document", 
                                            type=['pdf', 'jpg', 'png', 'docx'])
        
        if uploaded_file and st.button("📤 Save Document"):
            # Create documents directory if not exists
            os.makedirs("tax_documents", exist_ok=True)
            
            # Save file
            file_path = f"tax_documents/{doc_driver}_{doc_type}_{doc_year}_{uploaded_file.name}"
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Save to database
            receipt_system.save_tax_document(doc_driver, doc_type, file_path, doc_year)
            st.success(f"Document saved successfully: {uploaded_file.name}")
        
        # Show existing documents
        st.markdown("##### Stored Documents")
        conn = sqlite3.connect('trailer_data.db')
        docs_df = pd.read_sql_query("""
            SELECT driver_name, document_type, document_name, tax_year, upload_date
            FROM tax_documents
            ORDER BY upload_date DESC
            LIMIT 20
        """, conn)
        conn.close()
        
        if not docs_df.empty:
            st.dataframe(docs_df, hide_index=True)
        else:
            st.info("No documents stored yet")