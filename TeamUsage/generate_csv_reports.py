#!/usr/bin/env python3
"""
STEP 2: Cascade Analytics CSV Report Generator

This script parses the JSON data collected by CascadeLinesPerUser.py and generates 
three structured CSV reports for analysis and visualization.

PREREQUISITE:
Must run CascadeLinesPerUser.py first to generate cascade_analytics_results.json

OUTPUT FILES:
1. daily_user_analytics_YYYYMMDD.csv
   - Unique rows per user/date combination
   - Columns: user_email, date, linesAccepted, linesSuggested, percentage_accepted,
             models (JSON array), messagesSent, promptsUsed

2. aggregated_user_analytics_YYYYMMDD.csv  
   - One row per user with totals across all dates
   - Columns: user_email, total_linesAccepted, total_linesSuggested, 
             total_percentageAccepted, total_messagesSent, total_promptsUsed,
             plus individual columns for each Cascade tool (total_CODE_ACTION, 
             total_VIEW_FILE, total_WORKFLOWS_USED, etc.)

3. model_usage_analytics_YYYYMMDD.csv
   - Unique rows per user/date/model combination
   - Columns: user_email, date, model, messagesSent, promptsUsed

WORKFLOW:
1. Loads cascade_analytics_results.json (created by CascadeLinesPerUser.py)
2. Parses cascade_lines, cascade_runs, and cascade_tool_usage data
3. Aggregates data by user and date for daily report
4. Aggregates data by user across all dates for summary report
5. Aggregates data by user, date, and model for model usage report
6. Exports all reports as timestamped CSV files

The CSV files can be imported into Excel, Tableau, or other analytics tools for 
further analysis and visualization of Cascade usage patterns.
"""

import json
import csv
import os
import pandas as pd
from collections import defaultdict
from datetime import datetime

# Define output directory
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_json_results(filename="cascade_analytics_results.json"):
    """Load the JSON results file."""
    # Check if the file exists in the current directory or in the output directory
    if os.path.exists(filename):
        file_path = filename
    elif os.path.exists(os.path.join(OUTPUT_DIR, filename)):
        file_path = os.path.join(OUTPUT_DIR, filename)
    else:
        raise FileNotFoundError(f"Could not find {filename} in current directory or output directory")
        
    with open(file_path, 'r') as f:
        return json.load(f)

def generate_daily_csv(data, output_file=None):
    """Generate CSV with unique rows per user/date."""
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d")
        output_file = os.path.join(OUTPUT_DIR, f"daily_user_analytics_{timestamp}.csv")
    """
    Generate CSV with unique rows per user/date.
    Columns: user_email, date, linesAccepted, linesSuggested, %percentage accepted, 
             list(DISTINCT(model)), sum(messagesSent), sum(promptsUsed)
    """
    daily_data = []
    
    for email, results in data.items():
        if "error" in results:
            continue
            
        query_results = results.get("queryResults", [])
        
        # Process cascade lines data
        lines_data = {}
        runs_data = {}
        
        for query in query_results:
            if "cascadeLines" in query:
                cascade_lines = query["cascadeLines"].get("cascadeLines", [])
                for entry in cascade_lines:
                    date = entry["day"]
                    if date not in lines_data:
                        lines_data[date] = {"accepted": 0, "suggested": 0}
                    lines_data[date]["accepted"] += int(entry.get("linesAccepted", 0))
                    lines_data[date]["suggested"] += int(entry.get("linesSuggested", 0))
            
            elif "cascadeRuns" in query:
                cascade_runs = query["cascadeRuns"].get("cascadeRuns", [])
                for entry in cascade_runs:
                    date = entry["day"]
                    if date not in runs_data:
                        runs_data[date] = {"models": set(), "messages": 0, "prompts": 0}
                    runs_data[date]["models"].add(entry.get("model", ""))
                    runs_data[date]["messages"] += int(entry.get("messagesSent", 0))
                    runs_data[date]["prompts"] += int(entry.get("promptsUsed", 0))
        
        # Combine data by date
        all_dates = set(lines_data.keys()) | set(runs_data.keys())
        
        for date in all_dates:
            lines_info = lines_data.get(date, {"accepted": 0, "suggested": 0})
            runs_info = runs_data.get(date, {"models": set(), "messages": 0, "prompts": 0})
            
            # Calculate percentage
            suggested = lines_info["suggested"]
            accepted = lines_info["accepted"]
            percentage = (accepted / suggested * 100) if suggested > 0 else 0
            
            # Format models list as JSON array
            models_list = list(runs_info["models"]) if runs_info["models"] else []
            models_str = json.dumps(models_list)
            
            daily_data.append({
                "user_email": email,
                "date": date,
                "linesAccepted": accepted,
                "linesSuggested": suggested,
                "percentage_accepted": round(percentage, 2),
                "models": models_str,
                "messagesSent": runs_info["messages"],
                "promptsUsed": runs_info["prompts"]
            })
    
    # Write to CSV
    if daily_data:
        df = pd.DataFrame(daily_data)
        df = df.sort_values(["user_email", "date"])
        df.to_csv(output_file, index=False)
        print(f"Daily analytics saved to {output_file}")
    else:
        print("No daily data found to export")

