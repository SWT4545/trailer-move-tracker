# -*- coding: utf-8 -*-
"""UI Fixes for all pages"""

import streamlit as st

def add_cancel_button(form_key="form"):
    """Add cancel button to forms"""
    col1, col2 = st.columns(2)
    with col1:
        submit = st.form_submit_button("Submit", type="primary")
    with col2:
        cancel = st.form_submit_button("Cancel")
        if cancel:
            st.session_state.clear()
            st.rerun()
    return submit, cancel

def initialize_dashboard():
    """Safe dashboard initialization"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
    return True
