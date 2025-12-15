"""Routing handler for managing routing tables on FreeBSD."""

import re
import logging
from typing import List, Dict
from ..utils.system_utils import execute_command


class RoutingHandler:
    """
    Handles routing table operations using FreeBSD's route and netstat commands.
    
    This class provides methods to view, add, and delete routes in the
    system routing table.
    """
    
    def __init__(self):
        """Initialize the RoutingHandler."""
        self.logger = logging.getLogger(__name__)
    
    def get_routing_table(self) -> List[Dict]:
        """
        Get the current routing table using netstat -rn.
        
        Returns:
            List of dictionaries containing route information:
            - destination: Destination network/host
            - gateway: Gateway address
            - flags: Route flags
            - netmask: Network mask (if applicable)
            - interface: Network interface
            - metric: Route metric (if available)
        
        Note:
            Executes: netstat -rn
        """
        success, stdout, stderr = execute_command(['netstat', '-rn'])
        
        if not success:
            self.logger.error(f"Failed to get routing table: {stderr}")
            return []
        
        return self._parse_netstat_output(stdout)
    
    def add_route(self, destination: str, gateway: str, netmask: str = None) -> bool:
        """
        Add a route to the routing table.
        
        Args:
            destination: Destination network/host
            gateway: Gateway address
            netmask: Network mask (optional, for network routes)
        
        Returns:
            True if successful, False otherwise
        
        Note:
            For network routes: route add -net {destination}/{netmask} {gateway}
            For host routes: route add {destination} {gateway}
        """
        try:
            cmd = ['route', 'add']
            
            if netmask:
                # Network route
                # Convert netmask to CIDR prefix if it's in dotted decimal
                if '.' in netmask:
                    prefix = self._netmask_to_prefix(netmask)
                else:
                    prefix = netmask
                
                cmd.extend(['-net', f"{destination}/{prefix}", gateway])
            else:
                # Host route
                cmd.extend([destination, gateway])
            
            success, stdout, stderr = execute_command(cmd)
            
            if not success:
                self.logger.error(f"Failed to add route: {stderr}")
                return False
            
            self.logger.info(f"Route added successfully: {destination} via {gateway}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding route: {str(e)}")
            return False
    
    def delete_route(self, destination: str) -> bool:
        """
        Delete a route from the routing table.
        
        Args:
            destination: Destination network/host to remove
        
        Returns:
            True if successful, False otherwise
        
        Note:
            Executes: route delete {destination}
        """
        success, stdout, stderr = execute_command(['route', 'delete', destination])
        
        if not success:
            self.logger.error(f"Failed to delete route {destination}: {stderr}")
            return False
        
        self.logger.info(f"Route deleted successfully: {destination}")
        return True
    
    def add_default_gateway(self, gateway: str) -> bool:
        """
        Add or change the default gateway.
        
        Args:
            gateway: Gateway IP address
        
        Returns:
            True if successful, False otherwise
        
        Note:
            Executes: route delete default (if exists), then route add default {gateway}
        """
        # Try to delete existing default route (may fail if none exists)
        execute_command(['route', 'delete', 'default'])
        
        # Add new default gateway
        success, stdout, stderr = execute_command(['route', 'add', 'default', gateway])
        
        if not success:
            self.logger.error(f"Failed to add default gateway {gateway}: {stderr}")
            return False
        
        self.logger.info(f"Default gateway set to {gateway}")
        return True
    
    def _parse_netstat_output(self, output: str) -> List[Dict]:
        """
        Parse netstat -rn output and extract routing information.
        
        Args:
            output: Output from netstat -rn command
        
        Returns:
            List of route dictionaries
        """
        routes = []
        in_routing_table = False
        
        for line in output.split('\n'):
            line = line.strip()
            
            # Look for the routing table section
            if 'Routing tables' in line or 'Destination' in line:
                in_routing_table = True
                continue
            
            if not in_routing_table or not line:
                continue
            
            # Skip header lines
            if line.startswith('Internet') or line.startswith('Destination'):
                continue
            
            # Parse route line
            # Format varies, but typically: Destination Gateway Flags Netif Expire
            # or: Destination Gateway Flags Refs Use Netif Expire
            parts = line.split()
            
            if len(parts) >= 4:
                route = {
                    'destination': parts[0],
                    'gateway': parts[1],
                    'flags': parts[2],
                    'netmask': '',
                    'interface': parts[3] if len(parts) > 3 else '',
                    'metric': parts[4] if len(parts) > 4 and parts[4].isdigit() else '0'
                }
                
                # Try to find the interface name (usually the last or second to last column)
                for part in reversed(parts[3:]):
                    if not part.isdigit() and part != '-':
                        route['interface'] = part
                        break
                
                routes.append(route)
        
        return routes
    
    def _netmask_to_prefix(self, netmask: str) -> str:
        """
        Convert dotted decimal netmask to CIDR prefix length.
        
        Args:
            netmask: Netmask in dotted decimal format (e.g., "255.255.255.0")
        
        Returns:
            CIDR prefix length as string (e.g., "24")
        """
        try:
            # Split netmask into octets
            octets = netmask.split('.')
            if len(octets) != 4:
                return "32"  # Default to /32 if invalid
            
            # Convert to binary and count 1s
            binary = ''.join([bin(int(octet))[2:].zfill(8) for octet in octets])
            prefix_length = binary.count('1')
            
            return str(prefix_length)
        except (ValueError, AttributeError):
            self.logger.warning(f"Invalid netmask format: {netmask}, defaulting to /32")
            return "32"
