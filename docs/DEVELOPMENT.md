# BSD Network Manager - Development Documentation

## Architecture Overview

BSD Network Manager is structured in three main layers:

### 1. GUI Layer (`bsd_netgui/gui/`)

The GUI layer uses wxPython to provide a user-friendly interface. It consists of:

- **main_window.py**: Main application window with notebook/tab-based interface
- **interface_panel.py**: Interface management panel (view, enable/disable, configure IP)
- **wifi_panel.py**: WiFi network scanning and connection management
- **dns_panel.py**: DNS server configuration
- **routing_panel.py**: Routing table viewing and modification

All GUI components communicate with the backend through the NetworkManager singleton.

### 2. Backend Layer (`bsd_netgui/backend/`)

The backend layer handles all system-level network operations:

- **network_manager.py**: Central coordinator using Singleton pattern, provides unified API
- **interface_handler.py**: Network interface operations (ifconfig)
- **wifi_handler.py**: WiFi operations (wpa_supplicant, ifconfig scan)
- **dns_handler.py**: DNS configuration (/etc/resolv.conf)
- **routing_handler.py**: Routing table operations (route, netstat)

### 3. Utils Layer (`bsd_netgui/utils/`)

Shared utilities and helper functions:

- **system_utils.py**: Command execution, privilege checking, validation, logging

## Code Organization

```
bsd-netgui/
├── bsd_netgui/           # Main package
│   ├── __init__.py       # Package initialization
│   ├── main.py           # Entry point
│   ├── gui/              # GUI components
│   ├── backend/          # Backend handlers
│   └── utils/            # Utilities
├── docs/                 # Documentation
├── README.md             # User documentation
├── LICENSE               # MIT License
├── requirements.txt      # Python dependencies
└── setup.py              # Package setup
```

## FreeBSD Networking Commands Reference

### ifconfig - Interface Configuration

Used for viewing and configuring network interfaces:

```bash
# List all interfaces
ifconfig -a

# View specific interface
ifconfig em0

# Enable interface
ifconfig em0 up

# Disable interface
ifconfig em0 down

# Configure static IP
ifconfig em0 inet 192.168.1.100 netmask 255.255.255.0

# Scan for WiFi networks
ifconfig wlan0 scan

# Connect to WiFi (open network)
ifconfig wlan0 ssid "NetworkName"
```

### dhclient - DHCP Client

Used for obtaining IP addresses via DHCP:

```bash
# Start DHCP client on interface
dhclient em0

# Release DHCP lease
dhclient -r em0

# Kill DHCP client
pkill -f "dhclient.*em0"
```

### wpa_supplicant - WiFi Authentication

Used for connecting to secured WiFi networks:

```bash
# Generate WPA configuration
wpa_passphrase "SSID" "password" > /etc/wpa_supplicant.conf

# Start wpa_supplicant
wpa_supplicant -B -i wlan0 -c /etc/wpa_supplicant.conf

# Kill wpa_supplicant
pkill -f "wpa_supplicant.*wlan0"
```

### route - Routing Table Management

Used for viewing and modifying routing tables:

```bash
# View routing table
netstat -rn

# Add default gateway
route add default 192.168.1.1

# Add network route
route add -net 10.0.0.0/24 192.168.1.1

# Delete route
route delete 10.0.0.0

# Delete default gateway
route delete default
```

### netstat - Network Statistics

Used for viewing routing tables and network statistics:

```bash
# View routing table
netstat -rn

# View interface statistics
netstat -i

# View active connections
netstat -an
```

## Key Configuration Files

### /etc/resolv.conf
DNS resolver configuration file. Contains nameserver entries:
```
nameserver 8.8.8.8
nameserver 8.8.4.4
```

### /etc/wpa_supplicant.conf
WiFi authentication configuration for wpa_supplicant:
```
network={
    ssid="MyNetwork"
    psk="password"
}
```

### /etc/rc.conf
FreeBSD system configuration file for persistent network settings:
```bash
# Interface configuration
ifconfig_em0="inet 192.168.1.100 netmask 255.255.255.0"
defaultrouter="192.168.1.1"

# DHCP configuration
ifconfig_em0="DHCP"

# WiFi configuration
wlans_ath0="wlan0"
ifconfig_wlan0="WPA DHCP"
```

**Note**: The current version of BSD Network Manager makes runtime changes only. Support for persistent configuration via /etc/rc.conf is planned for a future release.

## Testing Guidelines

### Requirements for Testing

- **Operating System**: FreeBSD or BSD-based system
- **Privileges**: Root/sudo access
- **Hardware**: Network interfaces (Ethernet and/or WiFi)