def generate_model_usage_csv(data, output_file=None):
    """Generate CSV with model usage data."""
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d")
        output_file = os.path.join(OUTPUT_DIR, f"model_usage_analytics_{timestamp}.csv")
    """
    Generate CSV with unique rows per user/date/model combination.
    Columns: user_email, date, model, messagesSent, promptsUsed
    """
    model_data = []
    
    for email, results in data.items():
        if "error" in results:
            continue
            
        query_results = results.get("queryResults", [])
        
        # Process model usage data from cascade runs
        model_usage = defaultdict(lambda: defaultdict(lambda: {"messages": 0, "prompts": 0}))
        
        for query in query_results:
            if "cascadeRuns" in query:
                cascade_runs = query["cascadeRuns"].get("cascadeRuns", [])
                for entry in cascade_runs:
                    date = entry["day"]
                    model = entry.get("model", "")
                    if model:  # Only process entries with a valid model
                        model_usage[date][model]["messages"] += int(entry.get("messagesSent", 0))
                        model_usage[date][model]["prompts"] += int(entry.get("promptsUsed", 0))
        
        # Create rows for each date/model combination
        for date, models in model_usage.items():
            for model, stats in models.items():
                model_data.append({
                    "user_email": email,
                    "date": date,
                    "model": model,
                    "messagesSent": stats["messages"],
                    "promptsUsed": stats["prompts"]
                })
    
    # Write to CSV
    if model_data:
        df = pd.DataFrame(model_data)
        df = df.sort_values(["user_email", "date", "model"])
        df.to_csv(output_file, index=False)
        print(f"Model usage analytics saved to {output_file}")
    else:
        print("No model usage data found to export")

def generate_aggregated_csv(data, output_file=None):
    """Generate CSV with aggregated data per user."""
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d")
        output_file = os.path.join(OUTPUT_DIR, f"aggregated_user_analytics_{timestamp}.csv")
    """
    Generate CSV with aggregated data per user.
    Columns: user_email, total_linesAccepted, total_linesSuggested, total_percentageAccepted,
             total_messagesSent, total_promptsUsed, and individual tool columns
    """
    aggregated_data = []
    
    for email, results in data.items():
        if "error" in results:
            continue
            
        query_results = results.get("queryResults", [])
        
        # Initialize totals
        totals = {
            "linesAccepted": 0,
            "linesSuggested": 0,
            "messagesSent": 0,
            "promptsUsed": 0,
            "tools": defaultdict(int)
        }
        
        for query in query_results:
            # Process cascade lines
            if "cascadeLines" in query:
                cascade_lines = query["cascadeLines"].get("cascadeLines", [])
                for entry in cascade_lines:
                    totals["linesAccepted"] += int(entry.get("linesAccepted", 0))
                    totals["linesSuggested"] += int(entry.get("linesSuggested", 0))
            
            # Process cascade runs
            elif "cascadeRuns" in query:
                cascade_runs = query["cascadeRuns"].get("cascadeRuns", [])
                for entry in cascade_runs:
                    totals["messagesSent"] += int(entry.get("messagesSent", 0))
                    totals["promptsUsed"] += int(entry.get("promptsUsed", 0))
            
            # Process tool usage
            elif "cascadeToolUsage" in query:
                tool_usage = query["cascadeToolUsage"].get("cascadeToolUsage", [])
                for entry in tool_usage:
                    tool_name = entry.get("tool", "")
                    count = int(entry.get("count", 0))
                    totals["tools"][tool_name] += count
        
        # Calculate percentage
        percentage = (totals["linesAccepted"] / totals["linesSuggested"] * 100) if totals["linesSuggested"] > 0 else 0
        
        # Create row data
        row_data = {
            "user_email": email,
            "total_linesAccepted": totals["linesAccepted"],
            "total_linesSuggested": totals["linesSuggested"],
            "total_percentageAccepted": round(percentage, 2),
            "total_messagesSent": totals["messagesSent"],
            "total_promptsUsed": totals["promptsUsed"]
        }
        
        # Add tool columns
        for tool, count in totals["tools"].items():
            column_name = f"total_{tool}"
            row_data[column_name] = count
        
        aggregated_data.append(row_data)
    
    # Write to CSV
    if aggregated_data:
        df = pd.DataFrame(aggregated_data)
        df = df.fillna(0)  # Fill NaN values with 0 for missing tools
        df = df.sort_values("user_email")
        df.to_csv(output_file, index=False)
        print(f"Aggregated analytics saved to {output_file}")
    else:
        print("No aggregated data found to export")

def main():
    """Main function to generate all CSV reports."""
    print("Loading JSON results...")
    data = load_json_results()
    
    # Generate timestamp for file names
    timestamp = datetime.now().strftime("%Y%m%d")
    
    print("Generating daily user analytics CSV...")
    generate_daily_csv(data, f"daily_user_analytics_{timestamp}.csv")
    
    print("Generating aggregated user analytics CSV...")
    generate_aggregated_csv(data, f"aggregated_user_analytics_{timestamp}.csv")
    
    print("Generating model usage analytics CSV...")
    generate_model_usage_csv(data, f"model_usage_analytics_{timestamp}.csv")
    
    print("CSV generation complete!")

if __name__ == "__main__":
    main()
