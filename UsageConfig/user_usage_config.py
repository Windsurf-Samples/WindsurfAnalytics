#!/usr/bin/env python3
"""
User Usage Configuration Manager

This script provides functionality to get, set, and clear add-on credit caps
for individual users via the Windsurf Usage API.

The Usage API is scope-based, meaning each API call targets a specific scope
(team_level, group_id, or user_email). Setting a cap for one user does NOT
affect other users' configurations.

API Endpoints:
- POST /api/v1/UsageConfig - Set or clear usage caps
- POST /api/v1/GetUsageConfig - Retrieve current usage caps

Usage:
    # Get a user's current credit cap
    python3 user_usage_config.py get --email user@example.com

    # Set a user's credit cap
    python3 user_usage_config.py set --email user@example.com --credit-cap 1000

    # Clear a user's credit cap
    python3 user_usage_config.py clear --email user@example.com

    # Set with verification (checks other users aren't affected)
    python3 user_usage_config.py set --email user@example.com --credit-cap 1000 --verify-others user2@example.com,user3@example.com
"""

import os
import json
import requests
import argparse
import sys
from dotenv import load_dotenv

# Define output directory
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load environment variables from .env file
load_dotenv()

# Get service key from environment
SERVICE_KEY = os.getenv("SERVICE_KEY")

# API configuration
SET_USAGE_CONFIG_URL = "https://server.codeium.com/api/v1/UsageConfig"
GET_USAGE_CONFIG_URL = "https://server.codeium.com/api/v1/GetUsageConfig"


def validate_service_key():
    """Validate that the service key is configured."""
    if not SERVICE_KEY:
        print("Error: SERVICE_KEY not found in .env file")
        print("Please configure your service key in the .env file")
        print("See .env.example for reference")
        sys.exit(1)


