# Analytics Scripts

This directory contains shared utility scripts used across multiple Windsurf Analytics projects. These scripts provide common functionality for accessing and processing Cascade Analytics data.

## Available Scripts

### `email_api_mapping.py`

**Purpose**: Maps user email addresses to their corresponding API keys by querying the Cascade Analytics API.

**Functions**:

- `fetch_email_api_mapping(start_date=None, end_date=None)`: 
  - Queries the Cascade Analytics API to retrieve user data
  - Extracts unique email addresses and their associated API keys
  - Supports optional date range filtering
  - Returns a dictionary mapping emails to API keys

- `save_emails_to_json(email_api_map, output_file=None)`:
  - Saves the email-to-API-key mapping to a JSON file
  - Automatically generates a filename with the current date if none is provided
  - Returns the path to the saved file

- `read_api_keys_from_json(json_file_path)`:
  - Reads an existing email-to-API-key mapping from a JSON file
  - Returns a dictionary with API keys as keys and emails as values (inverted mapping)

**Usage Example**:

```python
from AnalyticScripts.email_api_mapping import fetch_email_api_mapping, save_emails_to_json

# Fetch email-to-API-key mapping for the last 30 days
email_api_map = fetch_email_api_mapping(start_date="2025-09-01", end_date="2025-09-30")

# Save the mapping to a JSON file
output_file = save_emails_to_json(email_api_map)
print(f"Email-to-API-key mapping saved to {output_file}")
```

### `cascade_usage_analyzer.py`

**Purpose**: Analyzes Cascade API usage data and generates reports on credit consumption.

**Functions**:

- `fetch_usage_data(api_key, start_date, end_date)`: 
  - Queries the Cascade API for usage data for a specific API key
  - Returns raw query results and the complete API response

- `analyze_usage_data(api_key_email_map, start_date, end_date)`:
  - Processes usage data for multiple API keys
  - Calculates total prompts and credits used per user
  - Returns user summary data and raw API responses

- `save_raw_responses(raw_responses, output_file=None)`:
  - Saves raw API responses to a JSON file
  - Useful for further analysis or debugging

- `save_user_summary(user_data, output_file=None)`:
  - Generates a CSV report with usage statistics per user
  - Includes total prompts, flex credits, and prompt credits

- `save_usage_by_model_date(raw_responses, output_file=None)`:
  - Creates a detailed CSV report breaking down usage by model and date
  - Useful for analyzing trends and patterns in model usage

**Usage Example**:

```python
from AnalyticScripts import fetch_email_api_mapping, analyze_usage_data, save_user_summary

# Step 1: Get email-to-API-key mapping
email_api_map = fetch_email_api_mapping(start_date="2025-09-01", end_date="2025-09-30")

# Step 2: Invert the mapping for the analyzer
api_key_email_map = {api_key: email for email, api_key in email_api_map.items()}

# Step 3: Analyze usage data
user_data, raw_responses = analyze_usage_data(api_key_email_map, "2025-09-01", "2025-09-30")

# Step 4: Generate a summary report
summary_file = save_user_summary(user_data)
print(f"Summary saved to {summary_file}")
```

## Best Practices for Using These Scripts

1. **Environment Variables**: Make sure the required environment variables (like `SERVICE_KEY`) are set before using these scripts.

4. **Date Formats**: When providing dates, use the YYYY-MM-DD format (e.g., "2025-09-30").

## Dependencies

- Python 3.6+
- requests
- dotenv
