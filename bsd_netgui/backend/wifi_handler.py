"""WiFi handler for managing wireless networks on FreeBSD."""

import re
import logging
import os
from typing import List, Dict, Optional
from ..utils.system_utils import execute_command


class WiFiHandler:
    """
    Handles WiFi operations using FreeBSD's ifconfig and wpa_supplicant.
    
    This class provides methods to scan for networks, connect to WiFi,
    and manage wireless connections on FreeBSD systems.
    """
    
    def __init__(self):
        """Initialize the WiFiHandler."""
        self.logger = logging.getLogger(__name__)
        self.wpa_conf = "/etc/wpa_supplicant.conf"
    
    def get_wifi_interfaces(self) -> List[str]:
        """
        Find all WiFi interfaces on the system.
        
        Returns:
            List of wireless interface names
        
        Note:
            On FreeBSD, WiFi interfaces typically start with 'wlan'
        """
        success, stdout, stderr = execute_command(['ifconfig', '-a'])
        
        if not success:
            self.logger.error(f"Failed to list interfaces: {stderr}")
            return []
        
        wifi_interfaces = []
        for line in stdout.split('\n'):
            # Look for wlan interfaces
            if line and not line.startswith('\t'):
                match = re.match(r'^(wlan\d+):', line)
                if match:
                    wifi_interfaces.append(match.group(1))
        
        return wifi_interfaces
    
    def scan_networks(self, iface: str) -> List[Dict]:
        """
        Scan for available WiFi networks.
        
        Args:
            iface: WiFi interface name (e.g., 'wlan0')
        
        Returns:
            List of dictionaries containing network information:
            - ssid: Network name
            - bssid: MAC address of access point
            - signal: Signal strength (dBm)
            - channel: WiFi channel
            - security: Security type (e.g., WPA2, WEP, Open)
        
        Note:
            Executes: ifconfig {iface} scan
        """
        # First, bring the interface up if it's down
        execute_command(['ifconfig', iface, 'up'])
        
        # Perform the scan
        success, stdout, stderr = execute_command(['ifconfig', iface, 'scan'], timeout=60)
        
        if not success:
            self.logger.error(f"Failed to scan networks on {iface}: {stderr}")
            return []
        
        return self._parse_scan_output(stdout)
    
    def get_current_connection(self, iface: str) -> Optional[Dict]:
        """
        Get current WiFi connection status.
        
        Args:
            iface: WiFi interface name
        
        Returns:
            Dictionary with connection info or None if not connected
            - ssid: Connected network name
            - bssid: Access point MAC address
            - signal: Current signal strength
        """
        success, stdout, stderr = execute_command(['ifconfig', iface])
        
        if not success:
            self.logger.error(f"Failed to get WiFi status for {iface}: {stderr}")
            return None
        
        # Parse the output for ssid and status
        connection_info = {}
        
        for line in stdout.split('\n'):
            # Look for ssid
            ssid_match = re.search(r'ssid\s+([^\s]+)', line)
            if ssid_match:
                connection_info['ssid'] = ssid_match.group(1)
            
            # Look for status
            if 'status:' in line:
                status_match = re.search(r'status:\s+(\w+)', line)
                if status_match:
                    status = status_match.group(1)
                    if status != 'associated':
                        return None  # Not connected
        
        return connection_info if connection_info else None
    
    def connect_network(self, iface: str, ssid: str, password: str = None, security: str = 'WPA2') -> bool:
        """
        Connect to a WiFi network.
        
        Args:
            iface: WiFi interface name
            ssid: Network SSID to connect to
            password: Network password (None for open networks)
            security: Security type ('Open', 'WEP', 'WPA', 'WPA2')
        
        Returns:
            True if successful, False otherwise
        
        Note:
            Creates/updates wpa_supplicant.conf and starts wpa_supplicant
        """
        try:
            # For open networks
            if security == 'Open' or not password:
                success, stdout, stderr = execute_command([
                    'ifconfig', iface, 'ssid', ssid
                ])
                if not success:
                    self.logger.error(f"Failed to connect to open network: {stderr}")
                    return False
                
                self.logger.info(f"Connected to open network {ssid}")
                return True
            
            # For secured networks, use wpa_supplicant
            # Generate wpa_supplicant.conf entry
            if not self._update_wpa_supplicant_conf(ssid, password, security):
                return False
            
            # Kill any existing wpa_supplicant for this interface
            execute_command(['pkill', '-f', f'wpa_supplicant.*{iface}'])
            
            # Start wpa_supplicant
            success, stdout, stderr = execute_command([
                'wpa_supplicant', '-B', '-i', iface, '-c', self.wpa_conf
            ], timeout=30)
            
            if not success:
                self.logger.error(f"Failed to start wpa_supplicant: {stderr}")
                return False
            
            self.logger.info(f"Connected to network {ssid}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error connecting to network: {str(e)}")
            return False
    
    def disconnect_network(self, iface: str) -> bool:
        """
        Disconnect from current WiFi network.
        
        Args:
            iface: WiFi interface name
        
        Returns:
            True if successful, False otherwise
        """
        # Kill wpa_supplicant
        execute_command(['pkill', '-f', f'wpa_supplicant.*{iface}'])
        
        # Bring interface down and up to clear connection
        execute_command(['ifconfig', iface, 'down'])
        success, stdout, stderr = execute_command(['ifconfig', iface, 'up'])
        
        if not success:
            self.logger.error(f"Failed to disconnect from network: {stderr}")
            return False
        
        self.logger.info(f"Disconnected from network on {iface}")
        return True
    
    def _parse_scan_output(self, output: str) -> List[Dict]:
        """
        Parse ifconfig scan output.
        
        Args:
            output: Output from ifconfig scan command
        
        Returns:
            List of network dictionaries
        """
        networks = []
        
        for line in output.split('\n'):
            if not line.strip() or line.startswith('SSID'):
                continue
            
            # Parse scan results
            # Format: SSID/MESH ID    BSSID              CHAN RATE   S:N     INT CAPS
            parts = line.split()
            if len(parts) >= 3:
                network = {
                    'ssid': parts[0],
                    'bssid': parts[1] if len(parts) > 1 else '',
                    'channel': parts[2] if len(parts) > 2 else '',
                    'signal': parts[4] if len(parts) > 4 else '',
                    'security': self._determine_security(line)
                }
                networks.append(network)
        
        return networks
    
    def _determine_security(self, scan_line: str) -> str:
        """
        Determine security type from scan output line.
        
        Args:
            scan_line: Single line from scan output
        
        Returns:
            Security type string
        """
        if 'WPA2' in scan_line or 'RSN' in scan_line:
            return 'WPA2'
        elif 'WPA' in scan_line:
            return 'WPA'
        elif 'WEP' in scan_line:
            return 'WEP'
        else:
            return 'Open'
    
    def _update_wpa_supplicant_conf(self, ssid: str, password: str, security: str) -> bool:
        """
        Update wpa_supplicant.conf with network configuration.
        
        Args:
            ssid: Network SSID
            password: Network password
            security: Security type
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate network configuration
            if security in ['WPA', 'WPA2']:
                # Use wpa_passphrase to generate PSK
                success, stdout, stderr = execute_command([
                    'wpa_passphrase', ssid, password
                ])
                
                if not success:
                    self.logger.error(f"Failed to generate WPA config: {stderr}")
                    return False
                
                network_config = stdout
            else:
                # For WEP
                network_config = f'''network={{
    ssid="{ssid}"
    key_mgmt=NONE
    wep_key0="{password}"
    wep_tx_keyidx=0
}}
'''
            
            # Backup existing config if it exists
            if os.path.exists(self.wpa_conf):
                execute_command(['cp', self.wpa_conf, f"{self.wpa_conf}.backup"])
            
            # Write new configuration
            with open(self.wpa_conf, 'w') as f:
                f.write(network_config)
            
            self.logger.info(f"Updated wpa_supplicant.conf for {ssid}")
            return True
            
        except (IOError, PermissionError) as e:
            self.logger.error(f"Failed to update wpa_supplicant.conf: {str(e)}")
            return False
