#!/usr/bin/env python3
"""BSD Network Manager CLI - Test client for daemon communication."""

import sys
import argparse
import json
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from bsd_netgui.ipc import IPCClient
from bsd_netgui.utils.system_utils import setup_logging


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="BSD Network Manager CLI - Test client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s status                           # Show network status
  %(prog)s interfaces                       # List interfaces
  %(prog)s wifi                             # List WiFi interfaces
  %(prog)s dns                              # Show DNS servers
  %(prog)s routes                           # Show routing table
  %(prog)s set-ip eth0 192.168.1.100      # Set interface IP
  %(prog)s enable eth0                      # Enable interface
  %(prog)s disable eth0                     # Disable interface
        """,
    )

    parser.add_argument(
        "--socket",
        default="/var/run/bsd-netgui.sock",
        help="Unix socket path (default: /var/run/bsd-netgui.sock)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Status command
    subparsers.add_parser("status", help="Show network status")

    # Interfaces command
    subparsers.add_parser("interfaces", help="List network interfaces")

    # WiFi command
    subparsers.add_parser("wifi", help="List WiFi interfaces")

    # DNS command
    subparsers.add_parser("dns", help="Show DNS servers")

    # Routes command
    subparsers.add_parser("routes", help="Show routing table")

    # Set IP command
    set_ip_parser = subparsers.add_parser("set-ip", help="Set interface IP")
    set_ip_parser.add_argument("interface", help="Interface name")
    set_ip_parser.add_argument("ip", help="IP address")

    # Enable interface command
    enable_parser = subparsers.add_parser("enable", help="Enable interface")
    enable_parser.add_argument("interface", help="Interface name")

    # Disable interface command
    disable_parser = subparsers.add_parser("disable", help="Disable interface")
    disable_parser.add_argument("interface", help="Interface name")

    args = parser.parse_args()

    if args.verbose:
        setup_logging("DEBUG")
    else:
        setup_logging("WARNING")

    # Create IPC client
    client = IPCClient(socket_path=args.socket)

    # Map commands to requests
    if args.command == "status":
        response = client.send_request({"action": "get_status"})

    elif args.command == "interfaces":
        response = client.send_request({"action": "get_interfaces"})

    elif args.command == "wifi":
        response = client.send_request({"action": "get_wifi_interfaces"})

    elif args.command == "dns":
        response = client.send_request({"action": "get_dns"})

    elif args.command == "routes":
        response = client.send_request({"action": "get_routes"})

    elif args.command == "set-ip":
        response = client.send_request(
            {
                "action": "set_interface_ip",
                "params": {"interface": args.interface, "ip": args.ip},
            }
        )

    elif args.command == "enable":
        response = client.send_request(
            {"action": "enable_interface", "params": {"interface": args.interface}}
        )

    elif args.command == "disable":
        response = client.send_request(
            {"action": "disable_interface", "params": {"interface": args.interface}}
        )

    else:
        parser.print_help()
        sys.exit(1)

    # Display response
    if response.get("success"):
        if "data" in response:
            print(json.dumps(response["data"], indent=2))
        else:
            print("✓ Command executed successfully")
    else:
        error = response.get("error", "Unknown error")
        print(f"✗ Error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
