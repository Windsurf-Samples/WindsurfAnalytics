#!/usr/bin/env python3
"""
User Activity Checker for Cascade Analytics

This script analyzes Cascade usage data to determine which users have been active
within a specified time period (default: past 30 days).
"""

import os
import csv
import json
import argparse
import datetime
import sys
from collections import defaultdict
from pathlib import Path

# Add parent directory to path to import AnalyticScripts
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Define output directory
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Try to import from AnalyticScripts package
try:
    from AnalyticScripts.email_api_mapping import read_api_keys_from_json
except ImportError:
    print("Warning: Could not import from AnalyticScripts package. Some functionality may be limited.")

def parse_date(date_str):
    """Parse date string in YYYY-MM-DD format"""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Please use YYYY-MM-DD format.")

def get_latest_file(directory, prefix, extension):
    """Find the most recent file with the given prefix and extension in the directory"""
    files = list(Path(directory).glob(f"{prefix}*.{extension}"))
    
    if not files:
        return None
    
    # Sort by modification time, newest first
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return files[0]

def read_api_responses(json_file_path, api_email_map=None):
    """Read raw API responses from JSON file"""
    with open(json_file_path, 'r') as f:
        raw_data = json.load(f)
    
    # Process the raw API responses to extract user activity data
    user_data = {}
    usage_data = defaultdict(list)
    api_key_email_map = api_email_map or {}
    
    # First pass: build API key to email mapping if not provided
    if not api_email_map:
        for api_key, response_data in raw_data.items():
            # Extract email from response data if available
            email = None
            if "queryResults" in response_data and response_data["queryResults"]:
                for query_result in response_data["queryResults"]:
                    if "responseItems" in query_result:
                        for response_item in query_result["responseItems"]:
                            if "item" in response_item:
                                item = response_item["item"]
                                if "metadata" in item and item["metadata"]:
                                    try:
                                        metadata = json.loads(item["metadata"])
                                        if "email" in metadata:
                                            email = metadata["email"]
                                            break
                                    except (json.JSONDecodeError, TypeError):
                                        pass
            
            # If we found an email, map it to the API key
            if email:
                api_key_email_map[api_key] = email
    
    # Second pass: extract usage data
    for api_key, response_data in raw_data.items():
        email = api_key_email_map.get(api_key, f"unknown_{api_key[:8]}")
        
        # Initialize user data if not already present
        if email not in user_data:
            user_data[email] = {
                'api_key': api_key,
                'total_prompts': 0,
                'total_flex_credits': 0,
                'total_prompt_credits': 0
            }
        
        # Extract usage data from response
        if "queryResults" in response_data and response_data["queryResults"]:
            for query_result in response_data["queryResults"]:
                if "responseItems" in query_result:
                    for response_item in query_result["responseItems"]:
                        if "item" in response_item:
                            item = response_item["item"]
                            
                            # Extract date
                            date_str = item.get("date", "")
                            if not date_str:
                                continue
                                
                            try:
                                date = parse_date(date_str)
                                
                                # Extract usage metrics
                                flex_credits = float(item.get("flex_credits_used", 0) or 0) / 100
                                prompts_used = float(item.get("prompts_used", 0) or 0) / 100
                                model = item.get("model", "unknown")
                                
                                # Update user totals
                                user_data[email]['total_prompts'] += 1
                                user_data[email]['total_flex_credits'] += flex_credits
                                user_data[email]['total_prompt_credits'] += prompts_used
                                
                                # Store detailed usage data
                                usage_data[email].append({
                                    'date': date,
                                    'model': model,
                                    'flex_credits': flex_credits,
                                    'prompt_credits': prompts_used
                                })
                                
                            except ValueError:
                                # Skip entries with invalid dates
                                continue
    
    return user_data, usage_data


def check_user_activity(user_data, usage_data, days=30):
    """Check if users have been active within the specified number of days"""
    today = datetime.datetime.now()
    cutoff_date = today - datetime.timedelta(days=days)
    
    active_users = {}
    inactive_users = {}
    
    for email, data in user_data.items():
        # Check if user has detailed usage data
        if email in usage_data and usage_data[email]:
            # Find the most recent usage date
            latest_usage = max(usage_data[email], key=lambda x: x['date'])
            
            if latest_usage['date'] >= cutoff_date:
                # User is active
                active_users[email] = {
                    **data,
                    'last_active': latest_usage['date'].strftime("%Y-%m-%d"),
                    'days_since_last_active': (today - latest_usage['date']).days
                }
            else:
                # User is inactive
                last_active = latest_usage['date'].strftime("%Y-%m-%d")
                days_inactive = (today - latest_usage['date']).days
                    
                inactive_users[email] = {
                    **data,
                    'last_active': last_active,
                    'days_since_last_active': days_inactive
                }
        else:
            # No usage data for this user
            inactive_users[email] = {
                **data,
                'last_active': "Never",
                'days_since_last_active': float('inf')
            }
    
    return active_users, inactive_users

