#!/usr/bin/env python3
"""
Cascade Credit Usage Workflow Orchestrator

This script orchestrates the complete credit usage monitoring workflow by running:
1. get_unique_emails.py - To fetch API keys and emails
2. cascade_usage_analyzer.py - To analyze usage data
3. credit_usage_monitor.py - To identify users approaching credit limits
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime
import re

def parse_arguments():
    parser = argparse.ArgumentParser(description='Orchestrate the complete Cascade credit usage workflow')
    parser.add_argument('--start-date', type=str, help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', type=str, help='End date in YYYY-MM-DD format')
    parser.add_argument('--credit-limit', type=float, default=1500.0, help='Credit limit (default: 1500)')
    parser.add_argument('--thresholds', type=str, default='75,85,95', help='Threshold percentages (default: 75,85,95)')
    parser.add_argument('--output-dir', type=str, default='.', help='Directory for output files')
    parser.add_argument('--skip-emails', action='store_true', help='Skip the email fetching step (use existing unique_emails.json)')
    parser.add_argument('--skip-analysis', action='store_true', help='Skip the usage analysis step (use existing CSV file)')
    parser.add_argument('--emails-file', type=str, help='Path to existing unique_emails.json file (when using --skip-emails)')
    parser.add_argument('--summary-file', type=str, help='Path to existing cascade_usage_by_user_*.csv file (when using --skip-analysis)')
    return parser.parse_args()

def run_command(command, description):
    """Run a command and print its output in real-time"""
    print(f"\n{'=' * 80}")
    print(f"STEP: {description}")
    print(f"{'=' * 80}")
    print(f"Running: {' '.join(command)}")
    
    # Run the command and capture output
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Store the complete output for later analysis
    full_output = []
    
    # Print output in real-time
    for line in iter(process.stdout.readline, ''):
        print(line, end='')
        full_output.append(line)
    
    # Wait for the process to complete
    process.stdout.close()
    return_code = process.wait()
    
    if return_code != 0:
        print(f"Error running {description} (exit code {return_code})")
        sys.exit(return_code)
    
    return ''.join(full_output)

def find_file_in_output(output, pattern):
    """Find a filename in command output using regex pattern"""
    match = re.search(pattern, output)
    if match:
        return match.group(1)
    return None

def find_latest_file(pattern):
    """Find the most recent file matching the given pattern"""
    matching_files = [f for f in os.listdir('.') if re.match(pattern, f)]
    if not matching_files:
        return None
    
    # Sort by modification time (newest first)
    matching_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    return matching_files[0]

def main():
    args = parse_arguments()
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Generate output filenames with timestamps
    timestamp = datetime.now().strftime("%Y-%m-%d")
    emails_json = args.emails_file or os.path.join(args.output_dir, f"unique_emails_{timestamp}.json")
    
    # Step 1: Get unique emails and API keys (unless skipped)
    if not args.skip_emails:
        # Find the path to get_unique_emails.py
        get_emails_script = "../TeamUsage.py/get_unique_emails.py"
        if not os.path.exists(get_emails_script):
            print(f"Warning: Could not find {get_emails_script}")
            get_emails_script = "get_unique_emails.py"
            if not os.path.exists(get_emails_script):
                print(f"Error: Could not find get_unique_emails.py script")
                sys.exit(1)
        
        email_cmd = ["python3", get_emails_script]
        if args.start_date:
            email_cmd.extend(["--start-date", args.start_date])
        if args.end_date:
            email_cmd.extend(["--end-date", args.end_date])
        email_cmd.extend(["--output", emails_json])
        
        run_command(email_cmd, "Fetching unique emails and API keys")
    else:
        print(f"\n{'=' * 80}")
        print(f"STEP: Skipping email fetching (using {emails_json})")
        print(f"{'=' * 80}")
        if not os.path.exists(emails_json):
            print(f"Error: Specified emails file {emails_json} does not exist")
            sys.exit(1)
    
    # Step 2: Analyze usage data (unless skipped)
    summary_file = args.summary_file
    
    if not args.skip_analysis:
        analyzer_cmd = ["python3", "cascade_usage_analyzer.py", "--json-file", emails_json]
        if args.start_date:
            analyzer_cmd.extend(["--start-date", args.start_date])
        if args.end_date:
            analyzer_cmd.extend(["--end-date", args.end_date])
        
        analyzer_output = run_command(analyzer_cmd, "Analyzing usage data")
        
        # Extract the generated summary file from output
        summary_file = find_file_in_output(analyzer_output, r"Summary statistics saved to (cascade_usage_by_user_[^\.]+\.csv)")
        
        if not summary_file:
            # Try to find the latest summary file
            summary_file = find_latest_file(r"cascade_usage_by_user_.*\.csv")
            if summary_file:
                print(f"Found latest summary file: {summary_file}")
            else:
                print("Error: Could not find summary file in analyzer output")
                sys.exit(1)
    else:
        print(f"\n{'=' * 80}")
        print(f"STEP: Skipping usage analysis (using {summary_file})")
        print(f"{'=' * 80}")
        if not summary_file:
            # Try to find the latest summary file
            summary_file = find_latest_file(r"cascade_usage_by_user_.*\.csv")
            if summary_file:
                print(f"Found latest summary file: {summary_file}")
            else:
                print("Error: No summary file specified and could not find any cascade_usage_by_user_*.csv files")
                sys.exit(1)
    
    # Step 3: Monitor credit usage
    monitor_cmd = ["python3", "credit_usage_monitor.py", 
                  "--credit-limit", str(args.credit_limit),
                  "--thresholds", args.thresholds,
                  "--input-file", summary_file]
    
    monitor_output = run_command(monitor_cmd, "Monitoring credit usage")
    
    # Extract the generated report file from output
    report_file = find_file_in_output(monitor_output, r"Report generated: (credit_usage_report_[^\.]+\.csv)")
    
    if not report_file:
        # Try to find the latest report file
        report_file = find_latest_file(r"credit_usage_report_.*\.csv")
        if report_file:
            print(f"Found latest report file: {report_file}")
    
    print("\n" + "=" * 80)
    print("WORKFLOW COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    
    # Print summary of generated files
    print("\nGenerated files:")
    print(f"1. Email-API key mapping: {emails_json}")
    print(f"2. Usage summary: {summary_file}")
    if report_file:
        print(f"3. Credit usage report: {report_file}")
    
    # Print next steps
    print("\nNext steps:")
    print("1. Review the credit usage report")
    print("2. Notify users approaching their limits")
    print("3. Adjust credit limits as needed")

if __name__ == "__main__":
    main()
