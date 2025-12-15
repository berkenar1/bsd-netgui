"""Main network manager that coordinates all backend handlers."""

import logging
from typing import Dict, Any
from .interface_handler import InterfaceHandler
from .wifi_handler import WiFiHandler
from .dns_handler import DNSHandler
from .routing_handler import RoutingHandler


class NetworkManager:
    """
    Main network manager coordinator using Singleton pattern.
    
    This class provides a unified interface to all network management
    functionality, coordinating between interface, WiFi, DNS, and routing
    handlers.
    """
    
    _instance = None
    
    def __new__(cls):
        """Implement Singleton pattern."""
        if cls._instance is None:
            cls._instance = super(NetworkManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the NetworkManager and all handlers."""
        if self._initialized:
            return
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing NetworkManager")
        
        # Initialize all handlers
        try:
            self.interface_handler = InterfaceHandler()
            self.wifi_handler = WiFiHandler()
            self.dns_handler = DNSHandler()
            self.routing_handler = RoutingHandler()
            
            self._initialized = True
            self.logger.info("NetworkManager initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize NetworkManager: {str(e)}")
            raise
    
    def get_all_status(self) -> Dict[str, Any]:
        """
        Get status of all network components.
        
        Returns:
            Dictionary containing:
            - interfaces: List of all interfaces
            - wifi_interfaces: List of WiFi interfaces
            - dns_servers: List of DNS servers
            - routes: Routing table
        """
        try:
            status = {
                'interfaces': self.interface_handler.list_interfaces(),
                'wifi_interfaces': self.wifi_handler.get_wifi_interfaces(),
                'dns_servers': self.dns_handler.get_dns_servers(),
                'routes': self.routing_handler.get_routing_table()
            }
            return status
        except Exception as e:
            self.logger.error(f"Error getting network status: {str(e)}")
            return {
                'interfaces': [],
                'wifi_interfaces': [],
                'dns_servers': [],
                'routes': []
            }
    
    def refresh_all(self) -> bool:
        """
        Refresh all network information.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Refreshing all network information")
            status = self.get_all_status()
            return True
        except Exception as e:
            self.logger.error(f"Error refreshing network information: {str(e)}")
            return False
    
    # Interface operations
    def list_interfaces(self):
        """Get all network interfaces."""
        return self.interface_handler.list_interfaces()
    
    def get_interface_details(self, iface: str):
        """Get details for a specific interface."""
        return self.interface_handler.get_interface_details(iface)
    
    def enable_interface(self, iface: str):
        """Enable a network interface."""
        return self.interface_handler.enable_interface(iface)
    
    def disable_interface(self, iface: str):
        """Disable a network interface."""
        return self.interface_handler.disable_interface(iface)
    
    def configure_dhcp(self, iface: str):
        """Configure interface to use DHCP."""
        return self.interface_handler.configure_dhcp(iface)
    
    def configure_static_ip(self, iface: str, ip: str, netmask: str, gateway: str = None):
        """Configure interface with static IP."""
        return self.interface_handler.configure_static_ip(iface, ip, netmask, gateway)
    
    # WiFi operations
    def get_wifi_interfaces(self):
        """Get all WiFi interfaces."""
        return self.wifi_handler.get_wifi_interfaces()
    
    def scan_networks(self, iface: str):
        """Scan for WiFi networks."""
        return self.wifi_handler.scan_networks(iface)
    
    def get_current_connection(self, iface: str):
        """Get current WiFi connection status."""
        return self.wifi_handler.get_current_connection(iface)
    
    def connect_network(self, iface: str, ssid: str, password: str = None, security: str = 'WPA2'):
        """Connect to a WiFi network."""
        return self.wifi_handler.connect_network(iface, ssid, password, security)
    
    def disconnect_network(self, iface: str):
        """Disconnect from WiFi network."""
        return self.wifi_handler.disconnect_network(iface)
    
    # DNS operations
    def get_dns_servers(self):
        """Get current DNS servers."""
        return self.dns_handler.get_dns_servers()
    
    def set_dns_servers(self, servers):
        """Set DNS servers."""
        return self.dns_handler.set_dns_servers(servers)
    
    def add_dns_server(self, server: str):
        """Add a DNS server."""
        return self.dns_handler.add_dns_server(server)
    
    def remove_dns_server(self, server: str):
        """Remove a DNS server."""
        return self.dns_handler.remove_dns_server(server)
    
    # Routing operations
    def get_routing_table(self):
        """Get the routing table."""
        return self.routing_handler.get_routing_table()
    
    def add_route(self, destination: str, gateway: str, netmask: str = None):
        """Add a route."""
        return self.routing_handler.add_route(destination, gateway, netmask)
    
    def delete_route(self, destination: str):
        """Delete a route."""
        return self.routing_handler.delete_route(destination)
    
    def add_default_gateway(self, gateway: str):
        """Add default gateway."""
        return self.routing_handler.add_default_gateway(gateway)