def generate_report(active_users, inactive_users, output_file=None):
    """Generate a report of active and inactive users"""
    # Sort users by days since last active
    sorted_active = sorted(active_users.items(), key=lambda x: x[1]['days_since_last_active'])
    sorted_inactive = sorted(inactive_users.items(), key=lambda x: x[1]['days_since_last_active'])
    
    report = {
        'report_date': datetime.datetime.now().strftime("%Y-%m-%d"),
        'active_users_count': len(active_users),
        'inactive_users_count': len(inactive_users),
        'active_users': dict(sorted_active),
        'inactive_users': dict(sorted_inactive)
    }
    
    # Print summary to console
    print(f"\nUser Activity Report ({report['report_date']})")
    print(f"Active Users: {report['active_users_count']}")
    print(f"Inactive Users: {report['inactive_users_count']}")
    
    print("\nActive Users:")
    for email, data in sorted_active:
        print(f"  - {email}: Last active {data['last_active']} ({data['days_since_last_active']} days ago)")
    
    print("\nInactive Users:")
    for email, data in sorted_inactive:
        if data['last_active'] == "Never":
            print(f"  - {email}: Never active")
        else:
            print(f"  - {email}: Last active {data['last_active']} ({data['days_since_last_active']} days ago)")
    
    # Write report to file if specified
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\nDetailed report saved to {output_file}")
    
    return report

def read_email_api_map(json_file_path):
    """Read email-to-API-key mapping from JSON file"""
    try:
        # Try to use the function from AnalyticScripts if available
        if 'read_api_keys_from_json' in globals():
            return read_api_keys_from_json(json_file_path)
        else:
            # Fallback implementation if AnalyticScripts is not available
            with open(json_file_path, 'r') as f:
                email_api_map = json.load(f)
                # Invert the mapping to get API key to email
                api_email_map = {api_key: email for email, api_key in email_api_map.items()}
                return api_email_map
    except Exception as e:
        print(f"Error reading email-to-API-key mapping file: {e}")
        return {}

def main():
    parser = argparse.ArgumentParser(description='Check user activity within a specified time period')
    parser.add_argument('--days', type=int, default=30,
                        help='Number of days to check for activity (default: 30)')
    parser.add_argument('--raw-file', type=str,
                        help='Path to raw API responses JSON file (default: most recent cascade_api_raw_responses_*.json)')
    parser.add_argument('--email-map', type=str,
                        help='Path to email-to-API-key mapping JSON file')
    parser.add_argument('--output', type=str,
                        help='Output file for detailed report (JSON format)')
    parser.add_argument('--directory', type=str, default='.',
                        help='Directory to search for files (default: current directory)')
    args = parser.parse_args()
    
    # Find the most recent raw API responses JSON file if not specified
    if not args.raw_file:
        raw_file = get_latest_file(args.directory, prefix="cascade_api_raw_responses_", extension="json")
        if not raw_file:
            print("Error: No raw API responses JSON file found. Please specify with --raw-file.")
            return
        args.raw_file = raw_file
    
    print(f"Using raw API responses file: {args.raw_file}")
    
    # Read email-to-API-key mapping if provided
    api_email_map = {}
    if args.email_map:
        print(f"Loading email-to-API-key mapping from {args.email_map}...")
        api_email_map = read_email_api_map(args.email_map)
        print(f"Loaded {len(api_email_map)} API key to email mappings")
    else:
        # Try to find the most recent email_api_mapping file
        mapping_file = get_latest_file(args.directory, prefix="email_api_mapping_", extension="json")
        if mapping_file:
            print(f"Found email mapping file: {mapping_file}")
            api_email_map = read_email_api_map(mapping_file)
            print(f"Loaded {len(api_email_map)} API key to email mappings")
        else:
            print("No email mapping file found. Users will be identified by API key prefix.")
    
    # Read user data and usage data from raw API responses JSON
    user_data, usage_data = read_api_responses(args.raw_file, api_email_map)
    print(f"Found data for {len(user_data)} users in raw API responses file")
    
    # Check user activity
    active_users, inactive_users = check_user_activity(user_data, usage_data, days=args.days)
    
    # Generate report
    # Generate output filename with timestamp
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d')
    output_file = args.output or os.path.join(OUTPUT_DIR, f"user_activity_report_{timestamp}.json")
    generate_report(active_users, inactive_users, output_file)

if __name__ == "__main__":
    main()
