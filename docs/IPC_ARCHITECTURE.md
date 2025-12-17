# BSD Network Manager - IPC Architecture Documentation

## Overview

The IPC (Inter-Process Communication) module enables communication between the BSD Network Manager daemon and CLI clients using Unix domain sockets. This architecture separates the backend logic (daemon) from the command-line interface, allowing multiple clients to communicate with a single daemon process.

---

## Architecture

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                      BSD Network Manager                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐      ┌──────────────────────┐                 │
│  │   GUI App    │      │   CLI Application    │                 │
│  │  (Future)    │      │  (bsd-netgui-cli)    │                 │
│  └──────┬───────┘      └──────────┬───────────┘                 │
│         │                         │                              │
│         │    Unix Domain Socket   │                              │
│         │    /var/run/            │                              │
│         │    bsd-netgui.sock      │                              │
│         │                         │                              │
│         └────────────┬────────────┘                              │
│                      │                                           │
│              ┌───────▼────────┐                                  │
│              │   IPC Server   │                                  │
│              │  (daemon.py)   │                                  │
│              └───────┬────────┘                                  │
│                      │                                           │
│              ┌───────▼─────────────────┐                         │
│              │  NetworkManager Backend │                         │
│              │  (Pure Logic, No IPC)   │                         │
│              │                         │                         │
│              ├─ Interface Handler      │                         │
│              ├─ WiFi Handler           │                         │
│              ├─ DNS Handler            │                         │
│              ├─ Routing Handler        │                         │
│              ├─ RC Conf Handler        │                         │
│              └─ Other Handlers         │                         │
│              └─────────────────────────┘                         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Communication Protocol

### Message Format

All messages use JSON over Unix domain sockets, terminated with a null byte (`\0`).

#### Request Structure

```json
{
  "action": "string",           // Required: Action to perform
  "params": {                   // Optional: Parameters for the action
    "key1": "value1",
    "key2": "value2"
  }
}
```

#### Response Structure

```json
{
  "success": boolean,           // Required: Success status
  "data": "any",               // Optional: Response data (for successful requests)
  "error": "string"            // Optional: Error message (when success is false)
}
```

### Message Transmission Flow

```
Client Process                      Server Process (Daemon)
│                                   │
├─ Create Socket                    │
├─ Connect to Socket                │
│                ├─ Accept Connection
│                │
├─ Format JSON Request              │
├─ Add '\0' Terminator              │
├─ Send over Socket ────────────────┤
│                ├─ Receive bytes
│                ├─ Accumulate until '\0' found
│                ├─ Parse JSON
│                ├─ Validate Action
│                │
│                ├─ Call Backend Handler
│                │
│                ├─ Format JSON Response
│                ├─ Add '\0' Terminator
│ Receive Response ◄────────────────┤ Send over Socket
│                │
├─ Receive bytes                    │
├─ Accumulate until '\0' found      │
├─ Parse JSON                       │
├─ Extract data/error               │
│                │
├─ Close Socket                     │
│                ├─ Close Connection
│                │
```

---

## Socket Implementation Details

### Unix Domain Sockets

Unix domain sockets provide several advantages for local IPC:

1. **Security**: Only accessible to processes on the same machine
2. **Performance**: No network stack overhead
3. **Permissions**: Can use filesystem permissions to control access
4. **Simplicity**: No need for TCP port management

### Socket Path

Default: `/var/run/bsd-netgui.sock`

- Can be customized via `--socket` parameter
- Requires write access to `/var/run/` (typically root)
- Old socket file is automatically cleaned up on daemon startup

### Connection Lifecycle

```
IPCServer.start()
    ├─ Remove old socket file
    ├─ Create socket (AF_UNIX, SOCK_STREAM)
    ├─ Bind to socket path
    ├─ Listen for connections
    │
    └─ Start background thread: _accept_connections()
        └─ Loop:
            ├─ Accept incoming connection
            ├─ Start new thread: _handle_client(connection)
            │   ├─ Read JSON message (accumulate until '\0')
            │   ├─ Parse JSON
            │   ├─ Call request_handler()
            │   ├─ Send JSON response with '\0'
            │   └─ Close connection
            │
            └─ Continue listening
```

---

## Request Handlers

### Implemented Actions

#### 1. **get_status**
Retrieve complete network status

