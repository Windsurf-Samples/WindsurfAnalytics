# Windsurf Autocomplete/Tab Acceptance Analytics Guide

## 🎯 **Overview**

Autocomplete/tab acceptance data is available through the **`QUERY_DATA_SOURCE_USER_DATA`** data source in the Windsurf Analytics API. This tracks when users press Tab to accept autocomplete suggestions.

## 📊 **Available Data**

### **Key Metrics**
- **`num_acceptances`** - Number of times user pressed Tab to accept suggestions
- **`num_lines_accepted`** - Total lines of code accepted via Tab
- **`num_bytes_accepted`** - Total bytes accepted via Tab

### **Dimensions**
- **`api_key`** - User identifier (hash)
- **`date`** - UTC date of autocompletion
- **`hour`** - UTC hour of autocompletion (aggregated per hour)
- **`language`** - Programming language
- **`ide`** - IDE being used
- **`version`** - Windsurf version

## 🔧 **API Usage**

### **Endpoint**
```
POST https://server.codeium.com/api/v1/Analytics
```

### **Basic Payload**
```json
{
  "service_key": "your_service_key",
  "query_requests": [
    {
      "data_source": "QUERY_DATA_SOURCE_USER_DATA",
      "selections": [
        {"field": "api_key", "name": "api_key"},
        {"field": "date", "name": "date"},
        {"field": "num_acceptances", "name": "num_acceptances"},
        {"field": "num_lines_accepted", "name": "num_lines_accepted"},
        {"field": "num_bytes_accepted", "name": "num_bytes_accepted"}
      ],
      "filters": [
        {
          "name": "date",
          "filter": "QUERY_FILTER_GE",
          "value": "2025-10-28"
        }
      ]
    }
  ]
}
```

### **Curl Example**
```bash
curl -X POST https://server.codeium.com/api/v1/Analytics \
  -H "Content-Type: application/json" \
  -d '{
    "service_key": "<SERVICE_KEY>",
    "query_requests": [
      {
        "data_source": "QUERY_DATA_SOURCE_USER_DATA",
        "selections": [
          {"field": "api_key", "name": "api_key"},
          {"field": "date", "name": "date"},
          {"field": "num_acceptances", "name": "num_acceptances"},
          {"field": "num_lines_accepted", "name": "num_lines_accepted"},
          {"field": "num_bytes_accepted", "name": "num_bytes_accepted"}
        ],
        "filters": [
          {
            "name": "date",
            "filter": "QUERY_FILTER_GE",
            "value": "2025-10-28"
          },
          {
            "name": "api_key",
            "filter": "QUERY_FILTER_EQUAL",
            "value": "<UUID>"
          }
        ]
      }
    ]
  }'
```

## 🐍 **Python Script Usage**

We've created a dedicated autocomplete analyzer script:

```bash
# Analyze your autocomplete acceptances
python AnalyticScripts/autocomplete_analyzer.py --emails xyz@company.com

# Analyze multiple users
python AnalyticScripts/autocomplete_analyzer.py --emails xyz@company.com abc@company.com

# Custom date range
python AnalyticScripts/autocomplete_analyzer.py --start-date 2025-10-01 --end-date 2025-10-29

# Direct API key usage
python AnalyticScripts/autocomplete_analyzer.py --api-keys <UUID>

# Include JSON output
python AnalyticScripts/autocomplete_analyzer.py --emails xyz@company.com --output-json
```

## 📈 **Your Autocomplete Data Analysis**

### **xyz@company.com (Oct 1-29, 2025)**

**Summary:**
- **22 total acceptances** across 9 coding sessions
- **22 lines accepted** (1:1 ratio with acceptances)
- **0 bytes accepted** (all structural/whitespace changes)

**Breakdown by Language:**
- **YAML**: 6 acceptances, 6 lines
- **UNSPECIFIED**: 8 acceptances, 8 lines  
- **TSX**: 5 acceptances, 5 lines
- **MARKDOWN**: 2 acceptances, 2 lines
- **SHELL**: 1 acceptance, 1 line

**Activity Timeline:**
```
Oct 02 19:00 | TSX          | windsurf-next   | 1 acceptance
Oct 20 20:00 | MARKDOWN     | windsurf-next   | 2 acceptances  
Oct 22 17:00 | YAML         | windsurf        | 4 acceptances
Oct 22 18:00 | YAML         | windsurf        | 1 acceptance
Oct 24 13:00 | YAML         | windsurf        | 1 acceptance
Oct 24 16:00 | UNSPECIFIED  | windsurf        | 7 acceptances ⭐
Oct 27 17:00 | UNSPECIFIED  | windsurf        | 1 acceptance
Oct 28 18:00 | TSX          | windsurf        | 4 acceptances
Oct 29 14:00 | SHELL        | windsurf        | 1 acceptance
```

## 🆚 **Autocomplete vs Command Data**

| Data Source | Purpose | Key Metrics | Your Usage |
|-------------|---------|-------------|------------|
| **USER_DATA** (Autocomplete) | Tab acceptances | `num_acceptances`, `num_lines_accepted` | 22 acceptances, 22 lines |
| **COMMAND_DATA** (Commands) | Windsurf Command | `bytes_added`, `lines_added`, `accepted` | 2 commands, 0 bytes, 2 lines |

## 📋 **Available Fields Reference**

| Field Name | Description | Valid Aggregations |
|------------|-------------|-------------------|
| `api_key` | Hash of user API key | UNSPECIFIED, COUNT |
| `date` | UTC date of autocompletion | UNSPECIFIED, COUNT |
| `date UTC-x` | Date with timezone offset | UNSPECIFIED, COUNT |
| `hour` | UTC hour of autocompletion | UNSPECIFIED, COUNT |
| `language` | Programming language | UNSPECIFIED, COUNT |
| `ide` | IDE being used | UNSPECIFIED, COUNT |
| `version` | Windsurf version | UNSPECIFIED, COUNT |
| `num_acceptances` | **Number of autocomplete acceptances** | SUM, MAX, MIN, AVG |
| `num_lines_accepted` | **Lines of code accepted** | SUM, MAX, MIN, AVG |
| `num_bytes_accepted` | **Bytes accepted** | SUM, MAX, MIN, AVG |
| `distinct_users` | Distinct users | UNSPECIFIED, COUNT |
| `distinct_developer_days` | Distinct (user, day) tuples | UNSPECIFIED, COUNT |
| `distinct_developer_hours` | Distinct (user, hour) tuples | UNSPECIFIED, COUNT |