### Virtual Machine Setup

For development and testing, it's recommended to use a virtual machine:

1. **VirtualBox Setup**:
   ```bash
   # Download FreeBSD ISO
   # Create new VM with at least 2GB RAM
   # Install FreeBSD with default networking
   # Enable NAT and/or Bridged networking
   ```

2. **VMware Setup**:
   ```bash
   # Similar to VirtualBox
   # Use VMware Tools for better integration
   ```

3. **Install Dependencies**:
   ```bash
   # Install Python and pip
   pkg install python39 py39-pip py39-sqlite3

   # Install wxPython and dependencies
   pkg install py39-wxPython
   pip install netifaces psutil
   ```

### Manual Testing

Test each component individually:

1. **Interface Management**:
   - List interfaces
   - Enable/disable interface
   - Configure DHCP
   - Configure static IP

2. **WiFi Management** (if WiFi hardware available):
   - Scan for networks
   - Connect to open network
   - Connect to WPA2 network
   - Disconnect

3. **DNS Configuration**:
   - View current DNS servers
   - Add DNS server
   - Remove DNS server
   - Apply changes

4. **Routing**:
   - View routing table
   - Add route
   - Delete route
   - Add default gateway

### Automated Testing

Currently, automated testing is limited due to the requirement for root privileges and real network hardware. Consider:

- Mock testing for parser functions
- Integration tests in isolated VM
- Manual test checklist before releases

## Development Workflow

### Setting Up Development Environment

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/berkenar1/bsd-netgui.git
   cd bsd-netgui
   ```

2. Create virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # or activate.csh for csh
   ```

3. Install in development mode:
   ```bash
   pip install -e .
   ```

4. Run the application:
   ```bash
   sudo venv/bin/python -m bsd_netgui.main
   ```

### Making Changes

1. Create a feature branch:
   ```bash
   git checkout -b feature/my-feature
   ```

2. Make your changes following the coding standards

3. Test your changes thoroughly

4. Commit with descriptive messages:
   ```bash
   git commit -m "Add feature: description"
   ```

5. Push and create pull request:
   ```bash
   git push origin feature/my-feature
   ```

## Coding Standards

### Python Style Guidelines

Follow PEP 8 style guidelines:

- Use 4 spaces for indentation (no tabs)
- Maximum line length: 100 characters
- Use descriptive variable names
- Add blank lines between functions and classes

### Type Hints

Use Python type hints for all function signatures:

```python
def get_interface_details(self, iface: str) -> Optional[Dict]:
    """Get interface details."""
    pass
```

### Docstrings

Use Google-style docstrings for all classes and methods:

```python
def execute_command(cmd: List[str], timeout: int = 30) -> Tuple[bool, str, str]:
    """
    Execute a system command safely using subprocess.
    
    Args:
        cmd: Command and arguments as a list of strings
        timeout: Command timeout in seconds (default: 30)
    
    Returns:
        Tuple of (success, stdout, stderr)
    
    Example:
        >>> success, output, error = execute_command(['ls', '-la'])
    """
    pass
```

### Error Handling

- Use try-except blocks for all system operations
- Log errors appropriately
- Provide user-friendly error messages
- Don't catch exceptions without handling them

### Logging

Use Python's logging module throughout:

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")
```

### GUI Threading

When performing long-running operations in the GUI:

```python
import threading
import wx

def long_operation():
    # Perform operation
    result = do_something()
    # Update GUI using CallAfter
    wx.CallAfter(update_gui, result)

thread = threading.Thread(target=long_operation)
thread.daemon = True
thread.start()
```

## Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes following our coding standards
4. Test thoroughly on FreeBSD
5. Submit a pull request

### Pull Request Guidelines

- Provide clear description of changes
- Reference any related issues
- Include testing notes
- Update documentation as needed

## Future Enhancements

Planned features for future releases:

- [ ] Persistent configuration via /etc/rc.conf
- [ ] IPv6 support
- [ ] VLAN configuration
- [ ] Bridge configuration
- [ ] Firewall integration (pf)
- [ ] VPN configuration
- [ ] Network diagnostics (ping, traceroute)
- [ ] Traffic monitoring
- [ ] System tray integration
- [ ] Multi-language support

## Support

For issues and questions:

- GitHub Issues: https://github.com/berkenar1/bsd-netgui/issues
- Discussions: https://github.com/berkenar1/bsd-netgui/discussions

## License

BSD Network Manager is released under the MIT License. See LICENSE file for details.
