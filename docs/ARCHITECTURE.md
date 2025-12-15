# BSD Network GUI - Architecture Documentation

## Overview

BSD Network GUI is a modern, user-friendly network management tool for FreeBSD and other BSD systems. This document describes the system architecture, design decisions, and component interactions.

## Design Principles

1. **BSD-Native**: Uses FreeBSD's native tools (ifconfig, wpa_supplicant, route, etc.)
2. **Safety-First**: Always backup before modifying configuration
3. **Parse, Don't Execute Blindly**: Parse configuration files instead of blind shell command execution
4. **Atomic Operations**: All configuration changes are atomic (write to temp, then move)
5. **Preserve State**: Maintain comments, formatting, and order in configuration files

## Architecture Layers

### 1. GUI Layer (`bsd_netgui/gui/`)

The presentation layer built with wxPython, providing an intuitive tabbed interface.

**Components:**
- `main_window.py` - Main application window with notebook interface
- `interface_panel.py` - Network interface management
- `wifi_panel.py` - WiFi scanning and connection
- `dns_panel.py` - DNS server configuration
- `routing_panel.py` - Routing table management
- `profile_panel.py` - **NEW**: Network profile management
- `diagnostics_panel.py` - **NEW**: Network diagnostics and troubleshooting
- `backup_panel.py` - **NEW**: Configuration backup and restore

**Design Pattern:**
- Each panel follows the same structure:
  - Initialize with `network_manager` reference
  - Create UI with wxPython widgets
  - Implement `refresh()` method for updating display
  - Handle user interactions with event handlers
  - Show clear error messages to users

### 2. Backend Layer (`bsd_netgui/backend/`)

The business logic layer that interacts with the system and manages network configuration.

#### Original Handlers

- **`network_manager.py`** - Singleton coordinator that provides unified interface to all handlers
- **`interface_handler.py`** - Manages network interfaces using `ifconfig`
- **`wifi_handler.py`** - Manages WiFi connections using `wpa_supplicant`
- **`dns_handler.py`** - Manages DNS configuration via `/etc/resolv.conf`
- **`routing_handler.py`** - Manages routing tables using `route` and `netstat`

#### New Enhanced Handlers

- **`rc_conf_handler.py`** - **NEW**: Parse and modify `/etc/rc.conf` safely
  - Preserves comments, order, and formatting
  - Supports interface configuration, default router, hostname, etc.
  - Validates changes before writing
  - Atomic writes with backup

- **`wpa_conf_handler.py`** - **NEW**: Parse and modify `/etc/wpa_supplicant.conf`
  - Manages multiple WiFi network profiles
  - Supports WPA/WPA2/WPA3/Open security
  - Priority-based connection ordering
  - Hidden network support (scan_ssid)

- **`profile_manager.py`** - **NEW**: Network profile abstraction
  - Combines rc.conf + wpa_supplicant.conf settings
  - Built-in templates for common scenarios
  - Import/export profiles as JSON
  - Apply profiles atomically

- **`backup_handler.py`** - **NEW**: Configuration backup and restore
  - ZFS snapshot support (when available)
  - File-based backup fallback
  - Automatic cleanup of old backups
  - Metadata tracking for each backup

- **`diagnostics_handler.py`** - **NEW**: Network diagnostics collection
  - Interface status and configuration
  - Routing table information
  - DNS configuration
  - Connectivity tests (gateway, external, DNS)
  - ARP table and active connections
  - WiFi signal strength
  - Export diagnostic reports

### 3. Utilities Layer (`bsd_netgui/utils/`)

Shared utilities and helpers used across the application.

- **`system_utils.py`** - System utility functions
  - `execute_command()` - Safe command execution with timeout
  - `validate_ip_address()` - IPv4 address validation
  - `validate_netmask()` - Netmask validation
  - `check_root_privileges()` - Root privilege detection
  - `setup_logging()` - Logging configuration

- **`config_parser.py`** - **NEW**: Generic shell-style config file parser
  - Preserves comments and formatting
  - Handles key=value pairs
  - Supports quoted values
  - Inline comment handling
  - Atomic writes

## Data Flow

### Profile Application Flow

