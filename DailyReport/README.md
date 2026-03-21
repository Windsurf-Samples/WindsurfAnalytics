# DailyReport - Combined Activity & Credit Usage Report

Generates a comprehensive daily report combining Cascade usage metrics and credit consumption into a single view per user.

## What It Tracks

### Cascade Usage (via CascadeAnalytics API)
- Lines suggested vs. accepted (with acceptance percentage)
- Messages sent and prompts used
- Model usage breakdown
- Tool usage (CODE_ACTION, VIEW_FILE, WORKFLOWS_USED, etc.)

### Credit Consumption (via Analytics Custom Query API)
- Flex credits used per day
- Prompt credits used per day
- Total prompt count

## Output Files

| File | Description |
|------|-------------|
| `daily_combined_report_YYYY-MM-DD.csv` | Per-user, per-day breakdown with all metrics |
| `daily_combined_summary_YYYY-MM-DD.csv` | Aggregated totals per user across all days |

Both files are saved to the `output/` directory.

## Usage

```bash
# Default: last 30 days, all users
python3 DailyReport/daily_combined_report.py

# Custom date range
python3 DailyReport/daily_combined_report.py --start-date 2025-01-01 --end-date 2025-01-31

# Last 7 days
python3 DailyReport/daily_combined_report.py --days 7

# Single user
python3 DailyReport/daily_combined_report.py --email user@example.com

# Limit to first 10 users
python3 DailyReport/daily_combined_report.py --limit 10

# Custom output file prefix
python3 DailyReport/daily_combined_report.py --output-prefix my_report
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--start-date` | `--days` ago | Start date in YYYY-MM-DD format |
| `--end-date` | Today | End date in YYYY-MM-DD format |
| `--days` | 30 | Days to look back (used when `--start-date` is not set) |
| `--email` | All users | Process only this email address |
| `--limit` | 0 (all) | Max number of users to process |
| `--output-prefix` | `daily_combined` | Prefix for output CSV filenames |

## Prerequisites

- Python 3.6+
- `SERVICE_KEY` configured in `.env` (see root README)
- Dependencies from `requirements.txt` installed

## Console Output

The script prints a team summary after generating reports:

```
============================================================
TEAM SUMMARY
============================================================
Total users:           42
Total lines accepted:  12,345
Total lines suggested: 23,456
Overall acceptance:    52.63%
Total messages sent:   8,901
Total prompts used:    6,789
Total flex credits:    1,234.56
Total prompt credits:  987.65

Top 5 users by prompt credits:
  alice@example.com: 150.25 credits, 234 messages, 1200 lines accepted
  bob@example.com: 120.00 credits, 189 messages, 980 lines accepted
  ...
```
