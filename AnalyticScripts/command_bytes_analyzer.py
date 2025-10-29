#!/usr/bin/env python3
"""
Command Bytes Analytics Client

This script retrieves command bytes added data from the Windsurf Analytics API.
It can analyze bytes added by users through Cascade commands over a specified date range.
"""

import os
import json
import requests
import csv
import argparse
import datetime
from collections import defaultdict
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Define output directory
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load environment variables from .env file
load_dotenv()

# Get service key from environment (try both possible names)
SERVICE_KEY = os.getenv("SERVICE_KEY")

# Validate service key
if not SERVICE_KEY:
    raise ValueError("SERVICE_KEY not found in .env file")

# API configuration
API_URL = "https://server.codeium.com/api/v1/Analytics"

def get_default_start_date():
    """Get default start date (7 days ago)"""
    return (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")

def get_default_end_date():
    """Get default end date (today)"""
    return datetime.datetime.now().strftime("%Y-%m-%d")

def parse_date(date_str):
    """Parse date string in YYYY-MM-DD format"""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Please use YYYY-MM-DD format.")

def create_command_bytes_payload(start_date: str, end_date: str, api_keys: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Create request payload for command bytes analytics.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        api_keys: Optional list of specific API keys to filter by
        
    Returns:
        Dictionary containing the API request payload
    """
    selections = [
        {"field": "api_key", "name": "api_key"},
        {"field": "date", "name": "date"},
        {"field": "timestamp", "name": "timestamp"},
        {"field": "language", "name": "language"},
        {"field": "ide", "name": "ide"},
        {"field": "command_source", "name": "command_source"},
        {"field": "provider_source", "name": "provider_source"},
        {"field": "bytes_added", "name": "bytes_added"},
        {"field": "bytes_removed", "name": "bytes_removed"},
        {"field": "lines_added", "name": "lines_added"},
        {"field": "lines_removed", "name": "lines_removed"},
        {"field": "accepted", "name": "accepted"}
    ]
    
    filters = [
        {
            "name": "date",
            "filter": "QUERY_FILTER_GE",
            "value": start_date
        },
        {
            "name": "date",
            "filter": "QUERY_FILTER_LE", 
            "value": end_date
        },
        # Note: Commented out accepted filter to see all commands including those with <nil> accepted status
        # {
        #     "name": "accepted",
        #     "filter": "QUERY_FILTER_EQUAL",
        #     "value": "true"  # Only accepted commands
        # }
    ]
    
    # Add API key filters if specified
    if api_keys:
        for api_key in api_keys:
            filters.append({
                "name": "api_key",
                "filter": "QUERY_FILTER_EQUAL",
                "value": api_key
            })
    
    return {
        "service_key": SERVICE_KEY,
        "query_requests": [
            {
                "data_source": "QUERY_DATA_SOURCE_COMMAND_DATA",
                "selections": selections,
                "filters": filters
            }
        ]
    }

def fetch_command_bytes_data(start_date: str, end_date: str, api_keys: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Fetch command bytes data from the Windsurf Analytics API.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        api_keys: Optional list of specific API keys to filter by
        
    Returns:
        List of command data items
    """
    print(f"Fetching command bytes data from {start_date} to {end_date}...")
    if api_keys:
        print(f"Filtering for {len(api_keys)} specific API keys")
    
    payload = create_command_bytes_payload(start_date, end_date, api_keys)
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        
        data = response.json()
        
        # Extract items from the response
        items = []
        if "queryResults" in data and data["queryResults"]:
            for query_result in data["queryResults"]:
                if "responseItems" in query_result:
                    for response_item in query_result["responseItems"]:
                        if "item" in response_item:
                            items.append(response_item["item"])
        
        print(f"Retrieved {len(items)} command records")
        return items
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching command bytes data: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            try:
                error_data = e.response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Response text: {e.response.text}")
        return []

def analyze_command_bytes(items: List[Dict[str, Any]], email_api_map: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Analyze command bytes data and generate statistics.
    
    Args:
        items: List of command data items from the API
        email_api_map: Optional mapping of API keys to email addresses
        
    Returns:
        Dictionary containing analysis results
    """
    if not items:
        return {"error": "No data to analyze"}
    
    # Initialize statistics
    stats = {
        "total_commands": len(items),
        "total_bytes_added": 0,
        "total_bytes_removed": 0,
        "total_lines_added": 0,
        "total_lines_removed": 0,
        "by_user": defaultdict(lambda: {
            "commands": 0,
            "bytes_added": 0,
            "bytes_removed": 0,
            "lines_added": 0,
            "lines_removed": 0,
            "languages": set(),
            "ides": set()
        }),
        "by_language": defaultdict(lambda: {
            "commands": 0,
            "bytes_added": 0,
            "bytes_removed": 0
        }),
        "by_ide": defaultdict(lambda: {
            "commands": 0,
            "bytes_added": 0,
            "bytes_removed": 0
        }),
        "by_date": defaultdict(lambda: {
            "commands": 0,
            "bytes_added": 0,
            "bytes_removed": 0
        })
    }
    
    for item in items:
        api_key = item.get("api_key", "unknown")
        user_id = email_api_map.get(api_key, api_key[:8] + "...") if email_api_map else api_key[:8] + "..."
        
        bytes_added = int(item.get("bytes_added", 0))
        bytes_removed = int(item.get("bytes_removed", 0))
        lines_added = int(item.get("lines_added", 0))
        lines_removed = int(item.get("lines_removed", 0))
        language = item.get("language", "unknown")
        ide = item.get("ide", "unknown")
        date = item.get("date", "unknown")
        
        # Update totals
        stats["total_bytes_added"] += bytes_added
        stats["total_bytes_removed"] += bytes_removed
        stats["total_lines_added"] += lines_added
        stats["total_lines_removed"] += lines_removed
        
        # Update by user
        user_stats = stats["by_user"][user_id]
        user_stats["commands"] += 1
        user_stats["bytes_added"] += bytes_added
        user_stats["bytes_removed"] += bytes_removed
        user_stats["lines_added"] += lines_added
        user_stats["lines_removed"] += lines_removed
        user_stats["languages"].add(language)
        user_stats["ides"].add(ide)
        
        # Update by language
        lang_stats = stats["by_language"][language]
        lang_stats["commands"] += 1
        lang_stats["bytes_added"] += bytes_added
        lang_stats["bytes_removed"] += bytes_removed
        
        # Update by IDE
        ide_stats = stats["by_ide"][ide]
        ide_stats["commands"] += 1
        ide_stats["bytes_added"] += bytes_added
        ide_stats["bytes_removed"] += bytes_removed
        
        # Update by date
        date_stats = stats["by_date"][date]
        date_stats["commands"] += 1
        date_stats["bytes_added"] += bytes_added
        date_stats["bytes_removed"] += bytes_removed
    
    # Convert sets to lists for JSON serialization
    for user_stats in stats["by_user"].values():
        user_stats["languages"] = list(user_stats["languages"])
        user_stats["ides"] = list(user_stats["ides"])
    
    return stats

def save_results_to_csv(stats: Dict[str, Any], start_date: str, end_date: str) -> str:
    """
    Save analysis results to CSV files.
    
    Args:
        stats: Analysis results dictionary
        start_date: Start date for filename
        end_date: End date for filename
        
    Returns:
        Path to the main summary CSV file
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"command_bytes_analysis_{start_date}_to_{end_date}_{timestamp}"
    
    # Save user summary
    user_csv_path = os.path.join(OUTPUT_DIR, f"{base_filename}_by_user.csv")
    with open(user_csv_path, 'w', newline='') as csvfile:
        fieldnames = ['user', 'commands', 'bytes_added', 'bytes_removed', 'lines_added', 'lines_removed', 'languages', 'ides']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for user, user_stats in stats["by_user"].items():
            writer.writerow({
                'user': user,
                'commands': user_stats['commands'],
                'bytes_added': user_stats['bytes_added'],
                'bytes_removed': user_stats['bytes_removed'],
                'lines_added': user_stats['lines_added'],
                'lines_removed': user_stats['lines_removed'],
                'languages': ', '.join(user_stats['languages']),
                'ides': ', '.join(user_stats['ides'])
            })
    
    # Save language summary
    lang_csv_path = os.path.join(OUTPUT_DIR, f"{base_filename}_by_language.csv")
    with open(lang_csv_path, 'w', newline='') as csvfile:
        fieldnames = ['language', 'commands', 'bytes_added', 'bytes_removed']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for language, lang_stats in sorted(stats["by_language"].items()):
            writer.writerow({
                'language': language,
                'commands': lang_stats['commands'],
                'bytes_added': lang_stats['bytes_added'],
                'bytes_removed': lang_stats['bytes_removed']
            })
    
    # Save daily summary
    daily_csv_path = os.path.join(OUTPUT_DIR, f"{base_filename}_by_date.csv")
    with open(daily_csv_path, 'w', newline='') as csvfile:
        fieldnames = ['date', 'commands', 'bytes_added', 'bytes_removed']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for date, date_stats in sorted(stats["by_date"].items()):
            writer.writerow({
                'date': date,
                'commands': date_stats['commands'],
                'bytes_added': date_stats['bytes_added'],
                'bytes_removed': date_stats['bytes_removed']
            })
    
    print(f"Results saved to:")
    print(f"  - User summary: {user_csv_path}")
    print(f"  - Language summary: {lang_csv_path}")
    print(f"  - Daily summary: {daily_csv_path}")
    
    return user_csv_path

def get_api_key_for_email(email: str) -> Optional[str]:
    """
    Get API key for a specific email address.
    
    Args:
        email: Email address to look up
        
    Returns:
        API key string or None if not found
    """
    try:
        import glob
        pattern = os.path.join(OUTPUT_DIR, 'email_api_mapping_*.json')
        files = glob.glob(pattern)
        if not files:
            print("No email-API mapping file found.")
            return None
        
        # Sort by filename (which includes date) and get the latest
        mapping_file = sorted(files)[-1]
        
        with open(mapping_file, 'r') as f:
            email_api_map = json.load(f)
            api_key = email_api_map.get(email)
            if api_key:
                print(f"Found API key for {email}: {api_key[:8]}...")
                return api_key
            else:
                print(f"Email {email} not found in mapping.")
                # Show similar emails
                similar = [e for e in email_api_map.keys() if email.split('@')[0].lower() in e.lower()]
                if similar:
                    print(f"Similar emails found: {similar}")
                return None
    except Exception as e:
        print(f"Error looking up email: {e}")
        return None

def load_email_api_mapping() -> Optional[Dict[str, str]]:
    """
    Load email-to-API-key mapping from the latest mapping file.
    
    Returns:
        Dictionary mapping API keys to emails, or None if not found
    """
    try:
        # Try to find the latest mapping file directly
        import glob
        pattern = os.path.join(OUTPUT_DIR, 'email_api_mapping_*.json')
        files = glob.glob(pattern)
        if not files:
            print("No email-API mapping file found. User identification will use API key prefixes.")
            return None
        
        # Sort by filename (which includes date) and get the latest
        mapping_file = sorted(files)[-1]
        
        print(f"Loading email mapping from: {mapping_file}")
        with open(mapping_file, 'r') as f:
            email_api_map = json.load(f)
            # Invert the mapping (email -> api_key becomes api_key -> email)
            api_email_map = {api_key: email for email, api_key in email_api_map.items()}
            print(f"Loaded mapping for {len(api_email_map)} users")
            return api_email_map
    except Exception as e:
        print(f"Could not load email mapping: {e}")
        return None

def main():
    """Main function to run the command bytes analyzer."""
    parser = argparse.ArgumentParser(description="Analyze Windsurf command bytes data")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)", default=get_default_start_date())
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)", default=get_default_end_date())
    parser.add_argument("--api-keys", type=str, nargs='+', help="Specific API keys to analyze")
    parser.add_argument("--emails", type=str, nargs='+', help="Specific email addresses to analyze (will be converted to API keys)")
    parser.add_argument("--output-json", action="store_true", help="Also save results as JSON")
    
    args = parser.parse_args()
    
    # Validate dates
    try:
        start_date = parse_date(args.start_date)
        end_date = parse_date(args.end_date)
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    
    # Handle email to API key conversion
    api_keys = args.api_keys or []
    if args.emails:
        print(f"Converting {len(args.emails)} email(s) to API keys...")
        for email in args.emails:
            api_key = get_api_key_for_email(email)
            if api_key:
                api_keys.append(api_key)
            else:
                print(f"Warning: Could not find API key for {email}")
        
        if not api_keys:
            print("Error: No valid API keys found for the provided emails.")
            return 1
    
    # Load email mapping
    email_api_map = load_email_api_mapping()
    
    # Fetch data
    items = fetch_command_bytes_data(start_date, end_date, api_keys)
    
    if not items:
        print("No command data found for the specified criteria.")
        return 1
    
    # Analyze data
    stats = analyze_command_bytes(items, email_api_map)
    
    # Print summary
    print(f"\n=== Command Bytes Analysis Summary ===")
    print(f"Date range: {start_date} to {end_date}")
    print(f"Total commands: {stats['total_commands']:,}")
    print(f"Total bytes added: {stats['total_bytes_added']:,}")
    print(f"Total bytes removed: {stats['total_bytes_removed']:,}")
    print(f"Net bytes: {stats['total_bytes_added'] - stats['total_bytes_removed']:,}")
    print(f"Total lines added: {stats['total_lines_added']:,}")
    print(f"Total lines removed: {stats['total_lines_removed']:,}")
    print(f"Unique users: {len(stats['by_user'])}")
    print(f"Languages used: {len(stats['by_language'])}")
    print(f"IDEs used: {len(stats['by_ide'])}")
    
    # Save results
    csv_path = save_results_to_csv(stats, start_date, end_date)
    
    if args.output_json:
        json_path = csv_path.replace('_by_user.csv', '_full_analysis.json')
        with open(json_path, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"  - Full analysis JSON: {json_path}")
    
    return 0

if __name__ == "__main__":
    exit(main())
