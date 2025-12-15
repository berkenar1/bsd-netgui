"""Interface handler for managing network interfaces on FreeBSD."""

import re
import logging
from typing import List, Dict, Optional
from ..utils.system_utils import execute_command


class InterfaceHandler:
    """
    Handles network interface operations using FreeBSD's ifconfig command.
    
    This class provides methods to list, configure, enable, and disable
    network interfaces on FreeBSD systems.
    """
    
    def __init__(self):
        """Initialize the InterfaceHandler."""
        self.logger = logging.getLogger(__name__)
    
    def list_interfaces(self) -> List[Dict]:
        """
        Get all network interfaces using ifconfig -a.
        
        Returns:
            List of dictionaries containing interface information:
            - name: Interface name
            - status: up/down
            - ipv4: IPv4 address (if configured)
            - netmask: Network mask (if configured)
            - mac: MAC address
            - mtu: MTU value
        
        Example:
            >>> handler = InterfaceHandler()
            >>> interfaces = handler.list_interfaces()
        """
        success, stdout, stderr = execute_command(['ifconfig', '-a'])
        
        if not success:
            self.logger.error(f"Failed to list interfaces: {stderr}")
            return []
        
        return self._parse_ifconfig_output(stdout)
    
    def get_interface_details(self, iface: str) -> Optional[Dict]:
        """
        Get detailed information for a specific interface.
        
        Args:
            iface: Interface name (e.g., 'em0', 'wlan0')
        
        Returns:
            Dictionary with interface details or None if interface not found
        """
        success, stdout, stderr = execute_command(['ifconfig', iface])
        
        if not success:
            self.logger.error(f"Failed to get interface details for {iface}: {stderr}")
            return None
        
        interfaces = self._parse_ifconfig_output(stdout)
        return interfaces[0] if interfaces else None
    
    def enable_interface(self, iface: str) -> bool:
        """
        Enable (bring up) a network interface.
        
        Args:
            iface: Interface name
        
        Returns:
            True if successful, False otherwise
        
        Note:
            Executes: ifconfig {iface} up
        """
        success, stdout, stderr = execute_command(['ifconfig', iface, 'up'])
        
        if not success:
            self.logger.error(f"Failed to enable interface {iface}: {stderr}")
            return False
        
        self.logger.info(f"Interface {iface} enabled successfully")
        return True
    
    def disable_interface(self, iface: str) -> bool:
        """
        Disable (bring down) a network interface.
        
        Args:
            iface: Interface name
        
        Returns:
            True if successful, False otherwise
        
        Note:
            Executes: ifconfig {iface} down
        """
        success, stdout, stderr = execute_command(['ifconfig', iface, 'down'])
        
        if not success:
            self.logger.error(f"Failed to disable interface {iface}: {stderr}")
            return False
        
        self.logger.info(f"Interface {iface} disabled successfully")
        return True
    
    def configure_dhcp(self, iface: str) -> bool:
        """
        Configure interface to use DHCP for IP address.
        
        Args:
            iface: Interface name
        
        Returns:
            True if successful, False otherwise
        
        Note:
            Executes: dhclient {iface}
        """
        # First, kill any existing dhclient for this interface
        execute_command(['pkill', '-f', f'dhclient.*{iface}'])
        
        # Start dhclient for the interface
        success, stdout, stderr = execute_command(['dhclient', iface], timeout=60)
        
        if not success:
            self.logger.error(f"Failed to configure DHCP for {iface}: {stderr}")
            return False
        
        self.logger.info(f"DHCP configured successfully for {iface}")
        return True
    
    def configure_static_ip(self, iface: str, ip: str, netmask: str, gateway: str = None) -> bool:
        """
        Configure interface with static IP address.
        
        Args:
            iface: Interface name
            ip: IPv4 address
            netmask: Network mask (e.g., "255.255.255.0")
            gateway: Default gateway (optional)
        
        Returns:
            True if successful, False otherwise
        
        Note:
            Executes: ifconfig {iface} inet {ip} netmask {netmask}
            If gateway provided: route add default {gateway}
        """
        # Configure the IP address and netmask
        success, stdout, stderr = execute_command([
            'ifconfig', iface, 'inet', ip, 'netmask', netmask
        ])
        
        if not success:
            self.logger.error(f"Failed to configure static IP for {iface}: {stderr}")
            return False
        
        self.logger.info(f"Static IP {ip} configured for {iface}")
        
        # Configure default gateway if provided
        if gateway:
            # First, try to delete existing default route (may fail if none exists)
            execute_command(['route', 'delete', 'default'])
            
            # Add the new default gateway
            success, stdout, stderr = execute_command([
                'route', 'add', 'default', gateway
            ])
            
            if not success:
                self.logger.warning(f"Failed to set default gateway {gateway}: {stderr}")
                # Don't return False here - IP is configured, just gateway failed
            else:
                self.logger.info(f"Default gateway set to {gateway}")
        
        return True
    
    def _parse_ifconfig_output(self, output: str) -> List[Dict]:
        """
        Parse ifconfig output and extract interface information.
        
        Args:
            output: Output string from ifconfig command
        
        Returns:
            List of dictionaries with interface information
        """
        interfaces = []
        current_iface = None
        
        for line in output.split('\n'):
            # Check if this is the start of a new interface
            if line and not line.startswith('\t') and ':' in line:
                # Save previous interface if exists
                if current_iface:
                    interfaces.append(current_iface)
                
                # Parse interface name and flags
                match = re.match(r'^(\S+):\s+flags=([^<]*)<([^>]+)>', line)
                if match:
                    iface_name = match.group(1)
                    flags = match.group(3)
                    
                    current_iface = {
                        'name': iface_name,
                        'status': 'up' if 'UP' in flags else 'down',
                        'ipv4': '',
                        'netmask': '',
                        'mac': '',
                        'mtu': '',
                        'flags': flags
                    }
                    
                    # Extract MTU if present in the same line
                    mtu_match = re.search(r'mtu\s+(\d+)', line)
                    if mtu_match:
                        current_iface['mtu'] = mtu_match.group(1)
            
            elif current_iface and line.strip():
                # Parse additional interface information
                line = line.strip()
                
                # IPv4 address
                if line.startswith('inet '):
                    inet_match = re.search(r'inet\s+(\S+)\s+netmask\s+(\S+)', line)
                    if inet_match:
                        current_iface['ipv4'] = inet_match.group(1)
                        # Convert hex netmask to dotted decimal
                        netmask_hex = inet_match.group(2)
                        if netmask_hex.startswith('0x'):
                            try:
                                netmask_int = int(netmask_hex, 16)
                                netmask_parts = [
                                    str((netmask_int >> 24) & 0xff),
                                    str((netmask_int >> 16) & 0xff),
                                    str((netmask_int >> 8) & 0xff),
                                    str(netmask_int & 0xff)
                                ]
                                current_iface['netmask'] = '.'.join(netmask_parts)
                            except ValueError:
                                current_iface['netmask'] = netmask_hex
                        else:
                            current_iface['netmask'] = netmask_hex
                
                # MAC address (ether)
                elif line.startswith('ether '):
                    ether_match = re.search(r'ether\s+(\S+)', line)
                    if ether_match:
                        current_iface['mac'] = ether_match.group(1)
        
        # Don't forget the last interface
        if current_iface:
            interfaces.append(current_iface)
        
        return interfaces
