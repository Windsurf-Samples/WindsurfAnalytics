import os
import json
import requests
import csv
import argparse
import datetime
from collections import defaultdict
from dotenv import load_dotenv

# Define output directory
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load environment variables from .env file
load_dotenv()

# Get service key from environment
SERVICE_KEY = os.getenv("SERVICE_KEY")

# Validate service key
if not SERVICE_KEY:
    raise ValueError("SERVICE_KEY not found in .env file")

# API configuration
API_URL = "https://server.codeium.com/api/v1/Analytics"

# Helper functions for date handling
def get_current_week_sunday():
    """Get the date of the Sunday of the current week"""
    now = datetime.datetime.now()
    # Get the current weekday (0 is Monday in Python's datetime)
    weekday = now.weekday()
    # Calculate days to go back to reach Sunday (which is 6 in Python's datetime)
    # If today is Sunday (weekday 6), days_to_subtract will be 0
    # If today is Monday (weekday 0), days_to_subtract will be 1
    # If today is Tuesday (weekday 1), days_to_subtract will be 2, etc.
    days_to_subtract = (weekday + 1) % 7
    # Get the date for Sunday
    sunday = now - datetime.timedelta(days=days_to_subtract)
    return sunday.strftime("%Y-%m-%d")

def get_default_start_date():
    """Get default start date (Sunday of the current week)"""
    return get_current_week_sunday()

def get_default_end_date():
    """Get default end date (today)"""
    return datetime.datetime.now().strftime("%Y-%m-%d")

def parse_date(date_str):
    """Parse date string in YYYY-MM-DD format"""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Please use YYYY-MM-DD format.")

def find_latest_email_mapping_file():
    """Find the latest email_api_mapping file in the output directory"""
    import glob
    pattern = os.path.join(OUTPUT_DIR, 'email_api_mapping_*.json')
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort by filename (which includes date) and return the latest
    return sorted(files)[-1]

# Read API keys and emails from JSON file
def read_api_keys_from_json(json_file_path):
    """
    Read API keys and emails from JSON file produced by get_unique_emails.py
    
    Args:
        json_file_path: Path to JSON file containing email:api_key pairs
        
    Returns:
        Dictionary mapping API keys to emails
    """
    api_key_email_map = {}
    
    try:
        print(f"Reading JSON file: {json_file_path}")
        with open(json_file_path, 'r') as json_file:
            # The JSON from get_unique_emails.py has email as key and api_key as value
            # We need to invert this for our use case
            email_api_map = json.load(json_file)
            api_key_email_map = {api_key: email for email, api_key in email_api_map.items()}
            print(f"Loaded {len(api_key_email_map)} API keys from JSON file")
    except Exception as e:
        print(f"Error reading JSON file: {e}")
    
    if not api_key_email_map:
        print("Warning: No API keys found in the JSON file. Please check the file format.")
    
    return api_key_email_map

def create_payload(api_key, start_date, end_date):
    """Create request payload for a specific API key with date range"""
    return {
        "service_key": SERVICE_KEY,
        "query_requests": [
            {
                "data_source": "QUERY_DATA_SOURCE_CASCADE_DATA",
                "selections": [
                    {"field": "api_key", "name": "api_key"},
                    {"field": "date", "name": "date"},
                    {"field": "prompts_used", "name": "prompts_used"},
                    {"field": "flex_credits_used", "name": "flex_credits_used"},
                    {"field": "model", "name": "model"},
                    {"field": "metadata", "name": "metadata"}
                ],
                "filters": [
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
                    {
                        "name": "api_key",
                        "filter": "QUERY_FILTER_EQUAL",
                        "value": api_key
                    }
                ]
            }
        ]
    }

