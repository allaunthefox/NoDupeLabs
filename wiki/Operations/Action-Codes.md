# Standard Action Codes (ISO-8000 LUT)

NoDupeLabs uses an **ISO-8000-110:2021 compliant Look-Up Table (LUT)** to index every significant event in the system. This provides a universal reference for logging, auditing, and programmatic responses.

## Code Structure

All codes are **6-digit integers** categorized into the following ranges:

| Range | Category | Purpose |
|-------|----------|---------|
| **1xxxxx** | IPC & Flow | Socket server lifecycle, communication status |
| **2xxxxx** | Plugins | Loading, initialization, Hot Reload events |
| **3xxxxx** | Functional | Hashing, MIME detection, Archive, Database |
| **4xxxxx** | Security | Risk flags, access control, rate limiting |
| **5xxxxx** | Errors | System faults, execution failures, missing resources |

## Common Reference Table

| Code | Mnemonic | Risk Level | Description |
|------|----------|------------|-------------|
| **100000** | `IPC_START` | INFO | Programmatic IPC server initialization |
| **200005** | `HOT_RELOAD_DETECT` | MEDIUM | Change detected in monitored plugin file |
| **300002** | `ARCHIVE_OP` | MEDIUM | Archive manipulation (extract/create) |
| **400000** | `SECURITY_RISK_FLAGGED` | CRITICAL | Sensitive operation requested |
| **500003** | `ERR_EXEC_FAILED` | MEDIUM | Logic execution failed during processing |

## Programmatic Access

The full registry can be retrieved via the `lut_service` plugin over the [Socket IPC](Socket-IPC.md):

*   **Plugin:** `lut_service`
*   **Method:** `get_codes`
*   **Method:** `describe_code(code: int)`
