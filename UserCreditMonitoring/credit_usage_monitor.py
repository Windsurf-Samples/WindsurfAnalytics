#!/usr/bin/env python3
"""
Credit Usage Monitor for Cascade Analytics

This script analyzes user credit usage data from Cascade Analytics and flags users
who are approaching or exceeding defined credit limits.

Features:
- Configurable credit limit (default: 1500)
- Configurable threshold percentages (default: 75%, 85%, 95%)
- Identifies users at each threshold level without double-counting
- Generates detailed CSV reports of flagged users
- Provides summary statistics of credit usage

Usage:
    python3 credit_usage_monitor.py [options]

Options:
    --credit-limit LIMIT    Set the total credit limit (default: 1500)
    --thresholds LIST       Comma-separated list of threshold percentages (default: 75,85,95)
    --input-file FILE       Path to the input CSV file
    --output-file FILE      Path to the output report file
"""

import pandas as pd
import argparse
import os
import sys
import glob
from datetime import datetime

# Define output directory
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Monitor Cascade credit usage and flag high-usage users')
    
    parser.add_argument('--credit-limit', type=float, default=1500.0,
                        help='Total credit limit (default: 1500)')
    parser.add_argument('--thresholds', type=str, default='75,85,95',
                        help='Comma-separated list of threshold percentages (default: 75,85,95)')
    parser.add_argument('--input-file', type=str,
                        help='Path to the input CSV file (default: latest cascade_usage_by_user_*.csv)')
    parser.add_argument('--output-file', type=str,
                        help='Path to the output report file (default: credit_usage_report_YYYY-MM-DD.csv)')
    
    args = parser.parse_args()
    
    # Parse threshold percentages
    try:
        thresholds = [float(t.strip()) for t in args.thresholds.split(',')]
        # Sort thresholds in descending order
        thresholds.sort(reverse=True)
        args.threshold_values = thresholds
    except ValueError:
        print(f"Error: Invalid threshold format. Please use comma-separated numbers (e.g., 75,85,95)")
        sys.exit(1)
    
    return args

def find_latest_usage_file():
    """Find the most recent cascade_usage_by_user_*.csv file."""
    files = glob.glob('cascade_usage_by_user_*.csv')
    if not files:
        return None
    
    # Sort files by modification time (newest first)
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def read_usage_data(file_path):
    """Read and parse the CSV data."""
    try:
        df = pd.read_csv(file_path)
        print(f"Successfully read data from {file_path}")
        print(f"Found {len(df)} user records")
        return df
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def identify_high_credit_usage(df, credit_limit=1500.0, threshold_values=None):
    """
    Identify users at specified threshold percentages of their total credit limit.
    
    Args:
        df: DataFrame with user usage data
        credit_limit: The total credit limit (default: 1500)
        threshold_values: List of threshold percentages (default: [75, 85, 95])
        
    Returns:
        Tuple of (DataFrame of flagged users, Dictionary of threshold counts)
    """
    # Use default thresholds if none provided
    if threshold_values is None:
        threshold_values = [75, 85, 95]
    
    # Define thresholds from highest to lowest
    thresholds = {}
    for value in threshold_values:
        threshold_name = f"{value}%"
        threshold_value = (value / 100) * credit_limit
        thresholds[threshold_name] = threshold_value
    
    # Create a dictionary to track users and their highest threshold
    user_highest_threshold = {}
    threshold_counts = {}
    already_counted_emails = set()  # Track emails that have already been counted at a higher threshold
    
    # Process thresholds from highest to lowest
    for threshold_name, threshold_value in thresholds.items():
        # Filter users who have used at least this threshold of their credit limit
        all_threshold_users = df[df['total_prompt_credits'] >= threshold_value]
        
        # Filter out users who have already been counted at a higher threshold
        new_threshold_users = [user for _, user in all_threshold_users.iterrows() 
                              if user['email'] not in already_counted_emails]
        
        # Update the count for this threshold (only counting users not already counted)
        threshold_counts[threshold_name] = len(new_threshold_users)
        
        print(f"Found {len(new_threshold_users)} users who have reached {threshold_name} of their credit limit (excluding those at higher thresholds)")
        
        # For each new user at this threshold, record this as their threshold
        for user in new_threshold_users:
            email = user['email']
            user_highest_threshold[email] = threshold_name
            already_counted_emails.add(email)  # Mark this email as counted
    
    # If no users found, return empty DataFrame
    if not user_highest_threshold:
        print("No users have reached any credit thresholds")
        return pd.DataFrame(), {}
    
    # Create a list to hold the flagged users with their highest threshold
    flagged_users = []
    
    # For each user, create a record with their highest threshold
    for _, user in df.iterrows():
        email = user['email']
        if email in user_highest_threshold:
            user_data = user.copy()
            user_data['threshold_reached'] = user_highest_threshold[email]
            user_data['percentage'] = (user_data['total_prompt_credits'] / credit_limit) * 100
            flagged_users.append(user_data)
    
    # Convert to DataFrame and sort by percentage
    flagged_df = pd.DataFrame(flagged_users)
    flagged_df = flagged_df.sort_values('percentage', ascending=False)
    
    return flagged_df, threshold_counts

def generate_report(flagged_users, threshold_counts, output_file):
    """
    Generate CSV report of flagged users.
    
    Args:
        flagged_users: DataFrame of users flagged for high credit usage
        threshold_counts: Dictionary with counts of users at each threshold
        output_file: Path to the output report file
    """
    if flagged_users.empty:
        print("No users to report.")
        return
        
    # Select and order columns for the report
    columns = ['api_key', 'email', 'total_prompt_credits', 'percentage', 'threshold_reached']
    
    # Sort by percentage (descending)
    report_df = flagged_users[columns].sort_values('percentage', ascending=False)
    
    # Write to CSV
    report_df.to_csv(output_file, index=False)
    print(f"Report generated: {output_file}")
    
    # Print summary
    print("\nSummary of flagged users:")
    
    # Display threshold counts in descending order (thresholds are already sorted)
    for threshold in sorted(threshold_counts.keys(), key=lambda x: float(x.strip('%')), reverse=True):
        print(f"- {threshold} threshold only: {threshold_counts[threshold]} users")
    
    print(f"- Total flagged users: {len(flagged_users)}")
    
    # Print the top 3 highest usage users
    print("\nTop 3 highest usage users:")
    top_users = flagged_users.nlargest(3, 'percentage')
    for _, user in top_users.iterrows():
        print(f"- {user['email']}: {user['percentage']:.1f}% of limit ({user['total_prompt_credits']:.1f} credits)")


def main():
    """Main execution flow."""
    args = parse_arguments()
    
    # Determine input file
    input_file = args.input_file
    if not input_file:
        input_file = find_latest_usage_file()
        if not input_file:
            print("Error: No input file specified and no cascade_usage_by_user_*.csv files found")
            return
    
    # Determine output file
    output_file = args.output_file
    if not output_file:
        current_date = datetime.now().strftime("%Y-%m-%d")
        output_file = os.path.join(OUTPUT_DIR, f"credit_usage_report_{current_date}.csv")
    
    # Read usage data
    df = read_usage_data(input_file)
    if df is None:
        return
    
    # Identify high usage users
    flagged_users, threshold_counts = identify_high_credit_usage(df, args.credit_limit, args.threshold_values)
    
    # Generate report
    if not flagged_users.empty:
        generate_report(flagged_users, threshold_counts, output_file)
    else:
        print("No users flagged for high credit usage")

if __name__ == "__main__":
    main()
