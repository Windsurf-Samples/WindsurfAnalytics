#!/usr/bin/env python3
"""
Example usage of the Command Bytes Analyzer

This script demonstrates how to use the command_bytes_analyzer module
to retrieve and analyze Windsurf command bytes data.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import from AnalyticScripts
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from command_bytes_analyzer import (
    fetch_command_bytes_data,
    analyze_command_bytes,
    load_email_api_mapping,
    save_results_to_csv
)

def example_basic_usage():
    """Example: Basic usage - get last 7 days of command bytes data"""
    print("=== Example 1: Basic Usage ===")
    
    # Get date range (last 7 days)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    print(f"Fetching command bytes data from {start_date} to {end_date}")
    
    # Fetch the data
    items = fetch_command_bytes_data(start_date, end_date)
    
    if items:
        print(f"Retrieved {len(items)} command records")
        
        # Load email mapping for better user identification
        email_api_map = load_email_api_mapping()
        
        # Analyze the data
        stats = analyze_command_bytes(items, email_api_map)
        
        # Print summary
        print(f"Total bytes added: {stats['total_bytes_added']:,}")
        print(f"Total commands: {stats['total_commands']:,}")
        print(f"Unique users: {len(stats['by_user'])}")
        
        # Save to CSV
        csv_path = save_results_to_csv(stats, start_date, end_date)
        print(f"Results saved to: {csv_path}")
    else:
        print("No data found for the specified date range")

def example_specific_users():
    """Example: Analyze specific users by API key"""
    print("\n=== Example 2: Specific Users ===")
    
    # You would replace these with actual API keys from your team
    specific_api_keys = [
        # "your_api_key_1_here",
        # "your_api_key_2_here"
    ]
    
    if not specific_api_keys:
        print("No specific API keys configured. Skipping this example.")
        print("To use this example, add actual API keys to the specific_api_keys list.")
        return
    
    # Get date range (last 30 days)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    print(f"Analyzing {len(specific_api_keys)} specific users from {start_date} to {end_date}")
    
    # Fetch data for specific users
    items = fetch_command_bytes_data(start_date, end_date, specific_api_keys)
    
    if items:
        email_api_map = load_email_api_mapping()
        stats = analyze_command_bytes(items, email_api_map)
        
        print(f"Results for {len(specific_api_keys)} users:")
        for user, user_stats in stats['by_user'].items():
            print(f"  {user}: {user_stats['bytes_added']:,} bytes added in {user_stats['commands']} commands")

def example_language_analysis():
    """Example: Analyze bytes added by programming language"""
    print("\n=== Example 3: Language Analysis ===")
    
    # Get date range (last 14 days)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    
    print(f"Analyzing language usage from {start_date} to {end_date}")
    
    items = fetch_command_bytes_data(start_date, end_date)
    
    if items:
        email_api_map = load_email_api_mapping()
        stats = analyze_command_bytes(items, email_api_map)
        
        print("Bytes added by programming language:")
        for language, lang_stats in sorted(stats['by_language'].items(), 
                                         key=lambda x: x[1]['bytes_added'], 
                                         reverse=True):
            print(f"  {language}: {lang_stats['bytes_added']:,} bytes ({lang_stats['commands']} commands)")

if __name__ == "__main__":
    print("Command Bytes Analyzer - Usage Examples")
    print("=" * 50)
    
    try:
        example_basic_usage()
        example_specific_users()
        example_language_analysis()
        
        print("\n" + "=" * 50)
        print("Examples completed successfully!")
        print("\nTo run the full analyzer with custom options, use:")
        print("python command_bytes_analyzer.py --help")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("\nMake sure you have:")
        print("1. Set up your SERVICE_KEY in the .env file")
        print("2. Installed required dependencies (pip install -r requirements.txt)")
        print("3. Have network access to the Windsurf Analytics API")
