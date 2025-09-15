#!/usr/bin/env python3
"""
Email Extraction Script for Cascade Analytics

This script fetches unique email addresses and their associated API keys from the UserPageAnalytics API
to be used with the CascadeLinesPerUser.py script.

By default, it fetches data from the last month, but you can customize the date range
using command-line arguments.
"""

import os
import requests
import json
import datetime
import argparse
from dotenv import load_dotenv
from typing import List, Set, Dict

# Load environment variables from .env file
load_dotenv()

def get_unique_emails(start_timestamp: str, end_timestamp: str) -> Dict[str, str]:
    """
    Get unique emails and their associated API keys from the UserPageAnalytics API.
    
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
        print(f"Fetching user data from {start_timestamp} to {end_timestamp}...")
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

def save_emails_to_file(email_api_map: Dict[str, str], filename: str = "unique_emails.json") -> None:
    """
    Save the unique email:api_key pairs to a JSON file.
    
    Args:
        email_api_map: Dictionary of email addresses to API keys
        filename: Output filename
    """
    with open(filename, "w") as f:
        json.dump(email_api_map, f, indent=2)
    
    print(f"Saved {len(email_api_map)} unique email-API key pairs to {filename}")

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
    parser.add_argument('--output', type=str, default="unique_emails.json",
                        help='Output JSON file name (default: unique_emails.json)')
    args = parser.parse_args()
    
    # Set time range
    now = datetime.datetime.now()
    
    # Process start date
    if args.start_date:
        start_date = parse_date(args.start_date)
    else:
        start_date = get_default_start_date()
    
    # Process end date
    if args.end_date:
        end_date = parse_date(args.end_date)
    else:
        end_date = now
    
    # Convert to ISO format with UTC timezone
    start_timestamp = start_date.strftime("%Y-%m-%dT00:00:00Z")
    end_timestamp = end_date.strftime("%Y-%m-%dT23:59:59Z")
    
    print("Starting unique email and API key extraction...")
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    email_api_map = get_unique_emails(start_timestamp, end_timestamp)
    
    if email_api_map:
        save_emails_to_file(email_api_map, args.output)
        
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
