# Email-Based Filtering for Windsurf Command Bytes Analytics

## ❌ Direct Email Filtering (NOT SUPPORTED)

The Windsurf Analytics API **does not support direct email filtering** in the `QUERY_DATA_SOURCE_COMMAND_DATA` data source. 

**Available filters for command data:**
- `api_key` ✅
- `date` ✅  
- `timestamp` ✅
- `language` ✅
- `ide` ✅
- `version` ✅
- `command_source` ✅
- `provider_source` ✅
- `bytes_added`, `bytes_removed`, `lines_added`, `lines_removed` ✅
- `accepted` ✅

**NOT available:**
- `email` ❌

## ✅ Workaround: Email → API Key Conversion

### Step 1: Get Email-to-API-Key Mapping
```bash
curl -X POST https://server.codeium.com/api/v1/UserPageAnalytics \
  -H "Content-Type: application/json" \
  -d '{
    "service_key": "<SERVICE_KEY>",
    "start_timestamp": "2025-10-01T00:00:00Z",
    "end_timestamp": "2025-10-29T23:59:59Z"
  }'
```

### Step 2: Extract API Key for Target Email
From the UserPageAnalytics response, find:
- `xyz@company.com` → `<UUID>`

### Step 3: Use API Key in Command Data Query
```bash
curl -X POST https://server.codeium.com/api/v1/Analytics \
  -H "Content-Type: application/json" \
  -d '{
    "service_key": "<SERVICE_KEY>",
    "query_requests": [
      {
        "data_source": "QUERY_DATA_SOURCE_COMMAND_DATA",
        "selections": [
          {"field": "api_key", "name": "api_key"},
          {"field": "date", "name": "date"},
          {"field": "timestamp", "name": "timestamp"},
          {"field": "bytes_added", "name": "bytes_added"},
          {"field": "bytes_removed", "name": "bytes_removed"},
          {"field": "lines_added", "name": "lines_added"},
          {"field": "lines_removed", "name": "lines_removed"},
          {"field": "accepted", "name": "accepted"},
          {"field": "language", "name": "language"},
          {"field": "ide", "name": "ide"}
        ],
        "filters": [
          {
            "name": "date",
            "filter": "QUERY_FILTER_GE",
            "value": "2025-10-28"
          },
          {
            "name": "date",
            "filter": "QUERY_FILTER_LE",
            "value": "2025-10-29"
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

## 🎯 Python Script Solution

Our updated Python script now supports email filtering:

```bash
# Filter by email (automatically converts to API key)
python AnalyticScripts/command_bytes_analyzer.py --emails xyz@company.com

# Filter by multiple emails
python AnalyticScripts/command_bytes_analyzer.py --emails xyz@company.com abc@company.com

# Still supports direct API key filtering
python AnalyticScripts/command_bytes_analyzer.py --api-keys <UUID>
```

## 🔑 Key Takeaways

1. **Email filtering requires a two-step process** (email→API key→command data)
2. **Our Python script automates this** with the `--emails` parameter
3. **Direct curl requires manual API key lookup**
4. **The API design separates user identity from command data** for performance/privacy reasons
