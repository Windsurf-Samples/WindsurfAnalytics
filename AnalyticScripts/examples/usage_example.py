#!/usr/bin/env python3
"""
Example script demonstrating how to use the AnalyticScripts package.
"""

import sys
import os
import datetime

# Add parent directory to path so we can import AnalyticScripts
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import functions from the package
from AnalyticScripts import fetch_email_api_mapping, save_emails_to_json, read_api_keys_from_json

def example_fetch_and_save():
    """Example of fetching and saving email-to-API-key mapping"""
    # Get data for the last 7 days
    end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    
    print(f"Fetching email-to-API-key mapping for {start_date} to {end_date}")
    
    # Fetch the data
    email_api_map = fetch_email_api_mapping(start_date, end_date)
    
    if email_api_map:
        # Save to a custom file
        output_file = save_emails_to_json(email_api_map, "recent_users.json")
        print(f"Data saved to {output_file}")
    else:
        print("No data found or an error occurred")

def example_read_existing_file():
    """Example of reading an existing email-to-API-key mapping file"""
    # Check if our example file exists
    if os.path.exists("recent_users.json"):
        # Read the file and invert the mapping
        api_email_map = read_api_keys_from_json("recent_users.json")
        
        # Print a sample of the data
        print("\nSample API key to email mapping:")
        for i, (api_key, email) in enumerate(list(api_email_map.items())[:3]):
            print(f"{i+1}. {api_key[:8]}... -> {email}")
    else:
        print("Example file 'recent_users.json' not found. Run example_fetch_and_save() first.")

if __name__ == "__main__":
    print("Running example_fetch_and_save()...")
    example_fetch_and_save()
    
    print("\nRunning example_read_existing_file()...")
    example_read_existing_file()
