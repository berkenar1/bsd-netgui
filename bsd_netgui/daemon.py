#!/usr/bin/env python3
"""BSD Network Manager Daemon - Backend service with IPC interface."""

import os
import sys
import logging
import argparse
import signal
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from bsd_netgui.utils.system_utils import check_root_privileges, setup_logging
from bsd_netgui.backend.network_manager import NetworkManager
from bsd_netgui.ipc import IPCServer


def create_request_handler(network_manager):
    """Create a request handler for the IPC server."""

    def handle_request(request):
        """Handle incoming requests from CLI clients."""
        try:
            action = request.get("action")
            params = request.get("params", {})

            if action == "get_status":
                return {"success": True, "data": network_manager.get_all_status()}

            elif action == "get_interfaces":
                interfaces = network_manager.interface_handler.list_interfaces()
                return {"success": True, "data": interfaces}

            elif action == "get_wifi_interfaces":
                wifi = network_manager.wifi_handler.get_wifi_interfaces()
                return {"success": True, "data": wifi}

            elif action == "get_dns":
                dns = network_manager.dns_handler.get_dns_servers()
                return {"success": True, "data": dns}

            elif action == "get_routes":
                routes = network_manager.routing_handler.get_routing_table()
                return {"success": True, "data": routes}

            elif action == "set_interface_ip":
                iface = params.get("interface")
                ip = params.get("ip")
                if iface and ip:
                    network_manager.interface_handler.set_interface_ip(iface, ip)
                    return {"success": True}
                return {"success": False, "error": "Missing interface or ip"}

            elif action == "enable_interface":
                iface = params.get("interface")
                if iface:
                    network_manager.interface_handler.enable_interface(iface)
                    return {"success": True}
                return {"success": False, "error": "Missing interface"}

            elif action == "disable_interface":
                iface = params.get("interface")
                if iface:
                    network_manager.interface_handler.disable_interface(iface)
                    return {"success": True}
                return {"success": False, "error": "Missing interface"}

            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    return handle_request


def main():
    """Main daemon entry point."""
    parser = argparse.ArgumentParser(description="BSD Network Manager Daemon")
    parser.add_argument(
        "--socket",
        default="/var/run/bsd-netgui.sock",
        help="Unix socket path (default: /var/run/bsd-netgui.sock)",
    )
    parser.add_argument(
        "--loglevel",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )
    parser.add_argument(
        "--nodaemon",
        action="store_true",
        help="Run in foreground (don't daemonize)",
    )

    args = parser.parse_args()

    # Check root privileges
    if not check_root_privileges():
        print("Error: This daemon requires root privileges", file=sys.stderr)
        sys.exit(1)

    # Setup logging
    setup_logging(args.loglevel)
    logger = logging.getLogger(__name__)

    logger.info("Starting BSD Network Manager Daemon")
    logger.info(f"IPC socket: {args.socket}")

    # Initialize network manager
    try:
        network_manager = NetworkManager()
        logger.info("Network manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize network manager: {e}")
        sys.exit(1)

    # Initialize IPC server
    ipc_server = IPCServer(socket_path=args.socket)
    ipc_server.set_request_handler(create_request_handler(network_manager))

    # Signal handlers
    def signal_handler(signum, frame):
        logger.info("Received signal, shutting down...")
        ipc_server.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start IPC server
        ipc_server.start()
        logger.info("IPC server started and waiting for connections")

        # Keep daemon running
        signal.pause()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Daemon error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        ipc_server.stop()
        logger.info("Daemon stopped")


if __name__ == "__main__":
    main()
