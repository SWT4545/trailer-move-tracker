# -*- coding: utf-8 -*-
"""Vernon IT Support - Black Theme"""

import streamlit as st

VERNON_ICON = "[Vernon IT]"  # Text representation

def show_vernon():
    """Show Vernon support"""
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"### {VERNON_ICON}")
        st.markdown("*IT Support Assistant*")
        
        if st.button("Get Help"):
            st.info("Vernon: How can I help you today?")