def get_user_usage_config(email):
    """
    Get the current add-on credit cap configuration for a specific user.
    
    Args:
        email: The user's email address
        
    Returns:
        dict: The usage configuration, or None if an error occurred
              Returns {'add_on_credit_cap': value} if configured,
              or {} if no cap is configured
    """
    headers = {"Content-Type": "application/json"}
    payload = {
        "service_key": SERVICE_KEY,
        "user_email": email
    }
    
    try:
        response = requests.post(GET_USAGE_CONFIG_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting usage config for {email}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            try:
                error_data = e.response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except Exception:
                print(f"Response text: {e.response.text}")
        return None


def set_user_usage_config(email, credit_cap):
    """
    Set the add-on credit cap for a specific user.
    
    This operation only affects the specified user's configuration.
    Other users' configurations remain unchanged.
    
    Args:
        email: The user's email address
        credit_cap: The credit cap value to set (integer)
        
    Returns:
        bool: True if successful, False otherwise
    """
    headers = {"Content-Type": "application/json"}
    payload = {
        "service_key": SERVICE_KEY,
        "user_email": email,
        "set_add_on_credit_cap": int(credit_cap)
    }
    
    try:
        response = requests.post(SET_USAGE_CONFIG_URL, headers=headers, json=payload)
        response.raise_for_status()
        print(f"Successfully set credit cap to {credit_cap} for {email}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error setting usage config for {email}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            try:
                error_data = e.response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except Exception:
                print(f"Response text: {e.response.text}")
        return False


def clear_user_usage_config(email):
    """
    Clear the add-on credit cap for a specific user.
    
    This removes any user-specific cap, allowing the user to fall back
    to group-level or team-level defaults.
    
    Args:
        email: The user's email address
        
    Returns:
        bool: True if successful, False otherwise
    """
    headers = {"Content-Type": "application/json"}
    payload = {
        "service_key": SERVICE_KEY,
        "user_email": email,
        "clear_add_on_credit_cap": True
    }
    
    try:
        response = requests.post(SET_USAGE_CONFIG_URL, headers=headers, json=payload)
        response.raise_for_status()
        print(f"Successfully cleared credit cap for {email}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error clearing usage config for {email}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            try:
                error_data = e.response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except Exception:
                print(f"Response text: {e.response.text}")
        return False


def verify_other_users_unchanged(emails, before_configs, after_configs):
    """
    Verify that other users' configurations haven't changed.
    
    Args:
        emails: List of email addresses to verify
        before_configs: Dict mapping email to config before the operation
        after_configs: Dict mapping email to config after the operation
        
    Returns:
        bool: True if all configs are unchanged, False otherwise
    """
    all_unchanged = True
    
    for email in emails:
        before = before_configs.get(email, {})
        after = after_configs.get(email, {})
        
        if before != after:
            print(f"WARNING: Configuration changed for {email}")
            print(f"  Before: {before}")
            print(f"  After: {after}")
            all_unchanged = False
        else:
            print(f"Verified: {email} configuration unchanged")
    
    return all_unchanged


def get_configs_for_emails(emails):
    """
    Get configurations for multiple email addresses.
    
    Args:
        emails: List of email addresses
        
    Returns:
        dict: Mapping of email to configuration
    """
    configs = {}
    for email in emails:
        config = get_user_usage_config(email)
        if config is not None:
            configs[email] = config
    return configs


def get_credit_cap_from_config(config):
    """
    Extract the credit cap value from a config response.
    
    The API returns 'addOnCreditCap' (camelCase) but we handle both formats
    for robustness.
    
    Args:
        config: The API response dictionary
        
    Returns:
        The credit cap value, or None if not configured
    """
    if config is None:
        return None
    # API returns camelCase 'addOnCreditCap'
    if 'addOnCreditCap' in config:
        return config['addOnCreditCap']
    # Also check snake_case for robustness
    if 'add_on_credit_cap' in config:
        return config['add_on_credit_cap']
    return None


def cmd_get(args):
    """Handle the 'get' command."""
    validate_service_key()
    
    config = get_user_usage_config(args.email)
    if config is not None:
        credit_cap = get_credit_cap_from_config(config)
        print(f"User: {args.email}")
        if credit_cap is not None:
            print(f"Add-on Credit Cap: {credit_cap}")
        else:
            print("Add-on Credit Cap: Not configured (no cap set)")
        
        if args.json:
            print(f"\nRaw response: {json.dumps(config, indent=2)}")


def cmd_set(args):
    """Handle the 'set' command."""
    validate_service_key()
    
    # Get current config for the target user
    print(f"\nGetting current configuration for {args.email}...")
    current_config = get_user_usage_config(args.email)
    if current_config is not None:
        current_cap = get_credit_cap_from_config(current_config)
        if current_cap is not None:
            print(f"Current credit cap: {current_cap}")
        else:
            print("Current credit cap: Not configured")
    
    # If verification is requested, get configs for other users before the change
    before_configs = {}
    verify_emails = []
    if args.verify_others:
        verify_emails = [e.strip() for e in args.verify_others.split(',')]
        print(f"\nGetting configurations for verification users: {verify_emails}")
        before_configs = get_configs_for_emails(verify_emails)
    
    # Set the new credit cap
    print(f"\nSetting credit cap to {args.credit_cap} for {args.email}...")
    success = set_user_usage_config(args.email, args.credit_cap)
    
    if success:
        # Verify the change was applied
        print(f"\nVerifying change was applied...")
        new_config = get_user_usage_config(args.email)
        if new_config is not None:
            new_cap = get_credit_cap_from_config(new_config)
            if new_cap is not None:
                print(f"New credit cap: {new_cap}")
            else:
                print("Warning: Credit cap not found in response after setting")
        
        # If verification is requested, check other users weren't affected
        if verify_emails:
            print(f"\nVerifying other users' configurations weren't affected...")
            after_configs = get_configs_for_emails(verify_emails)
            if verify_other_users_unchanged(verify_emails, before_configs, after_configs):
                print("\nVerification passed: Other users' configurations are unchanged")
            else:
                print("\nVerification FAILED: Some users' configurations changed unexpectedly")


def cmd_clear(args):
    """Handle the 'clear' command."""
    validate_service_key()
    
    # Get current config for the target user
    print(f"\nGetting current configuration for {args.email}...")
    current_config = get_user_usage_config(args.email)
    if current_config is not None:
        current_cap = get_credit_cap_from_config(current_config)
        if current_cap is not None:
            print(f"Current credit cap: {current_cap}")
        else:
            print("Current credit cap: Not configured")
    
    # If verification is requested, get configs for other users before the change
    before_configs = {}
    verify_emails = []
    if args.verify_others:
        verify_emails = [e.strip() for e in args.verify_others.split(',')]
        print(f"\nGetting configurations for verification users: {verify_emails}")
        before_configs = get_configs_for_emails(verify_emails)
    
    # Clear the credit cap
    print(f"\nClearing credit cap for {args.email}...")
    success = clear_user_usage_config(args.email)
    
    if success:
        # Verify the change was applied
        print(f"\nVerifying change was applied...")
        new_config = get_user_usage_config(args.email)
        if new_config is not None:
            new_cap = get_credit_cap_from_config(new_config)
            if new_cap is not None:
                print(f"Warning: Credit cap still present: {new_cap}")
            else:
                print("Credit cap successfully cleared")
        
        # If verification is requested, check other users weren't affected
        if verify_emails:
            print(f"\nVerifying other users' configurations weren't affected...")
            after_configs = get_configs_for_emails(verify_emails)
            if verify_other_users_unchanged(verify_emails, before_configs, after_configs):
                print("\nVerification passed: Other users' configurations are unchanged")
            else:
                print("\nVerification FAILED: Some users' configurations changed unexpectedly")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Manage user add-on credit cap configurations via the Windsurf Usage API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Get a user's current credit cap:
    python3 user_usage_config.py get --email user@example.com

  Set a user's credit cap to 1000:
    python3 user_usage_config.py set --email user@example.com --credit-cap 1000

  Set with verification that other users aren't affected:
    python3 user_usage_config.py set --email user@example.com --credit-cap 1000 \\
        --verify-others user2@example.com,user3@example.com

  Clear a user's credit cap:
    python3 user_usage_config.py clear --email user@example.com

Note:
  The Usage API is scope-based. Setting a cap for one user does NOT affect
  other users' configurations. Each user, group, and team has independent
  configuration settings.
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Get current usage configuration for a user')
    get_parser.add_argument('--email', required=True, help='User email address')
    get_parser.add_argument('--json', action='store_true', help='Output raw JSON response')
    get_parser.set_defaults(func=cmd_get)
    
    # Set command
    set_parser = subparsers.add_parser('set', help='Set usage configuration for a user')
    set_parser.add_argument('--email', required=True, help='User email address')
    set_parser.add_argument('--credit-cap', type=int, required=True, help='Credit cap value to set')
    set_parser.add_argument('--verify-others', type=str, 
                           help='Comma-separated list of other user emails to verify are unchanged')
    set_parser.set_defaults(func=cmd_set)
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear usage configuration for a user')
    clear_parser.add_argument('--email', required=True, help='User email address')
    clear_parser.add_argument('--verify-others', type=str,
                             help='Comma-separated list of other user emails to verify are unchanged')
    clear_parser.set_defaults(func=cmd_clear)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
