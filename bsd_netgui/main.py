"""Main entry point for BSD Network Manager - Backend CLI."""

import sys
import argparse
import logging
import json
from .utils.system_utils import check_root_privileges, setup_logging
from .backend.network_manager import NetworkManager


def show_status(network_manager):
    """Display current network status."""
    status = network_manager.get_all_status()
    print("\n=== Network Status ===")
    print(json.dumps(status, indent=2))


def show_interfaces(network_manager):
    """List all network interfaces."""
    interfaces = network_manager.interface_handler.list_interfaces()
    print("\n=== Network Interfaces ===")
    for iface in interfaces:
        print(f"  {iface}")


def show_wifi(network_manager):
    """List WiFi interfaces."""
    wifi_ifaces = network_manager.wifi_handler.get_wifi_interfaces()
    print("\n=== WiFi Interfaces ===")
    for iface in wifi_ifaces:
        print(f"  {iface}")


def show_dns(network_manager):
    """Show DNS configuration."""
    dns_servers = network_manager.dns_handler.get_dns_servers()
    print("\n=== DNS Servers ===")
    for server in dns_servers:
        print(f"  {server}")


def show_routes(network_manager):
    """Show routing table."""
    routes = network_manager.routing_handler.get_routing_table()
    print("\n=== Routing Table ===")
    print(json.dumps(routes, indent=2))


def main():
    """
    Main entry point for the backend CLI application.
    
    This function:
    1. Sets up logging
    2. Checks for root privileges
    3. Parses command-line arguments
    4. Executes requested operations
    """
    # Setup logging
    try:
        setup_logging()
    except Exception as e:
        print(f"Warning: Could not setup file logging: {e}")
        logging.basicConfig(level=logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting BSD Network Manager (Backend)")
    
    # Check for root privileges
    if not check_root_privileges():
        logger.error("Root privileges required")
        print("Error: BSD Network Manager requires root privileges to manage network settings.")
        print("Please run with sudo: sudo bsd-netgui")
        return 1
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="BSD Network Manager - Backend CLI Interface",
        prog="bsd-netgui"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    subparsers.add_parser('status', help='Show complete network status')
    subparsers.add_parser('interfaces', help='List network interfaces')
    subparsers.add_parser('wifi', help='Show WiFi interfaces')
    subparsers.add_parser('dns', help='Show DNS configuration')
    subparsers.add_parser('routes', help='Show routing table')
    
    args = parser.parse_args()
    
    # Initialize network manager
    try:
        network_manager = NetworkManager()
        logger.info("NetworkManager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize NetworkManager: {e}", exc_info=True)
        print(f"Error: Failed to initialize network manager: {e}")
        return 1
    
    # Handle commands
    if not args.command:
        parser.print_help()
        return 0
    
    try:
        if args.command == 'status':
            show_status(network_manager)
        elif args.command == 'interfaces':
            show_interfaces(network_manager)
        elif args.command == 'wifi':
            show_wifi(network_manager)
        elif args.command == 'dns':
            show_dns(network_manager)
        elif args.command == 'routes':
            show_routes(network_manager)
        else:
            parser.print_help()
            return 1
        
        return 0
    
    except Exception as e:
        logger.error(f"Error executing command: {e}", exc_info=True)
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
