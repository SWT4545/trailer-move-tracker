"""
Simple Payment Confirmation System
Quick checkbox to mark payments sent via Navy Federal
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

def get_connection():
    return sqlite3.connect('trailer_tracker_streamlined.db')

def show_simple_payment_confirmation():
    """Simple payment confirmation interface"""
    st.markdown("## ✅ Payment Confirmation")
    st.info("Check off payments as they are sent via Navy Federal transfer")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get moves ready for payment (completed with all documents)
    cursor.execute('''SELECT m.id, m.move_id, m.driver_name, m.total_miles, 
                            m.driver_pay, m.completed_date, m.payment_status,
                            dr.all_docs_complete,
                            ROUND(m.driver_pay * 0.03, 2) as est_fee,
                            ROUND(m.driver_pay * 0.97, 2) as est_net
                     FROM moves m
                     LEFT JOIN document_requirements dr ON m.move_id = dr.move_id
                     WHERE m.status = 'completed'
                     AND (dr.all_docs_complete = 1 OR dr.all_docs_complete IS NOT NULL)
                     ORDER BY 
                        CASE WHEN m.payment_status = 'paid' THEN 1 ELSE 0 END,
                        m.completed_date DESC''')
    
    moves = cursor.fetchall()
    
    if moves:
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        pending_moves = [m for m in moves if m[6] != 'paid']
        paid_moves = [m for m in moves if m[6] == 'paid']
        
        with col1:
            st.metric("Pending Payment", len(pending_moves))
        with col2:
            st.metric("Paid", len(paid_moves))
        with col3:
            pending_amount = sum(m[9] for m in pending_moves)  # est_net
            st.metric("Amount Due", f"${pending_amount:,.2f}")
        
        st.markdown("---")
        
        # Payment tabs
        tabs = st.tabs(["💳 Ready to Pay", "✅ Payment History"])
        
        with tabs[0]:  # Ready to Pay
            st.markdown("### Moves Ready for Payment")
            st.caption("Check the box when payment is sent via Navy Federal")
            
            if pending_moves:
                # Batch payment option
                if st.checkbox("Select All for Batch Payment"):
                    selected_all = True
                else:
                    selected_all = False
                
                selected_moves = []
                total_to_pay = 0
                
                for move in pending_moves:
                    move_id_db, move_id, driver, miles, gross, comp_date, pay_status, docs_complete, fee, net = move
                    
                    col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 1, 1])
                    
                    with col1:
                        # Payment checkbox
                        is_selected = st.checkbox(
                            "Pay",
                            key=f"pay_{move_id_db}",
                            value=selected_all
                        )
                        
                        if is_selected:
                            selected_moves.append((move_id_db, move_id, driver, net))
                            total_to_pay += net
                    
                    with col2:
                        st.write(f"**{move_id}**")
                        st.caption(f"{driver}")
                    
                    with col3:
                        st.write(f"{miles} miles")
                        st.caption(f"Completed {comp_date}")
                    
                    with col4:
                        st.write(f"${gross:.2f}")
                        st.caption(f"Less 3%: ${fee:.2f}")
                    
                    with col5:
                        st.write(f"**Net: ${net:.2f}**")
                        if docs_complete:
                            st.success("📄 Docs ✓")
                        else:
                            st.warning("📄 Check docs")
                
                if selected_moves:
                    st.markdown("---")
                    st.markdown("### Confirm Payment")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Moves Selected", len(selected_moves))
                    with col2:
                        st.metric("Total to Pay", f"${total_to_pay:.2f}")
                    with col3:
                        confirm_date = st.date_input("Payment Date", datetime.now())
                    
                    # Robust confirmation system
                    st.warning("⚠️ Please confirm payment details before proceeding")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        confirm_text = st.text_input(
                            "Type 'CONFIRM' to proceed",
                            help="This action cannot be undone"
                        )
                    
                    with col2:
                        reference_num = st.text_input(
                            "Navy Federal Reference # (optional)",
                            placeholder="Transaction reference"
                        )
                    
                    # Double confirmation checkbox
                    confirm_check = st.checkbox(
                        f"I confirm that ${total_to_pay:.2f} has been sent via Navy Federal to {len(selected_moves)} driver(s)"
                    )
                    
                    # Final confirmation button (only enabled with proper confirmation)
                    button_disabled = not (confirm_text == "CONFIRM" and confirm_check)
                    
                    if st.button(
                        "✅ Confirm Navy Federal Transfer Sent", 
                        type="primary", 
                        use_container_width=True,
                        disabled=button_disabled
                    ):
                        # Update all selected moves as paid
                        for move_id_db, move_id, driver, net in selected_moves:
                            # Update move status
                            cursor.execute('''UPDATE moves 
                                           SET payment_status = 'paid',
                                               payment_date = ?,
                                               payment_method = 'Navy Federal Transfer',
                                               service_fee = driver_pay * 0.03,
                                               net_pay = driver_pay * 0.97
                                           WHERE id = ?''',
                                         (confirm_date, move_id_db))
                            
                            # Create payment record with reference
                            notes = f'Navy Federal Transfer'
                            if reference_num:
                                notes += f' - Ref: {reference_num}'
                            
                            cursor.execute('''INSERT INTO payments 
                                           (driver_name, amount, service_fee, status, 
                                            payment_date, move_id, notes)
                                           VALUES (?, ?, ?, 'paid', ?, ?, ?)''',
                                         (driver, net, net * 0.03 / 0.97, confirm_date, 
                                          move_id, notes))
                            
                            # Log notification (would trigger actual notification in production)
                            cursor.execute('''INSERT INTO notifications 
                                           (recipient, type, message, created_at)
                                           VALUES (?, 'payment', ?, ?)''',
                                         (driver, f'Payment of ${net:.2f} sent for move {move_id}',
                                          datetime.now()))
                        
                        conn.commit()
                        
                        st.success(f"""
                        ✅ Payment Confirmed!
                        - {len(selected_moves)} payments marked as sent
                        - Total: ${total_to_pay:.2f}
                        - Drivers will be notified
                        """)
                        
                        # Show summary
                        with st.expander("Payment Summary"):
                            for _, move_id, driver, net in selected_moves:
                                st.write(f"- {driver}: ${net:.2f} for {move_id}")
                        
                        st.rerun()
            else:
                st.info("No moves pending payment. All caught up! 🎉")
        
        with tabs[1]:  # Payment History
            st.markdown("### Recent Payments")
            
            if paid_moves:
                # Show last 20 paid moves
                for move in paid_moves[:20]:
                    move_id_db, move_id, driver, miles, gross, comp_date, pay_status, docs_complete, fee, net = move
                    
                    # Get payment date
                    cursor.execute('SELECT payment_date FROM moves WHERE id = ?', (move_id_db,))
                    pay_date = cursor.fetchone()[0]
                    
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    
                    with col1:
                        st.write(f"✅ **{move_id}** - {driver}")
                        st.caption(f"Paid: {pay_date}")
                    
                    with col2:
                        st.write(f"{miles} miles")
                    
                    with col3:
                        st.write(f"Gross: ${gross:.2f}")
                    
                    with col4:
                        st.write(f"**Net: ${net:.2f}**")
                
                # Export option
                if st.button("📥 Export Payment History"):
                    df = pd.DataFrame(paid_moves, columns=[
                        'ID', 'Move ID', 'Driver', 'Miles', 'Gross Pay', 
                        'Completed', 'Status', 'Docs', 'Fee', 'Net Pay'
                    ])
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "Download CSV",
                        csv,
                        "payment_history.csv",
                        "text/csv"
                    )
            else:
                st.info("No payment history yet")
    
    else:
        st.info("No completed moves found")
    
    conn.close()

def check_payment_notifications():
    """Check for pending payment notifications to send"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get recent payments that need notification
    cursor.execute('''SELECT driver_name, amount, move_id 
                     FROM payments 
                     WHERE payment_date = date('now')
                     AND status = 'paid' ''')
    
    notifications = cursor.fetchall()
    conn.close()
    
    return notifications