def fetch_data_for_api_key(api_key, headers, start_date, end_date):
    """Fetch data for a single API key with date range"""
    print(f"Fetching data for API key: {api_key[:8]}...")
    
    payload = create_payload(api_key, start_date, end_date)
    
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
        
        print(f"Found {len(items)} items for API key {api_key[:8]}...")
        return items, data
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for API key {api_key[:8]}...: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            try:
                error_data = e.response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Response text: {e.response.text}")
        return [], None

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Fetch and analyze Cascade API usage data')
    parser.add_argument('--start-date', type=str, default=get_default_start_date(),
                        help='Start date in YYYY-MM-DD format (default: Sunday of current week)')
    parser.add_argument('--end-date', type=str, default=get_default_end_date(),
                        help='End date in YYYY-MM-DD format (default: today)')
    parser.add_argument('--json-file', type=str, default=None,
                        help='JSON file with email:api_key pairs (default: latest email_api_mapping file in output dir)')
    args = parser.parse_args()
    
    # Validate and parse dates
    try:
        start_date = parse_date(args.start_date)
        end_date = parse_date(args.end_date)
        print(f"Date range: {start_date} to {end_date}")
    except ValueError as e:
        print(f"Error: {e}")
        return
    
    # Determine JSON file to use
    json_file = args.json_file
    if not json_file:
        json_file = find_latest_email_mapping_file()
        if not json_file:
            print("Error: No email_api_mapping_*.json files found in output directory")
            return
        print(f"Using latest email mapping file: {json_file}")
    
    # Load API keys and emails from JSON
    API_KEY_EMAIL_MAP = read_api_keys_from_json(json_file)
    API_KEYS = list(API_KEY_EMAIL_MAP.keys())
    
    if not API_KEYS:
        print("Warning: No API keys found in the JSON file. Please check the file format.")
        return
    
    # Set headers
    headers = {"Content-Type": "application/json"}
    
    # Dictionary to aggregate data from all API keys
    aggregated_data = {}
    all_responses = {}
    total_items = 0
    
    print(f"Processing {len(API_KEYS)} API keys...")
    
    # Iterate through each API key
    for api_key in API_KEYS:
        items, response_data = fetch_data_for_api_key(api_key, headers, start_date, end_date)
        
        if response_data:
            all_responses[api_key] = response_data
        
        total_items += len(items)
        
        # Process each item and aggregate data
        for item in items:
            api_key_from_item = item.get("api_key", "")
            date = item.get("date", "")
            model = item.get("model", "unknown")
            email = API_KEY_EMAIL_MAP.get(api_key_from_item, "")
            
            # If model is None or empty, set it to "unknown"
            if not model:
                model = "unknown"
                
            flex_credits = float(item.get("flex_credits_used", 0) or 0)
            prompts_used = float(item.get("prompts_used", 0) or 0)
            
            # Create a unique key for aggregation
            key = (api_key_from_item, date, model)
            
            # Update aggregated data
            if key in aggregated_data:
                aggregated_data[key]["sum_flex_credits"] += flex_credits
                aggregated_data[key]["sum_prompt_credits"] += prompts_used
                aggregated_data[key]["total_prompts_sent"] += 1
            else:
                aggregated_data[key] = {
                    "api_key": api_key_from_item,
                    "email": email,
                    "date": date,
                    "model": model,
                    "sum_flex_credits": flex_credits,
                    "sum_prompt_credits": prompts_used,
                    "total_prompts_sent": 1
                }
    
    print(f"\nTotal items processed: {total_items}")
    print(f"Unique aggregated entries: {len(aggregated_data)}")
    
    # Get current date for filenames
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Save all responses to file
    json_filename = os.path.join(OUTPUT_DIR, f"cascade_api_raw_responses_{current_date}.json")
    with open(json_filename, "w") as f:
        json.dump(all_responses, f, indent=2)
    print(f"All responses saved to {json_filename}")
    
    # Output to CSV
    csv_filename = os.path.join(OUTPUT_DIR, f"cascade_usage_by_model_date_{current_date}.csv")
    
    # Divide sum_prompt_credits and sum_flex_credits by 100 before writing to CSV
    for key in aggregated_data:
        aggregated_data[key]["sum_flex_credits"] /= 100
        aggregated_data[key]["sum_prompt_credits"] /= 100
        
    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['api_key', 'email', 'date', 'model', 'sum_flex_credits', 'sum_prompt_credits', 'total_prompts_sent']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for data in aggregated_data.values():
            writer.writerow(data)
            
    print(f"Aggregated data saved to {csv_filename}")
    
    # Generate summary statistics
    print(f"\nGenerating summary statistics...")
    api_key_stats = defaultdict(lambda: {"total_prompts": 0, "total_flex_credits": 0, "total_prompt_credits": 0, "email": ""})
    
    for data in aggregated_data.values():
        api_key = data['api_key']
        api_key_stats[api_key]["total_prompts"] += data['total_prompts_sent']
        api_key_stats[api_key]["total_flex_credits"] += data['sum_flex_credits']
        api_key_stats[api_key]["total_prompt_credits"] += data['sum_prompt_credits']
        api_key_stats[api_key]["email"] = data['email']
    
    # Create a summary CSV file
    summary_csv_filename = os.path.join(OUTPUT_DIR, f"cascade_usage_by_user_{current_date}.csv")
    with open(summary_csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['api_key', 'email', 'total_prompts', 'total_flex_credits', 'total_prompt_credits']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for api_key, stats in api_key_stats.items():
            writer.writerow({
                'api_key': api_key,
                'email': stats['email'],
                'total_prompts': stats['total_prompts'],
                'total_flex_credits': round(stats['total_flex_credits'], 2),
                'total_prompt_credits': round(stats['total_prompt_credits'], 2)
            })
    
    print(f"Summary statistics saved to {summary_csv_filename}")
    
if __name__ == "__main__":
    main()