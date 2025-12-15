# BSD Network Manager

A modern, user-friendly network manager GUI for FreeBSD and other BSD systems. Built with Python and wxPython, this tool provides an intuitive interface for managing network interfaces, WiFi connections, DNS settings, and routing tables.

![BSD Network Manager](docs/screenshot.png)
*Screenshot placeholder - GUI interface*

## Features

- **Interface Management**: View and manage all network interfaces (enable/disable, configure IP)
- **IP Configuration**: Easy setup for both DHCP and static IP addresses
- **WiFi Management**: Scan, connect, and manage wireless networks
- **DNS Configuration**: Add, remove, and manage DNS servers
- **Routing Table**: View and modify routing tables with an intuitive interface
- **Real-time Updates**: Live status monitoring of network connections
- **BSD-Native**: Uses FreeBSD's native networking tools (ifconfig, dhclient, wpa_supplicant, route)

## Requirements

- **Operating System**: FreeBSD or other BSD-based systems
- **Python**: Version 3.8 or higher
- **Privileges**: Root/sudo access (required for network management)
- **Dependencies**:
  - wxPython >= 4.2.0
  - netifaces >= 0.11.0
  - psutil >= 5.9.0

## Installation

### From Source

1. Clone the repository:
```bash
git clone https://github.com/berkenar1/bsd-netgui.git
cd bsd-netgui
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install the package:
```bash
sudo python setup.py install
```

### Using pip (when available)

```bash
pip install bsd-netgui
```

## Usage

**Important**: This application requires root privileges to manage network settings.

### Running the Application

```bash
sudo bsd-netgui
```

Or if you haven't installed it:

```bash
sudo python -m bsd_netgui.main
```

### Basic Operations

1. **Interface Management**: Go to the "Interfaces" tab to view all network interfaces. Select an interface to enable/disable it or configure IP settings.

2. **WiFi Networks**: Use the "WiFi" tab to scan for available networks and connect to them with proper credentials.

3. **DNS Settings**: Manage your DNS servers in the "DNS" tab. Add or remove DNS servers and apply changes.

4. **Routing**: View and modify routing tables in the "Routing" tab. Add or delete routes as needed.

## Development Setup

### Prerequisites

- FreeBSD system (or virtual machine)
- Python 3.8+
- Git

### Setting Up Development Environment

1. Clone the repository:
```bash
git clone https://github.com/berkenar1/bsd-netgui.git
cd bsd-netgui
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On FreeBSD/bash
```

3. Install dependencies in development mode:
```bash
pip install -r requirements.txt
pip install -e .
```

4. Run the application:
```bash
sudo venv/bin/python -m bsd_netgui.main
```

### Testing

This application requires a FreeBSD or BSD-based system with root access for testing. It's recommended to use a virtual machine (VirtualBox or VMware) with FreeBSD for development and testing.

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for more detailed development information.

## Architecture

The application is structured in three main layers:

- **GUI Layer** (`bsd_netgui/gui/`): wxPython-based user interface
- **Backend Layer** (`bsd_netgui/backend/`): Network management logic and system command execution
- **Utils Layer** (`bsd_netgui/utils/`): Shared utilities and helpers

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Guidelines

1. Follow PEP 8 style guidelines
2. Add docstrings to all functions and classes
3. Use type hints for function signatures
4. Test your changes on FreeBSD
5. Update documentation as needed

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

- **berkenar1** - [GitHub](https://github.com/berkenar1)

## Acknowledgments

- Built for the FreeBSD community
- Uses FreeBSD's native networking tools
- Inspired by the need for a modern GUI network manager for BSD systems

## Disclaimer

This tool modifies system network settings and requires root privileges. Use with caution and always ensure you have backup network access methods when making changes to network configurations.