```json
Request:
{
  "action": "get_status"
}

Response:
{
  "success": true,
  "data": {
    "interfaces": [...],
    "routes": [...],
    "dns": [...],
    ...
  }
}
```

#### 2. **get_interfaces**
List all network interfaces

```json
Request:
{
  "action": "get_interfaces"
}

Response:
{
  "success": true,
  "data": ["em0", "em1", "lo0"]
}
```

#### 3. **get_wifi_interfaces**
List WiFi interfaces

```json
Request:
{
  "action": "get_wifi_interfaces"
}

Response:
{
  "success": true,
  "data": ["wlan0", "wlan1"]
}
```

#### 4. **get_dns**
Get DNS servers

```json
Request:
{
  "action": "get_dns"
}

Response:
{
  "success": true,
  "data": ["8.8.8.8", "8.8.4.4"]
}
```

#### 5. **get_routes**
Get routing table

```json
Request:
{
  "action": "get_routes"
}

Response:
{
  "success": true,
  "data": [
    {"destination": "0.0.0.0/0", "gateway": "192.168.1.1", "interface": "em0"},
    ...
  ]
}
```

#### 6. **set_interface_ip**
Configure interface IP address

```json
Request:
{
  "action": "set_interface_ip",
  "params": {
    "interface": "em0",
    "ip": "192.168.1.100/24"
  }
}

Response:
{
  "success": true
}
```

#### 7. **enable_interface**
Enable a network interface

```json
Request:
{
  "action": "enable_interface",
  "params": {
    "interface": "em0"
  }
}

Response:
{
  "success": true
}
```

#### 8. **disable_interface**
Disable a network interface

```json
Request:
{
  "action": "disable_interface",
  "params": {
    "interface": "em0"
  }
}

Response:
{
  "success": true
}
```

---

## Class Diagrams

### IPCServer Class

```
┌─────────────────────────────────────┐
│          IPCServer                  │
├─────────────────────────────────────┤
│ Attributes:                         │
│  - socket_path: str                 │
│  - socket: socket.socket            │
│  - running: bool                    │
│  - request_handler: Callable        │
├─────────────────────────────────────┤
│ Methods:                            │
│  + __init__(socket_path)            │
│  + set_request_handler(handler)     │
│  + start()                          │
│  + stop()                           │
│  - _accept_connections()            │
│  - _handle_client(connection)       │
├─────────────────────────────────────┤
│ Thread Model:                       │
│  - Main thread: accept connections  │
│  - Worker threads: handle clients   │
│  - Daemon threads (don't block exit)│
└─────────────────────────────────────┘
```

### IPCClient Class

```
┌─────────────────────────────────────┐
│          IPCClient                  │
├─────────────────────────────────────┤
│ Attributes:                         │
│  - socket_path: str                 │
├─────────────────────────────────────┤
│ Methods:                            │
│  + __init__(socket_path)            │
│  + send_request(request_dict,       │
│      timeout=5.0) -> dict           │
├─────────────────────────────────────┤
│ Behavior:                           │
│  - Synchronous (blocking)           │
│  - Auto-connects and disconnects    │
│  - Configurable timeout             │
│  - Error handling & logging         │
└─────────────────────────────────────┘
```

---

## Data Flow Examples

### Example 1: Getting Network Status

```
┌─────────────────────────────────────────────────────────────┐
│ Client (CLI)                                                │
│                                                             │
│ $ bsd-netgui-cli status                                     │
│                                                             │
│ 1. Parse arguments                                          │
│ 2. Create IPCClient("/var/run/bsd-netgui.sock")            │
│ 3. Build request: {"action": "get_status"}                 │
│ 4. Call send_request(request)                              │
│                                                             │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Connect to Unix socket
                 │ Send: '{"action": "get_status"}\0'
                 ▼
┌────────────────────────────────────────────────────────────┐
│ Server (Daemon)                                            │
│                                                            │
│ 1. _handle_client() receives connection                    │
│ 2. Reads bytes until '\0' found                            │
│ 3. Parses JSON: {"action": "get_status"}                   │
│ 4. Calls request_handler()                                 │
│ 5. Calls network_manager.get_all_status()                  │
│ 6. Builds response:                                        │
│    {                                                       │
│      "success": true,                                      │
│      "data": {...network status...}                        │
│    }                                                       │
│ 7. Sends: '{...response...}\0'                             │
│                                                            │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Response received
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Client (CLI)                                                │
│                                                             │
│ 8. Receives and parses JSON response                        │
│ 9. Extracts data field                                      │
│ 10. Pretty-prints JSON to stdout                            │
│                                                             │
│ Output:                                                     │
│ {                                                           │
│   "interfaces": ["em0", "em1"],                             │
│   "routes": [...],                                          │
│   ...                                                       │
│ }                                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Example 2: Setting Interface IP

```
┌──────────────────────────────────────────────────────────┐
│ Client (CLI)                                             │
│                                                          │
│ $ bsd-netgui-cli set-ip em0 192.168.1.100/24            │
│                                                          │
│ Request:                                                 │
│ {                                                        │
│   "action": "set_interface_ip",                          │
│   "params": {                                            │
│     "interface": "em0",                                  │
│     "ip": "192.168.1.100/24"                             │
│   }                                                      │
│ }                                                        │
│                                                          │
└─────────────────┬──────────────────────────────────────┘
                  │
                  │ JSON + '\0' over socket
                  ▼
