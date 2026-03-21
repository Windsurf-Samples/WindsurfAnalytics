#!/usr/bin/env python3
"""
Daily Combined Activity & Credit Usage Report

Generates a comprehensive daily report that combines:
- Cascade usage metrics (lines suggested/accepted, messages, prompts, tools)
- Credit consumption (flex credits, prompt credits)
- Per-user, per-day breakdown with totals

WORKFLOW:
1. Fetches email→API key mappings via UserPageAnalytics API
2. Queries CascadeAnalytics API for usage metrics per user
3. Queries Analytics API (Custom Query) for credit consumption per user
4. Merges all data into a single CSV report

OUTPUT FILES:
- daily_combined_report_YYYY-MM-DD.csv  (per-user daily breakdown)
- daily_combined_summary_YYYY-MM-DD.csv (per-user totals)

USAGE:
    python3 daily_combined_report.py
    python3 daily_combined_report.py --start-date 2025-01-01 --end-date 2025-01-31
    python3 daily_combined_report.py --days 7
    python3 daily_combined_report.py --email user@example.com
"""

import os
import sys
import json
import requests
import argparse
import datetime
from collections import defaultdict
from dotenv import load_dotenv

import pandas as pd

# Add parent directory to path to import AnalyticScripts
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Define output directory
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load environment variables from .env file
load_dotenv()


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def get_service_key():
    """Return the SERVICE_KEY or raise if missing."""
    key = os.getenv('SERVICE_KEY')
    if not key:
        raise ValueError("SERVICE_KEY not found in environment variables. "
                         "Please set it in your .env file.")
    return key


def fetch_email_api_mapping(service_key, start_ts, end_ts):
    """
    Call UserPageAnalytics to get email → apiKey mapping.

    Returns:
        dict: {email: api_key, ...}
    """
    url = "https://server.codeium.com/api/v1/UserPageAnalytics"
    payload = {
        "service_key": service_key,
        "start_timestamp": start_ts,
        "end_timestamp": end_ts,
    }
    headers = {"Content-Type": "application/json"}

    print("Fetching email → API key mappings...")
    try:
        resp = requests.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching user page analytics: {e}")
        return {}

    email_api_map = {}
    if "userTableStats" in data and isinstance(data["userTableStats"], list):
        for user in data["userTableStats"]:
            email = user.get("email")
            api_key = user.get("apiKey")
            if email and api_key:
                email_api_map[email] = api_key
    else:
        # Fallback: recursive search
        def _search(obj):
            if isinstance(obj, dict):
                e = obj.get("email")
                k = obj.get("apiKey")
                if e and k and isinstance(e, str) and isinstance(k, str):
                    email_api_map[e] = k
                for v in obj.values():
                    if isinstance(v, (dict, list)):
                        _search(v)
            elif isinstance(obj, list):
                for item in obj:
                    _search(item)
        _search(data)

    print(f"  Found {len(email_api_map)} users")
    return email_api_map


def fetch_cascade_analytics(service_key, email, start_ts, end_ts):
    """
    Call CascadeAnalytics for a single user.

    Returns the raw API response dict.
    """
    url = "https://server.codeium.com/api/v1/CascadeAnalytics"
    payload = {
        "service_key": service_key,
        "start_timestamp": start_ts,
        "end_timestamp": end_ts,
        "emails": [email],
        "query_requests": [
            {"cascade_lines": {}},
            {"cascade_runs": {}},
            {"cascade_tool_usage": {}},
        ],
    }
    headers = {"Content-Type": "application/json"}

    try:
        resp = requests.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching CascadeAnalytics for {email}: {e}")
        return None


def fetch_credit_usage(service_key, api_key, start_date, end_date):
    """
    Call Analytics (Custom Query) for a single API key to get credit usage.

    Returns a list of item dicts.
    """
    url = "https://server.codeium.com/api/v1/Analytics"
    payload = {
        "service_key": service_key,
        "query_requests": [
            {
                "data_source": "QUERY_DATA_SOURCE_CASCADE_DATA",
                "selections": [
                    {"field": "api_key", "name": "api_key"},
                    {"field": "date", "name": "date"},
                    {"field": "prompts_used", "name": "prompts_used"},
                    {"field": "model", "name": "model"},
                    {"field": "ide", "name": "ide"},
                ],
                "filters": [
                    {"name": "date", "filter": "QUERY_FILTER_GE", "value": start_date},
                    {"name": "date", "filter": "QUERY_FILTER_LE", "value": end_date},
                    {"name": "api_key", "filter": "QUERY_FILTER_EQUAL", "value": api_key},
                ],
            }
        ],
    }
    headers = {"Content-Type": "application/json"}

    try:
        resp = requests.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching credit data for key {api_key[:8]}...: {e}")
        return []

    items = []
    if "queryResults" in data and data["queryResults"]:
        for qr in data["queryResults"]:
            if "responseItems" in qr:
                for ri in qr["responseItems"]:
                    if "item" in ri:
                        items.append(ri["item"])
    return items


