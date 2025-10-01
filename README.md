# WindsurfAnalytics

A comprehensive suite of analytics tools for monitoring Cascade usage, credit consumption, and team productivity across your organization.

## Overview

This repository contains three main components:

### 📊 **TeamUsage** - Team Productivity Analytics
Analyzes team-wide Cascade usage patterns, code suggestions, and productivity metrics.

**What it tracks:**
- Suggested vs. accepted lines of code per user
- Model usage patterns (GPT-4, Claude, etc.)
- Tool usage analytics
- User productivity trends
- Daily and aggregated usage reports

**Key outputs:**
- `daily_user_analytics_YYYYMMDD.csv` - Daily productivity reports
- `aggregated_user_analytics_YYYYMMDD.csv` - Aggregated team metrics
- `model_usage_analytics_YYYYMMDD.csv` - Model usage breakdown

### 💳 **UserCreditMonitoring** - Credit Usage Monitoring
Monitors individual user credit consumption and provides alerts for users approaching their limits.

**What it tracks:**
- Credit usage per user across time periods
- Percentage of credit limits consumed
- Threshold-based alerts (75%, 85%, 95%)
- Credit usage trends and patterns

**Key outputs:**
- `credit_usage_report_YYYY-MM-DD.csv` - Credit monitoring reports
- `cascade_usage_by_user_YYYY-MM-DD.csv` - User credit summaries
- Automated workflow for complete credit monitoring

### 🔍 **FindActiveUsers** - User Activity Analysis
Identifies which users have been active within a specified time period.

**What it tracks:**
- User activity status (active/inactive)
- Last activity date for each user
- Days since last activity

**Key outputs:**
- `user_activity_report_YYYY-MM-DD.json` - Detailed activity report
- Console summary of active and inactive users

### 📚 **AnalyticScripts** - Shared Analytics Library
Centralized library of shared functions used across all analytics modules.

**Key components:**
- `email_api_mapping.py` - Maps user emails to API keys
- `cascade_usage_analyzer.py` - Analyzes Cascade usage data

## Required Setup

### Prerequisites
- Python 3.6+
- Required Python packages (install from requirements.txt):
  ```bash
  pip install -r requirements.txt
  ```

### Service Key Configuration
- **Service Key**: Create at https://windsurf.com/team/settings
  - Go to Service Key Configuration → Configure → Add service key
  - Use Role: admin OR create a custom role with read-only access:
    - https://windsurf.com/team/settings → Role Management → Configure → Create role
    - Grant the new role the "Analytics Read" permissions

### Environment Setup
1. Create a `.env` file in the root directory:
```
SERVICE_KEY=your_key_here
```

2. The `output` directory will be automatically created to store all generated files:
   - All scripts save their output files to this directory by default
   - The directory is git-ignored to prevent accidental commits of data files
   - You can override output locations with command-line arguments if needed

## Support

For detailed usage instructions, see the README files in each folder:
- [TeamUsage README](TeamUsage/README.md)
- [UserCreditMonitoring README](UserCreditMonitoring/README_credit_usage_monitor.md)
- [FindActiveUsers README](FindActiveUsers/README.md)
- [AnalyticScripts README](AnalyticScripts/README.md)

## Contributing

Feel free to modify these scripts to suit your organization's specific needs. Both modules are designed to be extensible and customizable.
