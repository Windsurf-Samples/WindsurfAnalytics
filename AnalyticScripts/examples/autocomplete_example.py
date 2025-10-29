#!/usr/bin/env python3
"""
Example usage of the Autocomplete Analyzer

This script demonstrates how to use the autocomplete_analyzer module
to retrieve and analyze Windsurf autocomplete/tab acceptance data.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import from AnalyticScripts
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from autocomplete_analyzer import (
    fetch_autocomplete_data,
    analyze_autocomplete_data,
    load_email_api_mapping,
    save_autocomplete_results_to_csv
)

def example_basic_autocomplete_usage():
    """Example: Basic usage - get last 7 days of autocomplete data"""
    print("=== Example 1: Basic Autocomplete Usage ===")
    
    # Get date range (last 7 days)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    print(f"Fetching autocomplete data from {start_date} to {end_date}")
    
    # Fetch the data
    items = fetch_autocomplete_data(start_date, end_date)
    
    if items:
        print(f"Retrieved {len(items)} autocomplete records")
        
        # Load email mapping for better user identification
        email_api_map = load_email_api_mapping()
        
        # Analyze the data
        stats = analyze_autocomplete_data(items, email_api_map)
        
        # Print summary
        print(f"Total acceptances: {stats['total_acceptances']:,}")
        print(f"Total lines accepted: {stats['total_lines_accepted']:,}")
        print(f"Total bytes accepted: {stats['total_bytes_accepted']:,}")
        print(f"Unique users: {len(stats['by_user'])}")
        
        # Save to CSV
        csv_path = save_autocomplete_results_to_csv(stats, start_date, end_date)
        print(f"Results saved to: {csv_path}")
    else:
        print("No autocomplete data found for the specified date range")

def example_hourly_analysis():
    """Example: Analyze autocomplete usage by hour of day"""
    print("\n=== Example 2: Hourly Analysis ===")
    
    # Get date range (last 14 days)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    
    print(f"Analyzing hourly autocomplete patterns from {start_date} to {end_date}")
    
    items = fetch_autocomplete_data(start_date, end_date)
    
    if items:
        email_api_map = load_email_api_mapping()
        stats = analyze_autocomplete_data(items, email_api_map)
        
        print("Autocomplete acceptances by hour (UTC):")
        for hour, hour_stats in sorted(stats['by_hour'].items()):
            if hour != "unknown" and hour_stats['acceptances'] > 0:
                print(f"  {hour}:00 - {hour_stats['acceptances']:,} acceptances, {hour_stats['lines_accepted']:,} lines")

def example_language_autocomplete():
    """Example: Analyze autocomplete usage by programming language"""
    print("\n=== Example 3: Language Autocomplete Analysis ===")
    
    # Get date range (last 30 days)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    print(f"Analyzing autocomplete by language from {start_date} to {end_date}")
    
    items = fetch_autocomplete_data(start_date, end_date)
    
    if items:
        email_api_map = load_email_api_mapping()
        stats = analyze_autocomplete_data(items, email_api_map)
        
        print("Autocomplete acceptances by programming language:")
        for language, lang_stats in sorted(stats['by_language'].items(), 
                                         key=lambda x: x[1]['acceptances'], 
                                         reverse=True):
            if lang_stats['acceptances'] > 0:
                avg_bytes = lang_stats['bytes_accepted'] / lang_stats['acceptances'] if lang_stats['acceptances'] > 0 else 0
                print(f"  {language}: {lang_stats['acceptances']:,} acceptances, {lang_stats['lines_accepted']:,} lines, {avg_bytes:.1f} avg bytes/acceptance")

if __name__ == "__main__":
    print("Autocomplete Analyzer - Usage Examples")
    print("=" * 50)
    
    try:
        example_basic_autocomplete_usage()
        example_hourly_analysis()
        example_language_autocomplete()
        
        print("\n" + "=" * 50)
        print("Examples completed successfully!")
        print("\nTo run the full autocomplete analyzer with custom options, use:")
        print("python autocomplete_analyzer.py --help")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("\nMake sure you have:")
        print("1. Set up your SERVICE_KEY in the .env file")
        print("2. Installed required dependencies (pip install -r requirements.txt)")
        print("3. Have network access to the Windsurf Analytics API")
