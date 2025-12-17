# Migration from GUI to Backend-Only CLI

This document summarizes the changes made to convert BSD Network Manager from a wxPython GUI application to a backend-only CLI interface.

## Changes Made

### 1. Main Entry Point (`bsd_netgui/main.py`)
- **Changed**: Complete rewrite from wxPython GUI to CLI-based interface
- **Removed**: All wxPython imports and GUI initialization
- **Added**: argparse for command-line argument parsing
- **Added**: CLI commands for network operations:
  - `status`: Show complete network status
  - `interfaces`: List all network interfaces
  - `wifi`: Show WiFi interfaces  
  - `dns`: Show DNS configuration
  - `routes`: Show routing table

### 2. Dependencies (`requirements.txt`)
- **Removed**: wxPython>=4.2.0
- **Kept**: netifaces>=0.11.0, psutil>=5.9.0 (still needed by backend)

### 3. GUI Panel Files (Deprecated)
All GUI panel files have been replaced with minimal stubs:
- `bsd_netgui/gui/main_window.py` → Deprecated stub
- `bsd_netgui/gui/interface_panel.py` → Deprecated stub
- `bsd_netgui/gui/wifi_panel.py` → Deprecated stub
- `bsd_netgui/gui/dns_panel.py` → Deprecated stub
- `bsd_netgui/gui/routing_panel.py` → Deprecated stub
- `bsd_netgui/gui/profile_panel.py` → Deprecated stub
- `bsd_netgui/gui/diagnostics_panel.py` → Deprecated stub
- `bsd_netgui/gui/backup_panel.py` → Deprecated stub

### 4. Version Update (`bsd_netgui/__init__.py`)
- Updated version from 0.1.0 to 0.2.0
- Updated description to reflect backend-only approach

## Backend Integration

The CLI now directly interfaces with the backend components:
- `NetworkManager`: Main coordinator for all backend operations
- `InterfaceHandler`: Network interface management
- `WiFiHandler`: WiFi operations
- `DNSHandler`: DNS configuration
- `RoutingHandler`: Routing table operations

These components remain unchanged and fully functional.

## Usage

The application now runs as a CLI tool:

```bash
# Show complete network status
sudo bsd-netgui status

# List network interfaces
sudo bsd-netgui interfaces

# Show WiFi interfaces
sudo bsd-netgui wifi

# Show DNS configuration
sudo bsd-netgui dns

# Show routing table
sudo bsd-netgui routes

# Show help
sudo bsd-netgui -h
```

## Benefits

1. **Reduced Dependencies**: Removed heavy wxPython dependency (easier to install/maintain)
2. **Lightweight**: Reduced memory footprint and faster startup
3. **Better Portability**: Works on headless systems
4. **Scriptable**: CLI output can be easily piped to other tools
5. **Focus on Backend**: All development effort now goes to the backend network management logic

## Future Enhancements

The CLI can be extended with additional commands:
- Configuration management
- Advanced routing operations
- Profile management
- Backup/restore operations