┌──────────────────────────────────────────────────────────┐
│ Server (Daemon)                                          │
│                                                          │
│ 1. Parse request                                         │
│ 2. Extract action: "set_interface_ip"                    │
│ 3. Extract params: {interface, ip}                       │
│ 4. Call network_manager.interface_handler               │
│    .set_interface_ip("em0", "192.168.1.100/24")         │
│ 5. Handle any exceptions                                 │
│ 6. Return: {"success": true}                             │
│                                                          │
└─────────────────┬──────────────────────────────────────┘
                  │
                  │ Response JSON + '\0'
                  ▼
┌──────────────────────────────────────────────────────────┐
│ Client (CLI)                                             │
│                                                          │
│ Output: ✓ Command executed successfully                 │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Threading Model

### Daemon Threading

```
┌─────────────────────────────────────────────────────┐
│ Main Thread (daemon.py:main())                      │
│                                                     │
│ 1. Initialize NetworkManager (synchronous)         │
│ 2. Create IPCServer                                │
│ 3. Set request_handler                             │
│ 4. Call ipc_server.start()                          │
│    └─ Spawns: Accept Thread (daemon=True)          │
│ 5. Call signal.pause() (blocks here)               │
│                                                     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Accept Thread (ipc_server:_accept_connections)     │
│ (daemon=True, won't block process exit)            │
│                                                     │
│ Loop (while running):                              │
│  1. Wait for connection                            │
│  2. Accept connection socket                       │
│  3. Spawn Client Handler Thread (daemon=True)      │
│     └─ Handles single client                       │
│  4. Continue loop                                  │
│                                                     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Client Handler Threads (daemon=True)               │
│ (Multiple instances, one per client)               │
│                                                     │
│ 1. Read from socket until '\0'                     │
│ 2. Parse JSON request                              │
│ 3. Call request_handler()                          │
│ 4. Format response                                 │
│ 5. Send response                                   │
│ 6. Close connection & exit                         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Key Threading Characteristics

- **Accept Thread**: Daemon thread, accepts connections continuously
- **Client Handlers**: Daemon threads, one per client
- **Thread-safe**: Each handler operates on separate socket connection
- **Backend isolation**: Backend handlers are NOT inherently thread-safe
  - Consider using locks if backend needs concurrent access
- **Graceful shutdown**: Signal handlers can stop the server immediately

---

## Error Handling

### Client-Side Error Handling

```python
response = client.send_request(request)

if response.get("success"):
    # Process data
    print(response["data"])
else:
    # Handle error
    error = response.get("error", "Unknown error")
    print(f"Error: {error}")
```

### Server-Side Error Handling

```python
try:
    # Process request
    response = request_handler(request)
except json.JSONDecodeError:
    # Invalid JSON
    logger.error("Invalid JSON received")
except Exception as e:
    # Generic error
    return {"success": False, "error": str(e)}
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Connection refused | Daemon not running | Start daemon: `bsd-netgui-daemon` |
| Request timeout | Daemon unresponsive | Check daemon logs, restart if needed |
| Socket not found | Wrong socket path | Use correct `--socket` parameter |
| Permission denied | Wrong socket permissions | Ensure daemon runs as root |
| Invalid JSON | Malformed request | Check request format |
| Unknown action | Unsupported command | Use supported actions |

---

## Security Considerations

### 1. Socket Permissions