# ---------------------------------------------------------------------------
# Data parsing helpers
# ---------------------------------------------------------------------------

def normalize_date(date_str):
    """
    Normalize date strings to YYYY-MM-DD format.
    Handles both ISO timestamps (2026-01-25T00:00:00Z) and simple dates (2026-01-25).
    """
    if not date_str:
        return ""
    # If it's an ISO timestamp, extract just the date part
    if "T" in date_str:
        return date_str.split("T")[0]
    # Otherwise return as-is
    return date_str

def parse_cascade_analytics(email, response):
    """
    Parse CascadeAnalytics response into per-day dicts.

    Returns:
        dict: {date_str: {metrics...}, ...}
    """
    if not response or "queryResults" not in response:
        return {}

    lines_by_day = defaultdict(lambda: {"linesAccepted": 0, "linesSuggested": 0})
    runs_by_day = defaultdict(lambda: {"messagesSent": 0, "promptsUsed": 0, "models": set()})
    tools_by_day = defaultdict(lambda: defaultdict(int))

    for query in response.get("queryResults", []):
        if "cascadeLines" in query:
            for entry in query["cascadeLines"].get("cascadeLines", []):
                day = normalize_date(entry.get("day", ""))
                if not day:
                    continue
                lines_by_day[day]["linesAccepted"] += int(entry.get("linesAccepted", 0))
                lines_by_day[day]["linesSuggested"] += int(entry.get("linesSuggested", 0))

        elif "cascadeRuns" in query:
            for entry in query["cascadeRuns"].get("cascadeRuns", []):
                day = normalize_date(entry.get("day", ""))
                if not day:
                    continue
                runs_by_day[day]["messagesSent"] += int(entry.get("messagesSent", 0))
                runs_by_day[day]["promptsUsed"] += int(entry.get("promptsUsed", 0))
                model = entry.get("model", "")
                if model:
                    runs_by_day[day]["models"].add(model)

        elif "cascadeToolUsage" in query:
            for entry in query["cascadeToolUsage"].get("cascadeToolUsage", []):
                day = normalize_date(entry.get("day", ""))
                tool = entry.get("tool", "")
                count = int(entry.get("count", 0))
                if day and tool:
                    tools_by_day[day][tool] += count

    # Merge all days
    all_days = set(lines_by_day.keys()) | set(runs_by_day.keys()) | set(tools_by_day.keys())
    result = {}
    for day in all_days:
        li = lines_by_day[day]
        ru = runs_by_day[day]
        suggested = li["linesSuggested"]
        accepted = li["linesAccepted"]
        pct = round((accepted / suggested * 100), 2) if suggested > 0 else 0.0

        result[day] = {
            "linesAccepted": accepted,
            "linesSuggested": suggested,
            "acceptancePct": pct,
            "messagesSent": ru["messagesSent"],
            "promptsUsed": ru["promptsUsed"],
            "models": sorted(ru["models"]),
            "tools": dict(tools_by_day[day]),
        }

    return result


