# WindsurfAnalytics

A comprehensive suite of analytics tools for monitoring Cascade usage, credit consumption, and team productivity across your organization.

## Overview

This repository contains two main analytics modules:

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

## Required Setup

### Prerequisites
- Python 3.6+
- Required Python packages:
  ```bash
  pip install requests python-dotenv pandas
  ```

### Service Key Configuration
- **Service Key**: Create at https://windsurf.com/team/settings
  - Go to Service Key Configuration → Configure → Add service key
  - Use Role: admin OR create a custom role with read-only access:
    - https://windsurf.com/team/settings → Role Management → Configure → Create role
    - Grant the new role the "Analytics Read" permissions

### Environment Setup
Create a `.env` file in the root directory:
```
SERVICE_KEY=your_key_here
```

## Support

For detailed usage instructions, see the README files in each folder:
- [TeamUsage README](TeamUsage/README.md)
- [UserCreditMonitoring README](UserCreditMonitoring/README_credit_usage_monitor.md)

## Contributing

Feel free to modify these scripts to suit your organization's specific needs. Both modules are designed to be extensible and customizable.