Unix domain sockets use filesystem permissions:
- Typically created as `/var/run/bsd-netgui.sock`
- Owner: root (daemon runs as root)
- Permissions: Can be restricted to specific users/groups

### 2. Root Privileges

- Daemon requires root to manage network settings
- Client can be unprivileged (communicates via socket)
- Socket acts as security boundary

### 3. Input Validation

Current validation:
- JSON parsing catches malformed messages
- Action names are whitelisted
- Parameters are passed directly to backend

**Recommendations:**
- Validate parameter values before backend use
- Add rate limiting if needed
- Consider authentication for sensitive operations

### 4. Socket Cleanup

- Old socket files are automatically removed on startup
- Socket is properly closed on daemon shutdown
- Failed connections don't leak resources

---

## Performance Characteristics

### Latency

- **Socket Creation**: ~1-5ms
- **JSON Serialization**: ~0.1-1ms (depending on data size)
- **Backend Operation**: Depends on operation (varies widely)
- **Total Roundtrip**: Typically <50ms for simple operations

### Throughput

- Multiple concurrent clients supported (one thread per client)
- Typical capacity: 100+ concurrent connections on modern hardware
- No practical limit for sequential requests

### Resource Usage

- **Memory per connection**: ~50KB (Python + buffers)
- **CPU**: Minimal (I/O bound, not CPU bound)
- **File descriptors**: 1 per connection + 1 for listening socket

---

## Usage Examples

### Starting the Daemon

```bash
# Basic daemon startup
sudo bsd-netgui-daemon

# Custom socket path
sudo bsd-netgui-daemon --socket /tmp/bsd-netgui.sock

# Debug logging
sudo bsd-netgui-daemon --loglevel DEBUG --nodaemon

# In foreground (useful for debugging)
sudo bsd-netgui-daemon --nodaemon
```

### Using the CLI

```bash
# Show network status
bsd-netgui-cli status

# List interfaces
bsd-netgui-cli interfaces

# Get WiFi interfaces
bsd-netgui-cli wifi

# Show DNS servers
bsd-netgui-cli dns

# Show routes
bsd-netgui-cli routes

# Configure interface
sudo bsd-netgui-cli set-ip em0 192.168.1.100/24

# Enable interface
sudo bsd-netgui-cli enable em0

# Disable interface
sudo bsd-netgui-cli disable em0
```

### Using IPCClient Directly (Python)

```python
from bsd_netgui.ipc import IPCClient

client = IPCClient("/var/run/bsd-netgui.sock")

# Get status
response = client.send_request({"action": "get_status"})
if response["success"]:
    print(response["data"])

# Set IP
response = client.send_request({
    "action": "set_interface_ip",
    "params": {"interface": "em0", "ip": "192.168.1.100/24"}
})
print("Success!" if response["success"] else f"Error: {response['error']}")
```

---

## Future Enhancements

### Possible Improvements

1. **Authentication**: Add token-based or capability-based access control
2. **Pub/Sub**: Implement event subscription for network changes
3. **Streaming Responses**: Support large data transfers in chunks
4. **Connection Pooling**: Client-side connection reuse
5. **Metrics**: Collect request/response statistics
6. **Binary Protocol**: Use protobuf/msgpack for better performance
7. **TLS over Unix Socket**: Enhanced security for sensitive operations
8. **Rate Limiting**: Prevent abuse of sensitive operations

---

## Debugging

### Enable Debug Logging

```bash
# Daemon with debug output
sudo bsd-netgui-daemon --loglevel DEBUG --nodaemon

# CLI with verbose output
bsd-netgui-cli --verbose status
```

### Monitor Socket Activity

```bash
# Watch daemon logs
tail -f /var/log/bsd-netgui.log

# Check socket exists
ls -la /var/run/bsd-netgui.sock

# Monitor connections (Linux)
netstat -x | grep bsd-netgui

# Monitor connections (FreeBSD)
sockstat -u | grep bsd-netgui
```

### Test Socket Communication

```bash
# Raw socket test (Unix socket)
nc -U /var/run/bsd-netgui.sock

# Then send raw JSON:
{"action": "get_interfaces"}
<Ctrl+D or send \0>
```

---

## References

- **Unix Domain Sockets**: [man page](https://man7.org/linux/man-pages/man7/unix.7.html)
- **Python socket module**: [docs](https://docs.python.org/3/library/socket.html)
- **JSON Protocol**: [RFC 8259](https://tools.ietf.org/html/rfc8259)
