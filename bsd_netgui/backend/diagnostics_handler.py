"""Network diagnostics collection and testing.

This module provides network diagnostic information and connectivity tests
for troubleshooting.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from ..utils.system_utils import execute_command


class DiagnosticsHandler:
    """
    Collects and formats network diagnostic information.
    
    Features:
    - Interface status
    - Routing table
    - DNS configuration
    - Connectivity tests (gateway, external, DNS)
    - ARP table
    - Active connections
    - WiFi signal strength
    """
    
    def __init__(self):
        """Initialize the DiagnosticsHandler."""
        self.logger = logging.getLogger(__name__)
    
    def get_interface_status(self) -> str:
        """
        Get current ifconfig output for all interfaces.
        
        Returns:
            ifconfig output as string
        """
        try:
            success, stdout, stderr = execute_command(['ifconfig', '-a'])
            if success:
                return stdout
            else:
                return f"Error: {stderr}"
        except Exception as e:
            self.logger.error(f"Error getting interface status: {e}")
            return f"Error: {str(e)}"
    
    def get_routing_table(self) -> str:
        """
        Get current routing table.
        
        Returns:
            Routing table as string
        """
        try:
            # Try netstat first
            success, stdout, stderr = execute_command(['netstat', '-rn'])
            if success:
                return stdout
            
            # Try route as fallback
            success, stdout, stderr = execute_command(['route', '-n', 'show'])
            if success:
                return stdout
            
            return f"Error: {stderr}"
        except Exception as e:
            self.logger.error(f"Error getting routing table: {e}")
            return f"Error: {str(e)}"
    
    def get_dns_config(self) -> str:
        """
        Get DNS configuration from resolv.conf.
        
        Returns:
            DNS configuration as string
        """
        try:
            with open('/etc/resolv.conf', 'r') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Error reading resolv.conf: {e}")
            return f"Error: {str(e)}"
    
    def get_default_gateway(self) -> Optional[str]:
        """
        Get the default gateway IP address.
        
        Returns:
            Gateway IP or None
        """
        try:
            success, stdout, stderr = execute_command(['netstat', '-rn'])
            if not success:
                return None
            
            # Parse routing table for default gateway
            for line in stdout.split('\n'):
                # Look for default route (0.0.0.0 or "default")
                if line.startswith('default') or line.startswith('0.0.0.0'):
                    parts = line.split()
                    if len(parts) >= 2:
                        return parts[1]
            
            return None
        except Exception as e:
            self.logger.error(f"Error getting default gateway: {e}")
            return None
    
    def ping_host(self, host: str, count: int = 3, timeout: int = 5) -> Tuple[bool, str]:
        """
        Ping a host to test connectivity.
        
        Args:
            host: Hostname or IP address
            count: Number of ping packets
            timeout: Timeout in seconds
        
        Returns:
            Tuple of (success, output)
        """
        try:
            success, stdout, stderr = execute_command(
                ['ping', '-c', str(count), '-W', str(timeout), host],
                timeout=timeout + 5
            )
            
            output = stdout + stderr
            return success, output
        except Exception as e:
            self.logger.error(f"Error pinging {host}: {e}")
            return False, f"Error: {str(e)}"
    
    def test_gateway_connectivity(self) -> Dict[str, Any]:
        """
        Test connectivity to default gateway.
        
        Returns:
            Dictionary with test results
        """
        gateway = self.get_default_gateway()
        
        if not gateway:
            return {
                'status': 'error',
                'message': 'No default gateway configured',
                'gateway': None
            }
        
        success, output = self.ping_host(gateway, count=3)
        
        return {
            'status': 'success' if success else 'failure',
            'message': 'Gateway is reachable' if success else 'Gateway is unreachable',
            'gateway': gateway,
            'output': output
        }
    
    def test_external_connectivity(self) -> Dict[str, Any]:
        """
        Test connectivity to external host (8.8.8.8).
        
        Returns:
            Dictionary with test results
        """
        external_ip = '8.8.8.8'
        success, output = self.ping_host(external_ip, count=3)
        
        return {
            'status': 'success' if success else 'failure',
            'message': 'External connectivity OK' if success else 'Cannot reach external hosts',
            'host': external_ip,
            'output': output
        }
    
    def test_dns_resolution(self, hostname: str = 'cloudflare.com') -> Dict[str, Any]:
        """
        Test DNS resolution.
        
        Args:
            hostname: Hostname to resolve
        
        Returns:
            Dictionary with test results
        """
        try:
            # Try nslookup first
            success, stdout, stderr = execute_command(['nslookup', hostname], timeout=10)
            
            if success:
                return {
                    'status': 'success',
                    'message': f'DNS resolution working for {hostname}',
                    'hostname': hostname,
                    'output': stdout
                }
            
            # Try host as fallback
            success, stdout, stderr = execute_command(['host', hostname], timeout=10)
            
            if success:
                return {
                    'status': 'success',
                    'message': f'DNS resolution working for {hostname}',
                    'hostname': hostname,
                    'output': stdout
                }
            
            return {
                'status': 'failure',
                'message': 'DNS resolution failed',
                'hostname': hostname,
                'output': stderr
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error testing DNS: {str(e)}',
                'hostname': hostname,
                'output': ''
            }
    
    def get_arp_table(self) -> str:
        """
        Get ARP table.
        
        Returns:
            ARP table as string
        """
        try:
            success, stdout, stderr = execute_command(['arp', '-a'])
            if success:
                return stdout
            return f"Error: {stderr}"
        except Exception as e:
            self.logger.error(f"Error getting ARP table: {e}")
            return f"Error: {str(e)}"
    
    def get_active_connections(self) -> str:
        """
        Get active network connections.
        
        Returns:
            Connection list as string
        """
        try:
            # Try sockstat (BSD-specific)
            success, stdout, stderr = execute_command(['sockstat', '-4', '-6'])
            if success:
                return stdout
            
            # Fallback to netstat
            success, stdout, stderr = execute_command(['netstat', '-an'])
            if success:
                return stdout
            
            return f"Error: {stderr}"
        except Exception as e:
            self.logger.error(f"Error getting active connections: {e}")
            return f"Error: {str(e)}"
    
    def get_wifi_signal_strength(self, interface: str) -> Dict[str, Any]:
        """
        Get WiFi signal strength for an interface.
        
        Args:
            interface: WiFi interface name
        
        Returns:
            Dictionary with signal information
        """
        try:
            success, stdout, stderr = execute_command(['ifconfig', interface])
            if not success:
                return {'error': f'Interface {interface} not found'}
            
            # Parse signal strength from ifconfig output
            signal_match = re.search(r'status:\s*(\w+)', stdout)
            ssid_match = re.search(r'ssid\s+([^\s]+)', stdout)
            
            result = {
                'interface': interface,
                'status': signal_match.group(1) if signal_match else 'unknown',
                'ssid': ssid_match.group(1) if ssid_match else None
            }
            
            # Try to get more details with wpa_cli (if available)
            success, stdout, stderr = execute_command(['wpa_cli', '-i', interface, 'signal_poll'])
            if success:
                for line in stdout.split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        result[key.strip()] = value.strip()
            
            return result
        except Exception as e:
            self.logger.error(f"Error getting WiFi signal strength: {e}")
            return {'error': str(e)}
    
    def scan_wifi_networks(self, interface: str) -> str:
        """
        Scan for available WiFi networks.
        
        Args:
            interface: WiFi interface name
        
        Returns:
            Scan results as string
        """
        try:
            success, stdout, stderr = execute_command(['ifconfig', interface, 'scan'], timeout=15)
            if success:
                return stdout
            return f"Error: {stderr}"
        except Exception as e:
            self.logger.error(f"Error scanning WiFi networks: {e}")
            return f"Error: {str(e)}"
    
    def get_dhcp_lease_info(self, interface: str) -> str:
        """
        Get DHCP lease information for an interface.
        
        Args:
            interface: Interface name
        
        Returns:
            DHCP lease info as string
        """
        try:
            # Try to read dhclient lease file
            lease_file = f"/var/db/dhclient.leases.{interface}"
            try:
                with open(lease_file, 'r') as f:
                    return f.read()
            except FileNotFoundError:
                return f"No DHCP lease file found for {interface}"
        except Exception as e:
            self.logger.error(f"Error getting DHCP lease info: {e}")
            return f"Error: {str(e)}"
    
    def run_full_diagnostics(self) -> Dict[str, Any]:
        """
        Run full diagnostic suite.
        
        Returns:
            Dictionary with all diagnostic information
        """
        self.logger.info("Running full network diagnostics")
        
        diagnostics = {
            'interface_status': self.get_interface_status(),
            'routing_table': self.get_routing_table(),
            'dns_config': self.get_dns_config(),
            'arp_table': self.get_arp_table(),
            'active_connections': self.get_active_connections(),
            'connectivity_tests': {
                'gateway': self.test_gateway_connectivity(),
                'external': self.test_external_connectivity(),
                'dns': self.test_dns_resolution()
            }
        }
        
        return diagnostics
    
    def get_connectivity_status(self) -> Dict[str, str]:
        """
        Get overall connectivity status with visual indicators.
        
        Returns:
            Dictionary with status for each component
        """
        status = {}
        
        # Test gateway
        gateway_test = self.test_gateway_connectivity()
        if gateway_test['status'] == 'error':
            status['gateway'] = 'red'
        elif gateway_test['status'] == 'success':
            status['gateway'] = 'green'
        else:
            status['gateway'] = 'yellow'
        
        # Test external connectivity
        external_test = self.test_external_connectivity()
        status['external'] = 'green' if external_test['status'] == 'success' else 'red'
        
        # Test DNS
        dns_test = self.test_dns_resolution()
        status['dns'] = 'green' if dns_test['status'] == 'success' else 'red'
        
        return status
    
    def get_common_issues_help(self) -> List[Dict[str, str]]:
        """
        Get help messages for common network issues.
        
        Returns:
            List of issue-help dictionaries
        """
        return [
            {
                'issue': 'No default gateway configured',
                'help': 'Set a default gateway in rc.conf: defaultrouter="192.168.1.1"\n'
                       'Or use DHCP to get gateway automatically.',
                'handbook': 'FreeBSD Handbook: Section 32.2 - Basic Network Configuration'
            },
            {
                'issue': 'DNS servers unreachable',
                'help': 'Check /etc/resolv.conf for correct DNS servers.\n'
                       'Common DNS servers: 8.8.8.8 (Google), 1.1.1.1 (Cloudflare)',
                'handbook': 'FreeBSD Handbook: Section 32.7 - DNS'
            },
            {
                'issue': 'Interface has no IP address',
                'help': 'Configure interface with DHCP: ifconfig_em0="DHCP" in rc.conf\n'
                       'Or set static IP: ifconfig_em0="inet 192.168.1.100 netmask 255.255.255.0"',
                'handbook': 'FreeBSD Handbook: Section 32.3 - Network Interfaces'
            },
            {
                'issue': 'WiFi not connecting',
                'help': 'Check wpa_supplicant.conf for correct SSID and password.\n'
                       'Verify wireless interface is up: ifconfig wlan0 up\n'
                       'Check signal strength: ifconfig wlan0',
                'handbook': 'FreeBSD Handbook: Section 32.4 - Wireless Networking'
            },
            {
                'issue': 'Cannot reach external hosts but gateway works',
                'help': 'This usually indicates a routing or firewall issue.\n'
                       'Check if packets are being routed: traceroute 8.8.8.8\n'
                       'Verify firewall rules allow outbound traffic.',
                'handbook': 'FreeBSD Handbook: Section 32.6 - Firewalls'
            }
        ]
    
    def export_diagnostics_report(self, filepath: str) -> bool:
        """
        Export full diagnostics to a text file.
        
        Args:
            filepath: Path to export file
        
        Returns:
            True if successful
        """
        try:
            diagnostics = self.run_full_diagnostics()
            
            with open(filepath, 'w') as f:
                f.write("=" * 70 + "\n")
                f.write("BSD Network GUI - Diagnostics Report\n")
                f.write("=" * 70 + "\n\n")
                
                from datetime import datetime
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("\n" + "=" * 70 + "\n")
                f.write("INTERFACE STATUS\n")
                f.write("=" * 70 + "\n")
                f.write(diagnostics['interface_status'])
                
                f.write("\n" + "=" * 70 + "\n")
                f.write("ROUTING TABLE\n")
                f.write("=" * 70 + "\n")
                f.write(diagnostics['routing_table'])
                
                f.write("\n" + "=" * 70 + "\n")
                f.write("DNS CONFIGURATION\n")
                f.write("=" * 70 + "\n")
                f.write(diagnostics['dns_config'])
                
                f.write("\n" + "=" * 70 + "\n")
                f.write("ARP TABLE\n")
                f.write("=" * 70 + "\n")
                f.write(diagnostics['arp_table'])
                
                f.write("\n" + "=" * 70 + "\n")
                f.write("CONNECTIVITY TESTS\n")
                f.write("=" * 70 + "\n")
                
                for test_name, result in diagnostics['connectivity_tests'].items():
                    f.write(f"\n{test_name.upper()}:\n")
                    f.write(f"  Status: {result['status']}\n")
                    f.write(f"  Message: {result['message']}\n")
                    if 'output' in result:
                        f.write(f"  Output:\n{result['output']}\n")
                
                f.write("\n" + "=" * 70 + "\n")
                f.write("ACTIVE CONNECTIONS\n")
                f.write("=" * 70 + "\n")
                f.write(diagnostics['active_connections'])
                
                f.write("\n" + "=" * 70 + "\n")
                f.write("End of Report\n")
                f.write("=" * 70 + "\n")
            
            self.logger.info(f"Exported diagnostics report to {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Error exporting diagnostics report: {e}")
            return False
