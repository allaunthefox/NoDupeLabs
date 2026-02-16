# Logging Policy

NoDupeLabs enforces a strict logging policy to ensure persistent, searchable, and resource-efficient audit trails.

## Log Management

1.  **Format:** All logs follow a structured format: `[CODE] Message | key=value context`.
2.  **Storage:** Persistent logging to the `logs/` directory.
3.  **Rotation:** Files rotate automatically when they reach **10MB**.
4.  **Retention:** Up to **5 backup rotations** are kept on disk.

## Automated Compression

To optimize disk usage, the system leverages its built-in ZIP capabilities to compress logs:

*   **Trigger:** Logs are scanned and compressed during system **shutdown**.
*   **Target:** All rotated log files (e.g., `app.log.1`, `app.log.2`) that are not already zipped.
*   **Action:** Rotated logs are converted to `.zip` archives and the original text files are removed.
*   **Action Code:** Log compression events are indexed under `300002` (`ARCHIVE_OP`).

## Rate Limiting

Programmatic interactions are rate-limited to ensure log stability:
*   **Limit:** 1000 events / 30 seconds.
*   **Handling:** Excess events trigger code `400002` (`RATE_LIMIT_HIT`) and are dropped.
