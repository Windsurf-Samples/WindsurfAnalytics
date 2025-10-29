# Windsurf Command Bytes Analytics - API Examples

## Endpoint
```
POST https://server.codeium.com/api/v1/Analytics
```

## Headers
```
Content-Type: application/json
```

## Basic Payload (All Users, Last 2 Days)

```json
{
  "service_key": "<SERVICE_KEY>",
  "query_requests": [
    {
      "data_source": "QUERY_DATA_SOURCE_COMMAND_DATA",
      "selections": [
        {"field": "api_key", "name": "api_key"},
        {"field": "date", "name": "date"},
        {"field": "timestamp", "name": "timestamp"},
        {"field": "language", "name": "language"},
        {"field": "ide", "name": "ide"},
        {"field": "command_source", "name": "command_source"},
        {"field": "provider_source", "name": "provider_source"},
        {"field": "bytes_added", "name": "bytes_added"},
        {"field": "bytes_removed", "name": "bytes_removed"},
        {"field": "lines_added", "name": "lines_added"},
        {"field": "lines_removed", "name": "lines_removed"},
        {"field": "accepted", "name": "accepted"}
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
        }
      ]
    }
  ]
}
```

## Curl Command (All Users)

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
          {"field": "language", "name": "language"},
          {"field": "ide", "name": "ide"},
          {"field": "command_source", "name": "command_source"},
          {"field": "provider_source", "name": "provider_source"},
          {"field": "bytes_added", "name": "bytes_added"},
          {"field": "bytes_removed", "name": "bytes_removed"},
          {"field": "lines_added", "name": "lines_added"},
          {"field": "lines_removed", "name": "lines_removed"},
          {"field": "accepted", "name": "accepted"}
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
          }
        ]
      }
    ]
  }'
```

## Curl Command (Filtered for xyz@company.com)

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
          {"field": "language", "name": "language"},
          {"field": "ide", "name": "ide"},
          {"field": "command_source", "name": "command_source"},
          {"field": "provider_source", "name": "provider_source"},
          {"field": "bytes_added", "name": "bytes_added"},
          {"field": "bytes_removed", "name": "bytes_removed"},
          {"field": "lines_added", "name": "lines_added"},
          {"field": "lines_removed", "name": "lines_removed"},
          {"field": "accepted", "name": "accepted"}
        ],
        "filters": [
          {
            "name": "date",
            "filter": "QUERY_FILTER_GE",
            "value": "2025-10-01"
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

## Minimal Example (Just Bytes Added)

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
          {"field": "bytes_added", "name": "bytes_added"}
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
          }
        ]
      }
    ]
  }'
```

## Available Fields for Command Data

| Field Name        | Description                                        | Valid Aggregations |
| ----------------- | -------------------------------------------------- | ------------------ |
| `api_key`         | Hash of user API key                               | UNSPECIFIED, COUNT |
| `date`            | UTC date of command                                | UNSPECIFIED, COUNT |
| `timestamp`       | UTC timestamp of command                           | UNSPECIFIED, COUNT |
| `language`        | Programming language                               | UNSPECIFIED, COUNT |
| `ide`             | IDE being used                                     | UNSPECIFIED, COUNT |
| `version`         | Windsurf version                                   | UNSPECIFIED, COUNT |
| `command_source`  | Command trigger source                             | UNSPECIFIED, COUNT |
| `provider_source` | Generation or edit mode                            | UNSPECIFIED, COUNT |
| `lines_added`     | Lines of code added                                | SUM, MAX, MIN, AVG |
| `lines_removed`   | Lines of code removed                              | SUM, MAX, MIN, AVG |
| `bytes_added`     | **Bytes added**                                    | SUM, MAX, MIN, AVG |
| `bytes_removed`   | **Bytes removed**                                  | SUM, MAX, MIN, AVG |
| `selection_lines` | Lines selected (zero for generations)              | SUM, MAX, MIN, AVG |
| `selection_bytes` | Bytes selected (zero for generations)              | SUM, MAX, MIN, AVG |
| `accepted`        | Whether command was accepted                       | SUM, COUNT         |

## Available Filters

| Filter Type              | Description                    | Example Value                           |
| ------------------------ | ------------------------------ | --------------------------------------- |
| `QUERY_FILTER_EQUAL`     | Exact match                    | `"<uuid>"` |
| `QUERY_FILTER_GE`        | Greater than or equal          | `"2025-10-01"`                          |
| `QUERY_FILTER_LE`        | Less than or equal             | `"2025-10-29"`                          |
| `QUERY_FILTER_GT`        | Greater than                   | `"100"`                                 |
| `QUERY_FILTER_LT`        | Less than                      | `"1000"`                                |
