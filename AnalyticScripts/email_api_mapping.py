#!/usr/bin/env python3
"""
Email API Mapping Module for Cascade Analytics

This module provides functions for retrieving, saving, and reading email-to-API-key mappings
from the Cascade Analytics API. These mappings can be used across multiple Windsurf Analytics projects.

By default, it fetches data from the last month, but you can customize the date range
using command-line arguments.

Typical usage:
    - As a standalone script: python email_api_mapping.py --output my_emails.json
    - As an imported module: from AnalyticScripts.email_api_mapping import fetch_email_api_mapping

Requires:
    - SERVICE_KEY environment variable to be set (typically in .env file)
    - Python 3.6+ with requests and python-dotenv packages
"""

import os
import requests
import json
import datetime
import argparse
from dotenv import load_dotenv
from typing import List, Set, Dict

# Define output directory
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load environment variables from .env file
load_dotenv()

def fetch_email_api_mapping(start_date=None, end_date=None) -> Dict[str, str]:
    """
    Get unique emails and their associated API keys from the Cascade Analytics API.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (e.g., "2025-01-01") or None for 30 days ago
        end_date: End date in YYYY-MM-DD format (e.g., "2025-01-31") or None for today
    
    Returns:
        Dictionary of unique email addresses as keys and API keys as values
    
    Raises:
        ValueError: If SERVICE_KEY is not found or date format is invalid
        requests.exceptions.RequestException: If the API request fails
    """
    # Process dates
    now = datetime.datetime.now()
    
    if start_date:
        start_date = parse_date(start_date)
    else:
        start_date = now - datetime.timedelta(days=30)
        
    if end_date:
        end_date = parse_date(end_date)
    else:
        end_date = now
        
    # Convert to ISO format with UTC timezone
    start_timestamp = start_date.strftime("%Y-%m-%dT00:00:00Z")
    end_timestamp = end_date.strftime("%Y-%m-%dT23:59:59Z")
    
    print(f"Fetching user data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
    
    return _query_analytics_api(start_timestamp, end_timestamp)

def _query_analytics_api(start_timestamp: str, end_timestamp: str) -> Dict[str, str]:
    """
    Internal function to query the UserPageAnalytics API for email-API key mappings.
    
    Args:
        start_timestamp: Start time in ISO format (e.g., "2025-01-01T00:00:00Z")
        end_timestamp: End time in ISO format (e.g., "2025-01-02T00:00:00Z")
    
    Returns:
        Dictionary of unique email addresses as keys and API keys as values
    """
    service_key = os.getenv('SERVICE_KEY')
    if not service_key:
        raise ValueError("SERVICE_KEY not found in environment variables")
    
    url = "https://server.codeium.com/api/v1/UserPageAnalytics"
    
    payload = {
        "service_key": service_key,
        "start_timestamp": start_timestamp,
        "end_timestamp": end_timestamp
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Querying API for data from {start_timestamp} to {end_timestamp}...")
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Extract unique email:api_key pairs from the response
        email_api_map = {}
        
        # Based on the API response structure, we know emails and API keys are in userTableStats
        if "userTableStats" in data and isinstance(data["userTableStats"], list):
            for user in data["userTableStats"]:
                if "email" in user and user["email"] and "apiKey" in user and user["apiKey"]:
                    email_api_map[user["email"]] = user["apiKey"]
        else:
            def search_for_email_api_pairs(obj):
                if isinstance(obj, dict):
                    # Check if this object has both email and apiKey
                    email = obj.get("email")
                    api_key = obj.get("apiKey")
                    if email and api_key and isinstance(email, str) and isinstance(api_key, str):
                        email_api_map[email] = api_key
                    
                    # Continue searching in nested objects
                    for value in obj.values():
                        if isinstance(value, (dict, list)):
                            search_for_email_api_pairs(value)
                elif isinstance(obj, list):
                    for item in obj:
                        search_for_email_api_pairs(item)
            
            search_for_email_api_pairs(data)
        
        print(f"\nFound {len(email_api_map)} unique email-API key pairs")
        return email_api_map
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return {}

def save_emails_to_json(email_api_map: Dict[str, str], output_file: str = None) -> str:
    """
    Save the unique email:api_key pairs to a JSON file.
    
    Args:
        email_api_map: Dictionary of email addresses to API keys
        output_file: Output filename (if None, generates a name with current date)
    
    Returns:
        Path to the saved file
    
    Raises:
        IOError: If the file cannot be written
    """
    if output_file is None:
        # Generate filename with current date
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        output_file = os.path.join(OUTPUT_DIR, f"email_api_mapping_{current_date}.json")
        
    with open(output_file, "w") as f:
        json.dump(email_api_map, f, indent=2)
    
    print(f"Saved {len(email_api_map)} unique email-API key pairs to {output_file}")
    return output_file

def parse_date(date_str: str) -> datetime.datetime:
    """
    Parse a date string in YYYY-MM-DD format.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        datetime object
    """
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Please use YYYY-MM-DD format.")

def get_default_start_date() -> datetime.datetime:
    """
    Get the default start date (1 month ago).
    
    Returns:
        datetime object representing 1 month ago
    """
    now = datetime.datetime.now()
    # Go back 1 month (approximately 30 days)
    return now - datetime.timedelta(days=30)

def read_api_keys_from_json(json_file_path: str) -> Dict[str, str]:
    """
    Read API keys and emails from JSON file.
    
    Args:
        json_file_path: Path to JSON file containing email:api_key pairs
        
    Returns:
        Dictionary mapping API keys to emails (inverted from the file format)
    
    Raises:
        FileNotFoundError: If the file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    api_key_email_map = {}
    
    try:
        print(f"Reading JSON file: {json_file_path}")
        with open(json_file_path, 'r') as json_file:
            # The JSON has email as key and api_key as value
            # We invert this for some use cases
            email_api_map = json.load(json_file)
            api_key_email_map = {api_key: email for email, api_key in email_api_map.items()}
            print(f"Loaded {len(api_key_email_map)} API keys from JSON file")
    except Exception as e:
        print(f"Error reading JSON file: {e}")
    
    return api_key_email_map

def main():
    """
    Main function to fetch and save unique email:api_key pairs.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Extract unique email addresses and API keys from Cascade Analytics API')
    parser.add_argument('--start-date', type=str, 
                        help='Start date in YYYY-MM-DD format (default: 1 month ago)')
    parser.add_argument('--end-date', type=str, 
                        help='End date in YYYY-MM-DD format (default: today)')
    parser.add_argument('--output', type=str,
                        help='Output JSON file name (default: email_api_mapping_YYYY-MM-DD.json)')
    args = parser.parse_args()
    
    print("Starting email-to-API-key mapping extraction...")
    
    # Fetch email-to-API-key mapping
    email_api_map = fetch_email_api_mapping(args.start_date, args.end_date)
    
    if email_api_map:
        output_file = save_emails_to_json(email_api_map, args.output)
        
        # Print sample of email:api_key pairs (up to 5)
        sample_items = list(email_api_map.items())[:5]
        print("\nSample email-API key pairs:")
        for email, api_key in sample_items:
            print(f"- {email}: {api_key[:8]}...")  # Show only first 8 chars of API key for security
        
        if len(email_api_map) > 5:
            print(f"... and {len(email_api_map) - 5} more")
    else:
        print("No email-API key pairs found or an error occurred")

if __name__ == "__main__":
    main()
