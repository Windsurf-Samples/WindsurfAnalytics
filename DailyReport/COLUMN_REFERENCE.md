# Daily Combined Report - Column Reference

This document defines all columns in the generated CSV reports and their data sources.

---

## Output Files

### 1. `daily_combined_report_YYYY-MM-DD.csv`
Per-user, per-day breakdown with all metrics.

### 2. `daily_combined_summary_YYYY-MM-DD.csv`
Aggregated totals per user across the entire date range.

---

## Column Definitions - Daily Report

| Column | Data Source | API Endpoint | Description | Example Value |
|--------|-------------|--------------|-------------|---------------|
| **user_email** | UserPageAnalytics | `/UserPageAnalytics` | User's email address | `alice@example.com` |
| **date** | Both APIs | Both | Date in YYYY-MM-DD format | `2026-01-25` |
| **linesAccepted** | CascadeAnalytics | `/CascadeAnalytics` | Number of AI-suggested code lines that the user accepted | `177` |
| **linesSuggested** | CascadeAnalytics | `/CascadeAnalytics` | Total number of code lines suggested by AI | `563` |
| **acceptancePct** | Calculated | N/A | Percentage of suggested lines that were accepted (linesAccepted / linesSuggested × 100) | `31.44` |
| **messagesSent** | CascadeAnalytics | `/CascadeAnalytics` | Number of chat messages sent to Cascade | `7` |
| **promptsUsed** | CascadeAnalytics | `/CascadeAnalytics` | Total number of prompts/requests made to Cascade | `2100` |
| **models** | CascadeAnalytics | `/CascadeAnalytics` | JSON array of AI models used that day | `["Claude Sonnet 4.5"]` |
| **promptCredits** | Analytics (Custom Query) | `/Analytics` | Prompt credits consumed (in credits, not hundredths) | `21.0` |
| **creditPromptCount** | Analytics (Custom Query) | `/Analytics` | Number of data points from credit API (internal metric) | `7` |
| **ides** | Analytics (Custom Query) | `/Analytics` | JSON array of IDEs/editors used that day | `["vscode", "jetbrains"]` |
| **tool_[TOOL_NAME]** | CascadeAnalytics | `/CascadeAnalytics` | Count of specific tool usage (dynamic columns) | `5` |

### Dynamic Tool Columns

Tool usage columns are created dynamically based on actual tool usage. Common tools include:

- `tool_CODE_ACTION` - Code editing actions
- `tool_VIEW_FILE` - File viewing operations
- `tool_GREP_SEARCH` - Search operations
- `tool_RUN_COMMAND` - Terminal commands executed
- `tool_EDIT` - File edit operations
- `tool_MULTI_EDIT` - Multi-file edit operations
- `tool_WRITE_TO_FILE` - New file creation

---

## Column Definitions - Summary Report

| Column | Source | Description | Example Value |
|--------|--------|-------------|---------------|
| **user_email** | UserPageAnalytics | User's email address | `alice@example.com` |
| **days_active** | Calculated | Number of days with any activity in the date range | `42` |
| **total_linesAccepted** | Sum of daily values | Total lines of code accepted across all days | `12,345` |
| **total_linesSuggested** | Sum of daily values | Total lines of code suggested across all days | `23,456` |
| **total_acceptancePct** | Calculated | Overall acceptance rate (total_linesAccepted / total_linesSuggested × 100) | `52.63` |
| **total_messagesSent** | Sum of daily values | Total chat messages sent | `234` |
| **total_promptsUsed** | Sum of daily values | Total prompts/requests made | `8,901` |
| **total_promptCredits** | Sum of daily values | Total prompt credits consumed | `150.25` |
| **total_creditPromptCount** | Sum of daily values | Total credit data points (internal metric) | `42` |
| **models_used** | Aggregated | JSON array of all unique models used | `["Claude Sonnet 4.5", "Claude 3.7 Sonnet"]` |
| **ides_used** | Aggregated | JSON array of all unique IDEs/editors used | `["jetbrains", "vscode"]` |
| **total_tool_[TOOL_NAME]** | Sum of daily values | Total usage count for each tool | `125` |

---

## API Data Source Details

### 1. CascadeAnalytics API
**Endpoint:** `POST https://server.codeium.com/api/v1/CascadeAnalytics`

**Request Structure:**
```json
{
  "service_key": "...",
  "start_timestamp": "2026-01-01T00:00:00Z",
  "end_timestamp": "2026-01-31T23:59:59Z",
  "emails": ["user@example.com"],
  "query_requests": [
    {"cascade_lines": {}},
    {"cascade_runs": {}},
    {"cascade_tool_usage": {}}
  ]
}
```

**Provides:**
- `cascade_lines` → `linesAccepted`, `linesSuggested`
- `cascade_runs` → `messagesSent`, `promptsUsed`, `models`
- `cascade_tool_usage` → `tool_*` columns

