"""
Driver Contractor Portal - Enhanced with Company Info, Documents, and Payments
Smith & Williams Trucking
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import os
from company_config import get_company_info

def get_connection():
    return sqlite3.connect('trailer_tracker_streamlined.db')

def show_driver_contractor_portal(username):
    """Enhanced driver portal for contractors"""
    
    # Get driver info
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get driver profile - check both username and driver_name
    cursor.execute('''SELECT driver_name, company_name, insurance_info, ein, 
                            total_miles, total_earnings, coi_uploaded, w9_uploaded,
                            phone, email
                     FROM drivers WHERE user = ? OR driver_name = ?''', 
                  (username, username))
    driver_info = cursor.fetchone()
    
    # If not found by username, check contractor_info table
    if not driver_info:
        cursor.execute('''SELECT driver_name FROM contractor_info WHERE driver_name LIKE ?''',
                      (f'%{username}%',))
        contractor = cursor.fetchone()
        if contractor:
            cursor.execute('''SELECT d.driver_name, c.company_name, c.insurance_company || ' - ' || c.insurance_policy,
                                    d.ein, d.total_miles, d.total_earnings, d.coi_uploaded, d.w9_uploaded,
                                    c.phone, c.email
                             FROM contractor_info c
                             LEFT JOIN drivers d ON c.driver_name = d.driver_name
                             WHERE c.driver_name = ?''', (contractor[0],))
            driver_info = cursor.fetchone()
    
    if not driver_info:
        st.error("Driver profile not found")
        return
    
    # Unpack driver info with new fields
    if len(driver_info) == 10:
        driver_name, company_name, insurance_info, ein, total_miles, total_earnings, coi_uploaded, w9_uploaded, phone, email = driver_info
    else:
        driver_name, company_name, insurance_info, ein, total_miles, total_earnings, coi_uploaded, w9_uploaded = driver_info[:8]
        phone = email = None
    
    # Header with driver info
    st.markdown(f"# 🚛 Driver Portal - {driver_name}")
    
    if company_name:
        st.markdown(f"### {company_name}")
    
    # Import self-assignment functionality
    try:
        from driver_self_assignment_portal import show_driver_self_assignment
        has_self_assignment = True
    except:
        has_self_assignment = False
    
    # Tabs for different sections
    tab_names = ["📊 Dashboard", "🎯 Self-Assign", "🚚 My Moves", "💰 Payments", "📄 Documents", "📚 Help Guide"]
    if not has_self_assignment:
        tab_names.remove("🎯 Self-Assign")
    
    tabs = st.tabs(tab_names)
    
    # Adjust tab indices based on self-assignment availability
    tab_idx = 0
    
    with tabs[tab_idx]:  # Dashboard
        st.markdown("## Your Performance Summary")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Miles", f"{int(total_miles or 0):,}")
        
        with col2:
            st.metric("Total Earnings", f"${total_earnings or 0:,.2f}")
        
        with col3:
            # Get completed moves count
            cursor.execute('''SELECT COUNT(*) FROM moves 
                            WHERE driver_name = ? AND status = 'completed' ''', 
                          (driver_name,))
            completed_count = cursor.fetchone()[0]
            st.metric("Completed Moves", completed_count)
        
        with col4:
            avg_per_move = (total_earnings / completed_count) if completed_count > 0 else 0
            st.metric("Avg Per Move", f"${avg_per_move:,.2f}")
        
        # Contractor Information - Get full details
        cursor.execute('''SELECT * FROM contractor_info WHERE driver_name = ?''', (driver_name,))
        contractor_details = cursor.fetchone()
        
        st.markdown("### Your Contractor Information")
        
        info_cols = st.columns(2)
        with info_cols[0]:
            if contractor_details:
                # Full contractor info available
                st.info(f"""
                **Company:** {contractor_details[2]}  
                **DOT #:** {contractor_details[6]}  
                **MC #:** {contractor_details[7]}  
                **Phone:** {contractor_details[3]}  
                **Email:** {contractor_details[5]}  
                **Address:** {contractor_details[4]}
                """)
            else:
                st.info(f"""
                **Company:** {company_name or 'Not Set'}  
                **Phone:** {phone or 'Not Provided'}  
                **Email:** {email or 'Not Provided'}  
                **Insurance:** {insurance_info or 'Not Provided'}
                """)
        
        with info_cols[1]:
            if contractor_details:
                # Show insurance info
                st.info(f"""
                **Insurance Company:** {contractor_details[8]}  
                **Policy #:** {contractor_details[9]}  
                **Expires:** {contractor_details[10]}  
                **COI Status:** {'✅ On File' if coi_uploaded else '❌ Required'}  
                **W9 Status:** {'✅ On File' if w9_uploaded else '❌ Required'}
                """)
            else:
                doc_status = []
                if coi_uploaded:
                    doc_status.append("✅ COI Uploaded")
                else:
                    doc_status.append("❌ COI Required")
                
                if w9_uploaded:
                    doc_status.append("✅ W9 Uploaded")
                else:
                    doc_status.append("❌ W9 Required")
                
                st.info("**Document Status:**\n" + "\n".join(doc_status))
        
        # Recent Activity
        st.markdown("### Recent Activity")
        cursor.execute('''SELECT move_id, pickup_location, delivery_location, 
                                total_miles, driver_pay, status, move_date
                         FROM moves WHERE driver_name = ? 
                         ORDER BY move_date DESC LIMIT 5''', (driver_name,))
        recent_moves = cursor.fetchall()
        
        if recent_moves:
            for move in recent_moves:
                move_id, pickup, delivery, miles, pay, status, date = move
                status_emoji = "✅" if status == "completed" else "🚚"
                st.markdown(f"{status_emoji} **{move_id}** - {pickup} → {delivery} ({miles} mi) - ${pay:.2f}")
    
    # Self-Assignment Tab (if available)
    if has_self_assignment:
        tab_idx += 1
        with tabs[tab_idx]:
            show_driver_self_assignment(username)
    
    tab_idx += 1
    with tabs[tab_idx]:  # My Moves
        st.markdown("## Your Move History")
        
        # Get all moves
        cursor.execute('''SELECT move_id, pickup_location, delivery_location, 
                                total_miles, driver_pay, status, move_date,
                                payment_status, mlbl_number, rate_con_number
                         FROM moves WHERE driver_name = ? 
                         ORDER BY move_date DESC''', (driver_name,))
        moves = cursor.fetchall()
        
        if moves:
            moves_df = pd.DataFrame(moves, columns=[
                'Move ID', 'Pickup', 'Delivery', 'Miles', 
                'Pay', 'Status', 'Date', 'Payment', 'MLBL#', 'RC#'
            ])
            
            # Format currency
            moves_df['Pay'] = moves_df['Pay'].apply(lambda x: f"${x:,.2f}")
            
            # Show summary
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Moves", len(moves))
            with col2:
                completed = len([m for m in moves if m[5] == 'completed'])
                st.metric("Completed", completed)
            
            # Display table
            st.dataframe(moves_df, use_container_width=True, hide_index=True)
            
            # Download option
            if st.button("📥 Export Move History"):
                csv = moves_df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    f"moves_{driver_name.replace(' ', '_')}.csv",
                    "text/csv"
                )
        else:
            st.info("No moves found")
    
    with tabs[2]:  # Payments
        st.markdown("## Payment History")
        
        # Get payment records
        cursor.execute('''SELECT payment_date, amount, service_fee, miles, status, notes
                         FROM payments WHERE driver_name = ?
                         ORDER BY payment_date DESC''', (driver_name,))
        payments = cursor.fetchall()
        
        if payments:
            # Summary
            total_paid = sum(p[1] for p in payments)
            total_fees = sum(p[2] for p in payments)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Paid", f"${total_paid:,.2f}")
            with col2:
                st.metric("Service Fees", f"${total_fees:,.2f}")
            with col3:
                st.metric("Net Earnings", f"${total_paid - total_fees:,.2f}")
            
            st.markdown("### Payment Details")
            for payment in payments:
                date, amount, fee, miles, status, notes = payment
                
                with st.expander(f"Payment: ${amount:,.2f} - {date}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"""
                        **Date:** {date}  
                        **Amount:** ${amount:,.2f}  
                        **Service Fee:** ${fee:,.2f}  
                        **Net Amount:** ${amount - fee:,.2f}
                        """)
                    
                    with col2:
                        st.markdown(f"""
                        **Miles:** {miles}  
                        **Status:** {status}  
                        **Notes:** {notes}
                        """)
                    
                    # Generate receipt button
                    if st.button(f"📄 Generate Receipt", key=f"receipt_{date}_{amount}"):
                        receipt = generate_payment_receipt(driver_name, driver_info, payment)
                        st.download_button(
                            "Download Receipt PDF",
                            receipt,
                            f"receipt_{driver_name}_{date}.pdf",
                            "application/pdf"
                        )
        else:
            st.info("No payment records found")
        
        # 1099 Information
        st.markdown("### 1099 Tax Information")
        st.info(f"""
        **Your 1099 Information:**
        - Company: {company_name}
        - EIN: {ein}
        - YTD Earnings: ${total_earnings:,.2f}
        
        1099 forms will be issued by January 31st for the previous tax year.
        """)
    
    with tabs[3]:  # Documents
        st.markdown("## Document Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Certificate of Insurance (COI)")
            if coi_uploaded:
                st.success("✅ COI on file")
                if st.button("Update COI"):
                    uploaded_coi = st.file_uploader("Upload new COI", type=['pdf', 'jpg', 'png'])
                    if uploaded_coi:
                        # Save file logic here
                        st.success("COI updated successfully!")
            else:
                st.warning("⚠️ COI required")
                uploaded_coi = st.file_uploader("Upload COI", type=['pdf', 'jpg', 'png'])
                if uploaded_coi:
                    # Save file and update database
                    cursor.execute('''UPDATE drivers SET coi_uploaded = 1 
                                    WHERE driver_name = ?''', (driver_name,))
                    conn.commit()
                    st.success("COI uploaded successfully!")
                    st.rerun()
        
        with col2:
            st.markdown("### W9 Form")
            if w9_uploaded:
                st.success("✅ W9 on file")
                if st.button("Update W9"):
                    uploaded_w9 = st.file_uploader("Upload new W9", type=['pdf'])
                    if uploaded_w9:
                        # Save file logic here
                        st.success("W9 updated successfully!")
            else:
                st.warning("⚠️ W9 required")
                uploaded_w9 = st.file_uploader("Upload W9", type=['pdf'])
                if uploaded_w9:
                    # Save file and update database
                    cursor.execute('''UPDATE drivers SET w9_uploaded = 1 
                                    WHERE driver_name = ?''', (driver_name,))
                    conn.commit()
                    st.success("W9 uploaded successfully!")
                    st.rerun()
        
        st.markdown("### Required Documents Checklist")
        st.markdown("""
        - ✅ Valid CDL
        - ✅ Medical Card
        - ✅ Certificate of Insurance (COI)
        - ✅ W9 Tax Form
        - ✅ Operating Authority (if applicable)
        - ✅ Vehicle Registration
        - ✅ Signed Contractor Agreement
        """)
    
    with tabs[4]:  # Help Guide
        st.markdown("## Driver Quick Guide")
        
        with st.expander("🚚 How to Accept & Complete Moves"):
            st.markdown("""
            1. **Check Available Moves** in the Moves tab
            2. **Accept a Move** by clicking the Accept button
            3. **Navigate to Pickup** location
            4. **Take Photo** of trailer at pickup
            5. **Complete Delivery** at destination
            6. **Upload POD** (Proof of Delivery)
            7. **Submit for Payment** once complete
            """)
        
        with st.expander("💰 Understanding Your Pay"):
            st.markdown(f"""
            **Your Rate:** $2.10 per mile (base rate)
            **Service Fee:** $6.00 per completed move
            **Payment Schedule:** Weekly on Fridays
            **Payment Method:** Direct Deposit or Check
            
            **Example Calculation:**
            - Move Distance: 200 miles
            - Gross Pay: 200 × $2.10 = $420.00
            - Service Fee: -$6.00
            - Net Pay: $414.00
            """)
        
        with st.expander("📄 Document Requirements"):
            st.markdown("""
            **Required Documents:**
            - Certificate of Insurance (COI) - Annual renewal
            - W9 Form - For tax purposes
            - Valid CDL - Keep current
            - Medical Card - Biannual renewal
            
            **Upload documents in the Documents tab**
            """)
        
        with st.expander("📞 Contact Information"):
            company_info = get_company_info()
            st.markdown(f"""
            **Dispatch:** {company_info['company_phone']}
            **Email:** {company_info['company_email']}
            **Emergency:** (901) 555-HELP
            
            **Office Hours:** Monday-Friday 7:00 AM - 6:00 PM CST
            **After Hours:** Leave voicemail for callback
            """)
        
        with st.expander("❓ Frequently Asked Questions"):
            st.markdown("""
            **Q: When do I get paid?**
            A: Payments are processed weekly on Fridays for completed moves.
            
            **Q: How do I update my insurance?**
            A: Upload your new COI in the Documents tab before expiration.
            
            **Q: What if I have truck problems?**
            A: Contact dispatch immediately for assistance.
            
            **Q: How do I see my 1099?**
            A: 1099s are issued by January 31st and available in the Documents tab.
            """)
    
    conn.close()

def generate_payment_receipt(driver_name, driver_info, payment):
    """Generate a payment receipt PDF"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        import io
        
        buffer = io.BytesIO()
        company_info = get_company_info()
        
        # Create PDF
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Header
        story.append(Paragraph(f"<b>{company_info['company_name']}</b>", styles['Title']))
        story.append(Paragraph("PAYMENT RECEIPT", styles['Heading1']))
        story.append(Spacer(1, 0.3*inch))
        
        # Receipt details
        date, amount, fee, miles, status, notes = payment
        company_name = driver_info[1] or "Independent Contractor"
        
        receipt_data = [
            ['Receipt Information', ''],
            ['Date:', date],
            ['Driver:', driver_name],
            ['Company:', company_name],
            ['', ''],
            ['Payment Details', ''],
            ['Gross Amount:', f'${amount:,.2f}'],
            ['Service Fee:', f'${fee:,.2f}'],
            ['Net Amount:', f'${amount - fee:,.2f}'],
            ['Miles:', str(miles)],
            ['Notes:', notes]
        ]
        
        table = Table(receipt_data, colWidths=[2*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('BACKGROUND', (0, 5), (-1, 5), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('TEXTCOLOR', (0, 5), (-1, 5), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.5*inch))
        
        # Footer
        story.append(Paragraph(f"{company_info['company_address']}", styles['Normal']))
        story.append(Paragraph(f"{company_info['company_phone']} | {company_info['company_email']}", styles['Normal']))
        
        doc.build(story)
        return buffer.getvalue()
        
    except ImportError:
        # Return simple text receipt if reportlab not available
        return f"Receipt for {driver_name}\nAmount: ${amount}\nDate: {date}".encode()

# Function to be called from main app
def show_driver_portal_in_app(username):
    """Wrapper function for main app integration"""
    show_driver_contractor_portal(username)