def parse_credit_items(items):
    """
    Parse Analytics credit items into per-day aggregated dicts.

    Credits are stored as hundredths in the API response, so we divide by 100.

    Returns:
        dict: {date_str: {"promptCredits": float, "totalPrompts": int, "ides": set()}, ...}
    """
    by_day = defaultdict(lambda: {"promptCredits": 0.0, "totalPrompts": 0, "ides": set()})

    for item in items:
        day = normalize_date(item.get("date", ""))
        if not day:
            continue
        by_day[day]["promptCredits"] += float(item.get("prompts_used", 0) or 0) / 100.0
        by_day[day]["totalPrompts"] += 1
        ide = item.get("ide", "")
        if ide:
            by_day[day]["ides"].add(ide)

    return dict(by_day)


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def build_daily_rows(email, cascade_data, credit_data):
    """
    Combine cascade usage + credit data into flat row dicts.

    Returns a list of dicts (one per day).
    """
    all_days = set(cascade_data.keys()) | set(credit_data.keys())
    rows = []

    for day in sorted(all_days):
        cas = cascade_data.get(day, {})
        cred = credit_data.get(day, {})

        # Collect all tool counts as individual columns
        tool_counts = cas.get("tools", {})

        row = {
            "user_email": email,
            "date": day,
            # Cascade usage
            "linesAccepted": cas.get("linesAccepted", 0),
            "linesSuggested": cas.get("linesSuggested", 0),
            "acceptancePct": cas.get("acceptancePct", 0.0),
            "messagesSent": cas.get("messagesSent", 0),
            "promptsUsed": cas.get("promptsUsed", 0),
            "models": json.dumps(cas.get("models", [])),
            # Credit usage
            "promptCredits": round(cred.get("promptCredits", 0.0), 2),
            "creditPromptCount": cred.get("totalPrompts", 0),
            "ides": json.dumps(sorted(cred.get("ides", set()))),
        }

        # Add tool columns
        for tool_name, count in tool_counts.items():
            row[f"tool_{tool_name}"] = count

        rows.append(row)

    return rows


