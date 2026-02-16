# Programmatic Socket IPC Interface

NoDupeLabs provides a **Unix Domain Socket** interface for programmatic, external access to plugin capabilities. This allows third-party tools and the [MCP Interface](MCP.md) to invoke plugin methods securely.

## Connection Details

*   **Socket Path:** `/tmp/nodupe.sock`
*   **Protocol:** JSON-RPC over TCP/Unix Stream
*   **Timeout:** 1.0 second

## Request Format

Requests must be sent as a single JSON object:

```json
{
  "plugin": "plugin_name",
  "method": "method_name",
  "params": {
    "arg1": "value1"
  },
  "id": 123
}
```

## Response Format

The server responds with a standard JSON-RPC envelope:

```json
{
  "jsonrpc": "2.0",
  "result": { ... },
  "id": 123
}
```

### Error Responses

Errors include a standardized [Action Code](Action-Codes.md) in the error object:

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": 500003,
    "message": "Method execution failed: ..."
  },
  "id": 123
}
```

## Security & Logging

1.  **Whitelist:** Only methods explicitly defined in a plugin's `api_methods` property are accessible.
2.  **Rate Limiting:** Limited to 1000 requests per 30 seconds to prevent DoS.
3.  **Risk Flagging:** Sensitive calls (like archive extraction) are flagged with Action Code `400000` for audit review.
