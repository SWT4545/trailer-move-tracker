"""
API Configuration Module
Vernon AI - External Service Integration Configuration
"""

import os
import streamlit as st
from typing import Dict, Optional

def get_api_config() -> Dict[str, Optional[str]]:
    """Get API configuration from environment or secrets"""
    config = {}
    
    # Try to get from Streamlit secrets first
    try:
        if hasattr(st, 'secrets'):
            config['google_maps_api_key'] = st.secrets.get('GOOGLE_MAPS_API_KEY', '')
            config['twilio_account_sid'] = st.secrets.get('TWILIO_ACCOUNT_SID', '')
            config['twilio_auth_token'] = st.secrets.get('TWILIO_AUTH_TOKEN', '')
            config['twilio_phone_number'] = st.secrets.get('TWILIO_PHONE_NUMBER', '')
            config['smtp_server'] = st.secrets.get('SMTP_SERVER', 'smtp.gmail.com')
            config['smtp_port'] = st.secrets.get('SMTP_PORT', 587)
            config['smtp_username'] = st.secrets.get('SMTP_USERNAME', '')
            config['smtp_password'] = st.secrets.get('SMTP_PASSWORD', '')
    except:
        pass
    
    # Fall back to environment variables
    if not config.get('google_maps_api_key'):
        config['google_maps_api_key'] = os.environ.get('GOOGLE_MAPS_API_KEY', '')
    
    if not config.get('twilio_account_sid'):
        config['twilio_account_sid'] = os.environ.get('TWILIO_ACCOUNT_SID', '')
        config['twilio_auth_token'] = os.environ.get('TWILIO_AUTH_TOKEN', '')
        config['twilio_phone_number'] = os.environ.get('TWILIO_PHONE_NUMBER', '')
    
    if not config.get('smtp_username'):
        config['smtp_server'] = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        config['smtp_port'] = int(os.environ.get('SMTP_PORT', 587))
        config['smtp_username'] = os.environ.get('SMTP_USERNAME', '')
        config['smtp_password'] = os.environ.get('SMTP_PASSWORD', '')
    
    return config

def get_google_maps_key() -> str:
    """Get Google Maps API key"""
    config = get_api_config()
    return config.get('google_maps_api_key', '')

def get_twilio_config() -> Dict[str, str]:
    """Get Twilio configuration"""
    config = get_api_config()
    return {
        'account_sid': config.get('twilio_account_sid', ''),
        'auth_token': config.get('twilio_auth_token', ''),
        'phone_number': config.get('twilio_phone_number', '')
    }

def get_smtp_config() -> Dict[str, any]:
    """Get SMTP email configuration"""
    config = get_api_config()
    return {
        'server': config.get('smtp_server', 'smtp.gmail.com'),
        'port': config.get('smtp_port', 587),
        'username': config.get('smtp_username', ''),
        'password': config.get('smtp_password', '')
    }

def validate_api_keys() -> Dict[str, bool]:
    """Validate which API keys are configured"""
    config = get_api_config()
    return {
        'google_maps': bool(config.get('google_maps_api_key')),
        'twilio': bool(config.get('twilio_account_sid') and config.get('twilio_auth_token')),
        'smtp': bool(config.get('smtp_username') and config.get('smtp_password'))
    }