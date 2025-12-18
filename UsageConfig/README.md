# UsageConfig Module

This module provides tools for managing user add-on credit cap configurations via the Windsurf Usage API.

## Overview

The Usage API is distinct from the Analytics API and provides endpoints for configuring credit limits at different scopes (team, group, or individual user). This module focuses on individual user configuration management.

**Key Insight**: The Usage API is scope-based. Setting a credit cap for one user does NOT affect other users' configurations. Each API call targets a specific scope, and configurations are stored independently.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/UsageConfig` | POST | Set or clear usage caps |
| `/api/v1/GetUsageConfig` | POST | Retrieve current usage caps |

## Scripts

### user_usage_config.py

A command-line tool for managing individual user credit caps.

#### Commands

**Get a user's current credit cap:**
```bash
python3 UsageConfig/user_usage_config.py get --email user@example.com
```

**Set a user's credit cap:**
```bash
python3 UsageConfig/user_usage_config.py set --email user@example.com --credit-cap 1000
```

**Clear a user's credit cap:**
```bash
python3 UsageConfig/user_usage_config.py clear --email user@example.com
```

**Set with verification (confirms other users aren't affected):**
```bash
python3 UsageConfig/user_usage_config.py set --email user@example.com --credit-cap 1000 \
    --verify-others user2@example.com,user3@example.com
```

#### Options

| Option | Description |
|--------|-------------|
| `--email` | User email address (required) |
| `--credit-cap` | Credit cap value to set (required for `set` command) |
| `--verify-others` | Comma-separated list of other user emails to verify are unchanged |
| `--json` | Output raw JSON response (for `get` command) |

## Configuration

The script requires a `SERVICE_KEY` environment variable. Configure this in your `.env` file:

```bash
SERVICE_KEY=your_service_key_here
```

The service key must have appropriate permissions. See the [Windsurf documentation](https://docs.windsurf.com/plugins/accounts/api-reference/usage-config) for details.

## API Behavior

### Scope-Based Configuration

The Usage API uses a scope-based approach where each API call targets exactly one scope:

- `team_level: true` - Applies to the entire team
- `group_id: "string"` - Applies to a specific group
- `user_email: "string"` - Applies to a specific user

When you set a credit cap for a user using `user_email`, only that user's configuration is modified. Other users' configurations remain unchanged.

### Configuration Hierarchy

Users can have configurations at multiple levels:
1. **User-level**: Specific to the individual user
2. **Group-level**: Applies to all users in a group
3. **Team-level**: Default for all team members

Clearing a user-level cap allows the user to fall back to group-level or team-level defaults.

## Verification Mode

The `--verify-others` option allows you to confirm that modifying one user's configuration doesn't affect other users. This is useful for:

- Testing the API behavior
- Auditing configuration changes
- Building confidence in the scope-based design

Example:
```bash
# Set user1's cap and verify user2 and user3 aren't affected
python3 UsageConfig/user_usage_config.py set \
    --email user1@example.com \
    --credit-cap 1000 \
    --verify-others user2@example.com,user3@example.com
```

## Related Documentation

- [Set Usage Configuration API](https://docs.windsurf.com/plugins/accounts/api-reference/usage-config)
- [Get Usage Configuration API](https://docs.windsurf.com/plugins/accounts/api-reference/get-usage-config)