def build_summary_rows(email, daily_rows):
    """
    Aggregate daily rows into a single summary row per user.
    """
    if not daily_rows:
        return None

    total = {
        "user_email": email,
        "days_active": len(daily_rows),
        "total_linesAccepted": 0,
        "total_linesSuggested": 0,
        "total_messagesSent": 0,
        "total_promptsUsed": 0,
        "total_promptCredits": 0.0,
        "total_creditPromptCount": 0,
    }

    all_models = set()
    all_ides = set()
    tool_totals = defaultdict(int)

    for row in daily_rows:
        total["total_linesAccepted"] += row["linesAccepted"]
        total["total_linesSuggested"] += row["linesSuggested"]
        total["total_messagesSent"] += row["messagesSent"]
        total["total_promptsUsed"] += row["promptsUsed"]
        total["total_promptCredits"] += row["promptCredits"]
        total["total_creditPromptCount"] += row["creditPromptCount"]

        for m in json.loads(row["models"]):
            all_models.add(m)
        
        for ide in json.loads(row["ides"]):
            all_ides.add(ide)

        for k, v in row.items():
            if k.startswith("tool_"):
                tool_totals[k] += v

    suggested = total["total_linesSuggested"]
    accepted = total["total_linesAccepted"]
    total["total_acceptancePct"] = round((accepted / suggested * 100), 2) if suggested > 0 else 0.0
    total["total_promptCredits"] = round(total["total_promptCredits"], 2)
    total["models_used"] = json.dumps(sorted(all_models))
    total["ides_used"] = json.dumps(sorted(all_ides))

    # Add tool totals
    for k, v in tool_totals.items():
        total[f"total_{k}"] = v

    return total


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a combined daily Cascade activity & credit usage report"
    )
    parser.add_argument(
        "--start-date", type=str,
        help="Start date YYYY-MM-DD (default: --days ago)"
    )
    parser.add_argument(
        "--end-date", type=str,
        help="End date YYYY-MM-DD (default: today)"
    )
    parser.add_argument(
        "--days", type=int, default=30,
        help="Number of days to look back if --start-date is not set (default: 30)"
    )
    parser.add_argument(
        "--email", type=str,
        help="Process only this single email address"
    )
    parser.add_argument(
        "--limit", type=int, default=0,
        help="Limit the number of users to process (0 = all)"
    )
    parser.add_argument(
        "--output-prefix", type=str,
        help="Override output file prefix (default: daily_combined)"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    service_key = get_service_key()

    # Resolve date range
    now = datetime.datetime.now()

    if args.end_date:
        end_date = datetime.datetime.strptime(args.end_date, "%Y-%m-%d")
    else:
        end_date = now

    if args.start_date:
        start_date = datetime.datetime.strptime(args.start_date, "%Y-%m-%d")
    else:
        start_date = end_date - datetime.timedelta(days=args.days)

    start_ts = start_date.strftime("%Y-%m-%dT00:00:00Z")
    end_ts = end_date.strftime("%Y-%m-%dT23:59:59Z")
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    print(f"Date range: {start_date_str} to {end_date_str}")

    # Step 1: Get email → API key mapping
    email_api_map = fetch_email_api_mapping(service_key, start_ts, end_ts)
    if not email_api_map:
        print("No users found. Exiting.")
        return

    # Filter to single email if requested
    if args.email:
        if args.email in email_api_map:
            email_api_map = {args.email: email_api_map[args.email]}
            print(f"Filtering to single user: {args.email}")
        else:
            print(f"Warning: {args.email} not found in user list. Processing all users.")

    # Apply limit
    emails = list(email_api_map.keys())
    if args.limit > 0 and args.limit < len(emails):
        emails = emails[:args.limit]
        print(f"Limiting to first {args.limit} users")

    # Step 2 & 3: Fetch data for each user
    all_daily_rows = []
    all_summary_rows = []

    for i, email in enumerate(emails, 1):
        api_key = email_api_map[email]
        print(f"[{i}/{len(emails)}] Processing {email}...")

        # Cascade usage metrics
        cascade_resp = fetch_cascade_analytics(service_key, email, start_ts, end_ts)
        cascade_data = parse_cascade_analytics(email, cascade_resp) if cascade_resp else {}

        # Credit consumption
        credit_items = fetch_credit_usage(service_key, api_key, start_date_str, end_date_str)
        credit_data = parse_credit_items(credit_items)

        # Build rows
        daily_rows = build_daily_rows(email, cascade_data, credit_data)
        all_daily_rows.extend(daily_rows)

        summary_row = build_summary_rows(email, daily_rows)
        if summary_row:
            all_summary_rows.append(summary_row)

    # Step 4: Write reports
    prefix = args.output_prefix or "daily_combined"
    timestamp = now.strftime("%Y-%m-%d")

    if all_daily_rows:
        daily_df = pd.DataFrame(all_daily_rows)
        daily_df = daily_df.fillna(0)
        daily_df = daily_df.sort_values(["user_email", "date"])
        daily_file = os.path.join(OUTPUT_DIR, f"{prefix}_report_{timestamp}.csv")
        daily_df.to_csv(daily_file, index=False)
        print(f"\nDaily report saved to {daily_file}")
        print(f"  {len(daily_df)} rows across {daily_df['user_email'].nunique()} users")
    else:
        print("\nNo daily data collected.")

    if all_summary_rows:
        summary_df = pd.DataFrame(all_summary_rows)
        summary_df = summary_df.fillna(0)
        summary_df = summary_df.sort_values("user_email")
        summary_file = os.path.join(OUTPUT_DIR, f"{prefix}_summary_{timestamp}.csv")
        summary_df.to_csv(summary_file, index=False)
        print(f"Summary report saved to {summary_file}")
        print(f"  {len(summary_df)} users")

        # Console summary
        print(f"\n{'='*60}")
        print("TEAM SUMMARY")
        print(f"{'='*60}")
        print(f"Total users:           {len(summary_df)}")
        print(f"Total lines accepted:  {summary_df['total_linesAccepted'].sum():,.0f}")
        print(f"Total lines suggested: {summary_df['total_linesSuggested'].sum():,.0f}")
        total_suggested = summary_df['total_linesSuggested'].sum()
        total_accepted = summary_df['total_linesAccepted'].sum()
        overall_pct = round((total_accepted / total_suggested * 100), 2) if total_suggested > 0 else 0
        print(f"Overall acceptance:    {overall_pct}%")
        print(f"Total messages sent:   {summary_df['total_messagesSent'].sum():,.0f}")
        print(f"Total prompts used:    {summary_df['total_promptsUsed'].sum():,.0f}")
        print(f"Total prompt credits:  {summary_df['total_promptCredits'].sum():,.2f}")

        # Top 5 users by prompt credits
        print(f"\nTop 5 users by prompt credits:")
        top = summary_df.nlargest(5, "total_promptCredits")
        for _, row in top.iterrows():
            print(f"  {row['user_email']}: {row['total_promptCredits']:.2f} credits, "
                  f"{row['total_messagesSent']:.0f} messages, "
                  f"{row['total_linesAccepted']:.0f} lines accepted")
    else:
        print("No summary data collected.")

    print("\nDone!")


if __name__ == "__main__":
    main()