**Date Format:** Returns dates as ISO timestamps (`2026-01-25T00:00:00Z`)

---

### 2. Analytics API (Custom Query)
**Endpoint:** `POST https://server.codeium.com/api/v1/Analytics`

**Request Structure:**
```json
{
  "service_key": "...",
  "query_requests": [{
    "data_source": "QUERY_DATA_SOURCE_CASCADE_DATA",
    "selections": [
      {"field": "api_key", "name": "api_key"},
      {"field": "date", "name": "date"},
      {"field": "prompts_used", "name": "prompts_used"},
      {"field": "model", "name": "model"},
      {"field": "ide", "name": "ide"}
    ],
    "filters": [
      {"name": "date", "filter": "QUERY_FILTER_GE", "value": "2026-01-01"},
      {"name": "date", "filter": "QUERY_FILTER_LE", "value": "2026-01-31"},
      {"name": "api_key", "filter": "QUERY_FILTER_EQUAL", "value": "..."}
    ]
  }]
}
```

**Provides:**
- `prompts_used` → `promptCredits` (divided by 100, API returns hundredths)
- `ide` → `ides` (aggregated into JSON array per day)

**Date Format:** Returns dates as simple dates (`2026-01-25`)

**Important:** Credit values in the API response are in **hundredths** (e.g., 2100 = 21.00 credits). The script automatically divides by 100.

---

### 3. UserPageAnalytics API
**Endpoint:** `POST https://server.codeium.com/api/v1/UserPageAnalytics`

**Request Structure:**
```json
{
  "service_key": "...",
  "start_timestamp": "2026-01-01T00:00:00Z",
  "end_timestamp": "2026-01-31T23:59:59Z"
}
```

**Provides:**
- List of users with `email` and `apiKey` mappings
- Used to map emails to API keys for the Analytics API queries

---

## Data Merging Process

1. **Fetch Users:** Call `UserPageAnalytics` to get email → API key mapping
2. **For Each User:**
   - Call `CascadeAnalytics` with user's email → get usage metrics
   - Call `Analytics` with user's API key → get credit consumption
3. **Normalize Dates:** Convert all dates to `YYYY-MM-DD` format
4. **Merge:** Combine data from both APIs by matching on (user_email, date)
5. **Output:** Write combined data to CSV

---

## Understanding the Metrics

### Lines Suggested vs. Accepted
- **Suggested:** AI proposes code changes
- **Accepted:** User accepts the suggestions
- **Acceptance %:** Higher = user finds AI suggestions more useful

### Messages vs. Prompts
- **Messages:** Individual chat messages sent to Cascade
- **Prompts:** Total number of AI requests (can be multiple per message)

### Credits
- **Prompt Credits:** Credits consumed for AI prompt processing
- **Note:** Credits are stored as hundredths in the API (e.g., 2100 = 21.00 credits) and automatically converted

### IDEs/Editors
- Shows which IDE/editor the user was working in (e.g., `vscode`, `jetbrains`, `vim`, `neovim`)
- Useful for understanding which development environments are most popular
- Common values: `vscode`, `jetbrains`, `vim`, `neovim`, `emacs`, `sublime`

### Tools
- Each tool column shows how many times that specific Cascade tool was used
- Tools are features like code editing, file viewing, search, etc.

---

## Example Row Interpretation

```csv
user_email,date,linesAccepted,linesSuggested,acceptancePct,messagesSent,promptsUsed,models,promptCredits,creditPromptCount,ides,tool_CODE_ACTION,tool_VIEW_FILE
alice@example.com,2026-01-25,177,563,31.44,7,2100,"[""Claude Sonnet 4.5""]",21.0,7,"[""vscode""]",5,12
```

**Translation:**
- **User:** alice@example.com on Jan 25, 2026
- **Code Generation:** AI suggested 563 lines, user accepted 177 (31.44% acceptance)
- **Chat Activity:** Sent 7 messages, made 2,100 prompts total
- **Model Used:** Claude Sonnet 4.5
- **Credits:** Consumed 21.0 prompt credits
- **IDE:** Used VS Code
- **Tools:** Used CODE_ACTION 5 times, VIEW_FILE 12 times

---

## Troubleshooting

### Why are some columns 0 or empty?
- **0 credits but activity:** User may be on a free tier or credits haven't been calculated yet
- **0 activity but credits:** Rare, but can happen if only credit data is available
- **Empty ides array:** IDE information may not be available for older data or certain usage patterns

### Why do I see duplicate dates (before the fix)?
- **Old data:** CascadeAnalytics returned `2026-01-25T00:00:00Z` and Analytics returned `2026-01-25`
- **Fixed:** The `normalize_date()` function now converts both to `2026-01-25` before merging

### Missing tool columns?
- Tool columns are dynamic and only appear if that tool was used by at least one user
- Different reports may have different tool columns based on actual usage
