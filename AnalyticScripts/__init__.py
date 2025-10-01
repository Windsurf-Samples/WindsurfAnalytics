"""
Windsurf Analytics Shared Scripts

This package contains shared utility scripts used across multiple Windsurf Analytics projects.
"""

# Make key functions available at the package level for easier imports
from .email_api_mapping import fetch_email_api_mapping, save_emails_to_json, read_api_keys_from_json
from .cascade_usage_analyzer import (
    read_api_keys_from_json as cascade_read_api_keys_from_json,
    create_payload,
    fetch_data_for_api_key
)

__all__ = [
    # Email API mapping functions
    'fetch_email_api_mapping', 
    'save_emails_to_json', 
    'read_api_keys_from_json',
    
    # Cascade usage analyzer functions
    'cascade_read_api_keys_from_json',
    'create_payload',
    'fetch_data_for_api_key'
]