```
User selects profile
    ↓
ProfilePanel.on_apply_profile()
    ↓
ProfileManager.apply_profile()
    ↓
BackupHandler.create_backup() [automatic]
    ↓
RCConfHandler.load() / WPAConfHandler.load()
    ↓
ConfigParser.parse() [parse config files]
    ↓
Apply profile settings to handlers
    ↓
Validate configuration
    ↓
ConfigParser.write() [atomic write]
    ↓
Success/Failure notification
```

### Configuration File Parsing Flow

```
RCConfHandler.load()
    ↓
ConfigParser.parse()
    ↓
Read file line by line
    ↓
Create ConfigLine objects
    ↓
Parse key=value pairs
    ↓
Handle inline comments
    ↓
Store in variables dict
    ↓
Configuration ready for use
```

### Backup and Restore Flow

```
Configuration change requested
    ↓
BackupHandler.create_backup()
    ↓
Check ZFS availability
    ├─ ZFS available
    │   ↓
    │   Create ZFS snapshot
    │   zfs snapshot pool/etc@netgui-TIMESTAMP
    │
    └─ ZFS not available
        ↓
        Copy config files to backup directory
        /var/backups/bsd-netgui/TIMESTAMP/
    ↓
Save metadata (JSON)
    ↓
Automatic cleanup of old backups
```

## Configuration File Management

### rc.conf Structure

The `rc.conf` file uses shell variable syntax:
```bash
# Network configuration
hostname="freebsd.local"
ifconfig_em0="DHCP"
ifconfig_em1="inet 192.168.1.100 netmask 255.255.255.0"
defaultrouter="192.168.1.1"
wlans_iwn0="wlan0"
ifconfig_wlan0="WPA DHCP"
```

**Parser Behavior:**
- Preserves all comments
- Maintains line order
- Handles quoted and unquoted values
- Supports inline comments
- Validates IP addresses and netmasks

### wpa_supplicant.conf Structure

The `wpa_supplicant.conf` file uses block syntax:
```
ctrl_interface=/var/run/wpa_supplicant
update_config=1

network={
    ssid="HomeNetwork"
    psk="mypassword"
    key_mgmt=WPA-PSK
    priority=5
    scan_ssid=1
}
```

**Parser Behavior:**
- Preserves header comments
- Supports multiple network blocks
- Handles all standard parameters
- Priority-based ordering
- Security type validation

## Profile System

### Profile Structure

Profiles combine network configuration into reusable units:

```json
{
  "name": "Home WiFi",
  "type": "wifi",
  "interface": "wlan0",
  "autoconnect": true,
  "config": {
    "ssid": "MyNetwork",
    "security": "WPA2-PSK",
    "password": "********",
    "dhcp": true,
    "priority": 5
  }
}
```

### Built-in Templates

1. **LAN (DHCP)** - Ethernet with automatic IP
2. **LAN (Static IP)** - Ethernet with manual IP configuration
3. **Home WiFi (WPA2)** - WPA2-PSK secured wireless
4. **Guest WiFi (Open)** - Open wireless network
5. **Mobile Tethering** - USB/Bluetooth tethering

### Profile Application

When a profile is applied:
1. Automatic backup is created
2. rc.conf is updated with interface configuration
3. wpa_supplicant.conf is updated (for WiFi profiles)
4. Configuration is validated
5. Files are written atomically
6. User is notified of success/failure

## Backup System

### ZFS Snapshot Mode

When `/etc` is on a ZFS filesystem:
- Creates snapshots: `pool/etc@netgui-TIMESTAMP`
- Fast and space-efficient
- Instant rollback capability
- Automatic cleanup (keeps last 10)

### File-based Mode

When ZFS is not available:
- Copies files to `/var/backups/bsd-netgui/TIMESTAMP/`
- Preserves permissions and timestamps
- Includes metadata JSON file
- Automatic cleanup (keeps last 20)

### Metadata Tracking

Each backup includes:
```json
{
  "timestamp": "2025-12-15T20:30:00Z",
  "method": "zfs",
  "files": ["rc.conf", "wpa_supplicant.conf"],
  "reason": "Applied profile: Home WiFi",
  "user": "root",
  "hostname": "freebsd-laptop",
  "snapshot_name": "tank/etc@netgui-20251215-203000"
}
```

## Diagnostics System

### Information Collection

