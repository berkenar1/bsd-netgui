"""Handler for /etc/rc.conf configuration file on FreeBSD.

This module provides safe parsing and modification of rc.conf while
preserving comments, order, and formatting.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from ..utils.config_parser import ConfigParser


class RCConfHandler:
    """
    Handler for FreeBSD rc.conf configuration file.
    
    Manages network-related variables in rc.conf:
    - ifconfig_* (interface configuration)
    - defaultrouter
    - hostname
    - wlans_* (wireless interfaces)
    - Network service flags
    """
    
    def __init__(self, rc_conf_path: str = "/etc/rc.conf"):
        """
        Initialize the RCConfHandler.
        
        Args:
            rc_conf_path: Path to rc.conf file (default: /etc/rc.conf)
        """
        self.rc_conf_path = rc_conf_path
        self.logger = logging.getLogger(__name__)
        self.parser = ConfigParser(rc_conf_path)
        self._loaded = False
    
    def load(self) -> bool:
        """
        Load and parse the rc.conf file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if file exists, create if not
            if not Path(self.rc_conf_path).exists():
                self.logger.warning(f"rc.conf not found at {self.rc_conf_path}, will create on save")
                self._loaded = True
                return True
            
            self._loaded = self.parser.parse()
            return self._loaded
        except Exception as e:
            self.logger.error(f"Error loading rc.conf: {e}")
            return False
    
    def save(self, backup: bool = True) -> bool:
        """
        Save changes to rc.conf atomically.
        
        Args:
            backup: Whether to create a backup before writing
        
        Returns:
            True if successful, False otherwise
        """
        if not self._loaded:
            self.logger.error("Cannot save: rc.conf not loaded")
            return False
        
        # Validate before saving
        valid, errors = self.validate()
        if not valid:
            self.logger.error(f"Validation failed: {errors}")
            return False
        
        return self.parser.write(backup=backup)
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate the rc.conf configuration.
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Basic parser validation
        valid, parser_errors = self.parser.validate()
        errors.extend(parser_errors)
        
        # Validate network-specific settings
        # Check defaultrouter is valid IP
        defaultrouter = self.get_default_router()
        if defaultrouter:
            from ..utils.system_utils import validate_ip_address
            if not validate_ip_address(defaultrouter):
                errors.append(f"Invalid defaultrouter IP: {defaultrouter}")
        
        # Validate interface configurations
        for key in self.parser.variables.keys():
            if key.startswith('ifconfig_'):
                value = self.parser.get(key)
                # Check for basic syntax issues
                if value and 'inet' in value.lower():
                    # Extract IP if present
                    ip_match = re.search(r'inet\s+(\S+)', value)
                    if ip_match:
                        from ..utils.system_utils import validate_ip_address
                        ip = ip_match.group(1)
                        if not validate_ip_address(ip):
                            errors.append(f"Invalid IP in {key}: {ip}")
        
        return len(errors) == 0, errors
    
    # Interface Configuration Methods
    
    def get_interface_config(self, iface: str) -> Optional[str]:
        """
        Get configuration for a specific interface.
        
        Args:
            iface: Interface name (e.g., 'em0', 'wlan0')
        
        Returns:
            Configuration string or None if not configured
        """
        key = f"ifconfig_{iface}"
        return self.parser.get(key)
    
    def set_interface_dhcp(self, iface: str) -> bool:
        """
        Configure interface to use DHCP.
        
        Args:
            iface: Interface name
        
        Returns:
            True if successful
        """
        try:
            key = f"ifconfig_{iface}"
            self.parser.set(key, "DHCP")
            self.logger.info(f"Set {iface} to DHCP")
            return True
        except Exception as e:
            self.logger.error(f"Error setting DHCP for {iface}: {e}")
            return False
    
    def set_interface_static(self, iface: str, ip: str, netmask: str, 
                           options: Optional[str] = None) -> bool:
        """
        Configure interface with static IP.
        
        Args:
            iface: Interface name
            ip: IP address
            netmask: Network mask (e.g., "255.255.255.0" or "24")
            options: Additional options (e.g., "mtu 1500")
        
        Returns:
            True if successful
        """
        try:
            from ..utils.system_utils import validate_ip_address, validate_netmask
            
            if not validate_ip_address(ip):
                self.logger.error(f"Invalid IP address: {ip}")
                return False
            
            if not validate_netmask(netmask):
                self.logger.error(f"Invalid netmask: {netmask}")
                return False
            
            # Build configuration string
            config = f"inet {ip} netmask {netmask}"
            if options:
                config += f" {options}"
            
            key = f"ifconfig_{iface}"
            self.parser.set(key, config)
            self.logger.info(f"Set {iface} to static IP {ip}/{netmask}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting static IP for {iface}: {e}")
            return False
    
    def remove_interface_config(self, iface: str) -> bool:
        """
        Remove interface configuration.
        
        Args:
            iface: Interface name
        
        Returns:
            True if removed, False if not found
        """
        key = f"ifconfig_{iface}"
        return self.parser.delete(key)
    
    def get_all_interface_configs(self) -> Dict[str, str]:
        """
        Get all interface configurations.
        
        Returns:
            Dictionary mapping interface names to their configurations
        """
        configs = {}
        for key, line in self.parser.variables.items():
            if key.startswith('ifconfig_'):
                iface = key.replace('ifconfig_', '')
                configs[iface] = line.value
        return configs
    
    # Wireless Configuration Methods
    
    def get_wlan_parent(self, wlan_iface: str) -> Optional[str]:
        """
        Get the parent interface for a WLAN interface.
        
        Args:
            wlan_iface: WLAN interface name (e.g., 'wlan0')
        
        Returns:
            Parent interface name or None
        """
        # Check wlans_<parent> for this wlan interface
        for key in self.parser.variables.keys():
            if key.startswith('wlans_'):
                value = self.parser.get(key)
                if value and wlan_iface in value:
                    return key.replace('wlans_', '')
        return None
    
    def set_wlan_parent(self, parent_iface: str, wlan_iface: str) -> bool:
        """
        Set up WLAN interface with parent.
        
        Args:
            parent_iface: Parent interface (e.g., 'iwn0')
            wlan_iface: WLAN interface (e.g., 'wlan0')
        
        Returns:
            True if successful
        """
        try:
            key = f"wlans_{parent_iface}"
            self.parser.set(key, wlan_iface)
            self.logger.info(f"Set wlan parent: {parent_iface} -> {wlan_iface}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting wlan parent: {e}")
            return False
    
    # Default Router Configuration
    
    def get_default_router(self) -> Optional[str]:
        """
        Get the default router (gateway) IP.
        
        Returns:
            Default router IP or None
        """
        return self.parser.get('defaultrouter')
    
    def set_default_router(self, gateway_ip: str) -> bool:
        """
        Set the default router (gateway).
        
        Args:
            gateway_ip: Gateway IP address
        
        Returns:
            True if successful
        """
        try:
            from ..utils.system_utils import validate_ip_address
            
            if not validate_ip_address(gateway_ip):
                self.logger.error(f"Invalid gateway IP: {gateway_ip}")
                return False
            
            self.parser.set('defaultrouter', gateway_ip)
            self.logger.info(f"Set default router to {gateway_ip}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting default router: {e}")
            return False
    
    def remove_default_router(self) -> bool:
        """
        Remove default router configuration.
        
        Returns:
            True if removed
        """
        return self.parser.delete('defaultrouter')
    
    # Hostname Configuration
    
    def get_hostname(self) -> Optional[str]:
        """
        Get the system hostname.
        
        Returns:
            Hostname or None
        """
        return self.parser.get('hostname')
    
    def set_hostname(self, hostname: str) -> bool:
        """
        Set the system hostname.
        
        Args:
            hostname: Hostname to set
        
        Returns:
            True if successful
        """
        try:
            if not hostname or not hostname.strip():
                self.logger.error("Hostname cannot be empty")
                return False
            
            self.parser.set('hostname', hostname.strip())
            self.logger.info(f"Set hostname to {hostname}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting hostname: {e}")
            return False
    
    # Service Configuration
    
    def enable_service(self, service: str) -> bool:
        """
        Enable a service (set service_enable="YES").
        
        Args:
            service: Service name (e.g., 'sshd', 'ntpd')
        
        Returns:
            True if successful
        """
        try:
            key = f"{service}_enable"
            self.parser.set(key, '"YES"')
            self.logger.info(f"Enabled service: {service}")
            return True
        except Exception as e:
            self.logger.error(f"Error enabling service {service}: {e}")
            return False
    
    def disable_service(self, service: str) -> bool:
        """
        Disable a service (set service_enable="NO").
        
        Args:
            service: Service name
        
        Returns:
            True if successful
        """
        try:
            key = f"{service}_enable"
            self.parser.set(key, '"NO"')
            self.logger.info(f"Disabled service: {service}")
            return True
        except Exception as e:
            self.logger.error(f"Error disabling service {service}: {e}")
            return False
    
    def is_service_enabled(self, service: str) -> bool:
        """
        Check if a service is enabled.
        
        Args:
            service: Service name
        
        Returns:
            True if enabled, False otherwise
        """
        key = f"{service}_enable"
        value = self.parser.get(key, "NO")
        return value.strip('"').upper() == "YES"
    
    # Generic Configuration Methods
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if not found
        
        Returns:
            Value or default
        """
        return self.parser.get(key, default)
    
    def set(self, key: str, value: str, comment: Optional[str] = None) -> bool:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            comment: Optional comment
        
        Returns:
            True if successful
        """
        try:
            self.parser.set(key, value, comment)
            return True
        except Exception as e:
            self.logger.error(f"Error setting {key}={value}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete a configuration key.
        
        Args:
            key: Configuration key
        
        Returns:
            True if deleted
        """
        return self.parser.delete(key)
    
    def get_all(self) -> Dict[str, str]:
        """
        Get all configuration variables.
        
        Returns:
            Dictionary of all key-value pairs
        """
        return self.parser.get_all_variables()