The diagnostics handler collects:
- Interface status (`ifconfig -a`)
- Routing table (`netstat -rn`)
- DNS configuration (`/etc/resolv.conf`)
- ARP table (`arp -a`)
- Active connections (`sockstat` or `netstat -an`)
- WiFi signal strength (`ifconfig wlan0`)

### Connectivity Tests

1. **Gateway Test**: Ping default gateway (3 packets)
2. **External Test**: Ping 8.8.8.8 (3 packets)
3. **DNS Test**: Resolve cloudflare.com using nslookup

### Status Indicators

- **Green**: Test successful
- **Red**: Test failed
- **Orange**: Configuration error (e.g., no gateway set)

### Common Issues Help

Built-in help for:
- No default gateway configured
- DNS servers unreachable
- Interface has no IP address
- WiFi not connecting
- Routing/firewall issues

## Safety Features

### Validation

Before writing configuration:
1. Syntax validation
2. IP address validation
3. Netmask validation
4. Check for duplicate keys
5. Network-specific validation (SSID, security type, etc.)

### Atomic Writes

All file writes follow this pattern:
```python
1. Create backup (.bak)
2. Write to temporary file (.tmp)
3. Validate temporary file
4. Move temporary file to actual file (atomic)
5. Cleanup on error
```

### Error Handling

- All operations wrapped in try/except
- Clear error messages to users
- Detailed logging for troubleshooting
- Graceful degradation when tools unavailable

## Threading Model

### Main Thread (GUI)

- All wxPython operations
- Event handling
- User interaction

### Background Threads

Used for:
- Network diagnostics collection
- Connectivity tests
- Long-running operations

Communication via `wx.CallAfter()` to update GUI safely.

## Logging

### Log Levels

- **INFO**: Normal operations, successful actions
- **WARNING**: Non-critical issues, fallback modes
- **ERROR**: Operation failures, configuration errors
- **DEBUG**: Detailed diagnostic information

### Log Locations

- Console output (during development)
- `/var/log/bsd-netgui.log` (production, if writable)
- Syslog integration (future enhancement)

## Security Considerations

### Privilege Requirements

- Root privileges required for network configuration
- File permissions verified before operations
- Config files set to appropriate permissions (e.g., 0600 for wpa_supplicant.conf)

### Sensitive Data

- Passwords masked in GUI displays
- WiFi passwords stored in wpa_supplicant.conf with 0600 permissions
- Backup files preserve original permissions

### Input Validation

- All user input validated
- IP addresses checked for valid format
- Netmasks validated (dotted decimal or CIDR)
- Interface names sanitized

## Future Enhancements

### Planned Features

1. **Test Mode**: Apply changes temporarily with auto-rollback
2. **Syslog Integration**: Log all changes to syslog
3. **Service Management**: Start/stop/restart network services
4. **VPN Support**: Profile templates for VPN connections
5. **IPv6 Support**: Full IPv6 configuration support
6. **Firewall Integration**: pf rules management
7. **Network Monitoring**: Real-time traffic graphs
8. **Remote Management**: Web interface for remote configuration

### Code Quality

- Type hints throughout codebase
- Google-style docstrings
- Comprehensive unit tests
- Integration tests on FreeBSD
- CI/CD pipeline

## Dependencies

### Required

- Python 3.8+
- wxPython 4.2.0+
- netifaces 0.11.0+
- psutil 5.9.0+

### Optional

- ZFS utilities (for snapshot support)
- wpa_supplicant (for WiFi)
- Various network tools (ifconfig, route, netstat, etc.)

## Testing Strategy

### Unit Tests

- Configuration parsers
- Backup handler
- Profile manager
- Validation functions

### Integration Tests

- Profile application end-to-end
- Backup and restore cycle
- Configuration file round-trip

### Manual Testing

- GUI functionality
- Network operations (requires root)
- FreeBSD-specific commands

## Deployment

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install package
sudo python setup.py install

# Run application
sudo bsd-netgui
```

### System Integration

- Desktop entry for application launcher
- Man page documentation
- Sample configuration files

## References

- FreeBSD Handbook: Networking Chapter
- wxPython Documentation
- Python Standard Library
- ZFS Administration Guide

## Contributors

See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines.

## License

MIT License - See [LICENSE](../LICENSE) for details.
