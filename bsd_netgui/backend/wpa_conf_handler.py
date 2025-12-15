"""Handler for /etc/wpa_supplicant.conf configuration file.

This module provides safe parsing and modification of wpa_supplicant.conf
while preserving comments and structure.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class WPANetwork:
    """Represents a network block in wpa_supplicant.conf."""
    
    def __init__(self):
        """Initialize a WPANetwork."""
        self.ssid: Optional[str] = None
        self.psk: Optional[str] = None
        self.key_mgmt: str = "WPA-PSK"
        self.priority: int = 0
        self.scan_ssid: int = 0
        self.disabled: bool = False
        self.other_params: Dict[str, str] = {}
        self.comments: List[str] = []
    
    def to_block(self) -> str:
        """
        Convert network to wpa_supplicant.conf block format.
        
        Returns:
            Configuration block as string
        """
        lines = []
        
        # Add comments
        for comment in self.comments:
            lines.append(f"# {comment}")
        
        lines.append("network={")
        
        # Add required parameters
        if self.ssid:
            lines.append(f'    ssid="{self.ssid}"')
        
        if self.key_mgmt == "NONE":
            lines.append("    key_mgmt=NONE")
        else:
            if self.psk:
                # Check if PSK is already hex (64 chars)
                if len(self.psk) == 64 and all(c in '0123456789abcdefABCDEF' for c in self.psk):
                    lines.append(f"    psk={self.psk}")
                else:
                    lines.append(f'    psk="{self.psk}"')
            
            if self.key_mgmt != "WPA-PSK":
                lines.append(f"    key_mgmt={self.key_mgmt}")
        
        # Add optional parameters
        if self.priority != 0:
            lines.append(f"    priority={self.priority}")
        
        if self.scan_ssid != 0:
            lines.append(f"    scan_ssid={self.scan_ssid}")
        
        if self.disabled:
            lines.append("    disabled=1")
        
        # Add other parameters
        for key, value in sorted(self.other_params.items()):
            lines.append(f"    {key}={value}")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def __repr__(self):
        """String representation."""
        return f"WPANetwork(ssid={self.ssid}, key_mgmt={self.key_mgmt}, priority={self.priority})"


class WPAConfHandler:
    """
    Handler for wpa_supplicant.conf configuration file.
    
    Manages WiFi network configurations with support for:
    - Multiple network profiles
    - WPA/WPA2/WPA3 security
    - Open networks
    - Priority-based connection
    """
    
    def __init__(self, wpa_conf_path: str = "/etc/wpa_supplicant.conf"):
        """
        Initialize the WPAConfHandler.
        
        Args:
            wpa_conf_path: Path to wpa_supplicant.conf
        """
        self.wpa_conf_path = wpa_conf_path
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.ctrl_interface: Optional[str] = None
        self.ctrl_interface_group: Optional[str] = None
        self.update_config: int = 1
        self.global_params: Dict[str, str] = {}
        
        # Networks
        self.networks: List[WPANetwork] = []
        
        # File structure
        self.header_comments: List[str] = []
        
        self._loaded = False
    
    def load(self) -> bool:
        """
        Load and parse the wpa_supplicant.conf file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            path = Path(self.wpa_conf_path)
            if not path.exists():
                self.logger.warning(f"wpa_supplicant.conf not found at {self.wpa_conf_path}")
                self._loaded = True
                return True
            
            with open(path, 'r') as f:
                content = f.read()
            
            self._parse_content(content)
            self._loaded = True
            self.logger.info(f"Loaded {len(self.networks)} networks from {self.wpa_conf_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error loading wpa_supplicant.conf: {e}")
            return False
    
    def _parse_content(self, content: str):
        """
        Parse wpa_supplicant.conf content.
        
        Args:
            content: File content as string
        """
        lines = content.split('\n')
        i = 0
        current_comments = []
        in_network_block = False
        current_network = None
        seen_global_config = False
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Handle comments
            if line.startswith('#'):
                comment = line[1:].strip()
                if in_network_block and current_network:
                    # Comment inside network block (ignore for now)
                    pass
                else:
                    current_comments.append(comment)
                i += 1
                continue
            
            # Parse network block
            if line.startswith('network={') or line == 'network={':
                in_network_block = True
                current_network = WPANetwork()
                current_network.comments = current_comments.copy()
                current_comments = []
                i += 1
                continue
            
            if in_network_block and (line == '}' or line.startswith('}')):
                if current_network:
                    self.networks.append(current_network)
                in_network_block = False
                current_network = None
                i += 1
                continue
            
            # Parse parameters
            if in_network_block and current_network:
                self._parse_network_param(line, current_network)
            else:
                # First global config - save accumulated comments as header
                if not seen_global_config and current_comments:
                    self.header_comments = current_comments.copy()
                    current_comments = []
                seen_global_config = True
                self._parse_global_param(line)
            
            i += 1
        
        # Store any remaining comments as header comments if no global config seen
        if current_comments and not seen_global_config:
            self.header_comments = current_comments
    
    def _parse_network_param(self, line: str, network: WPANetwork):
        """
        Parse a parameter line in a network block.
        
        Args:
            line: Parameter line
            network: Network object to update
        """
        if '=' not in line:
            return
        
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip()
        
        # Remove quotes from value if present
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        
        # Set known parameters
        if key == 'ssid':
            network.ssid = value
        elif key == 'psk':
            network.psk = value
        elif key == 'key_mgmt':
            network.key_mgmt = value
        elif key == 'priority':
            try:
                network.priority = int(value)
            except ValueError:
                network.priority = 0
        elif key == 'scan_ssid':
            try:
                network.scan_ssid = int(value)
            except ValueError:
                network.scan_ssid = 0
        elif key == 'disabled':
            network.disabled = value == '1' or value.lower() == 'true'
        else:
            # Store unknown parameters
            network.other_params[key] = value
    
    def _parse_global_param(self, line: str):
        """
        Parse a global parameter line.
        
        Args:
            line: Parameter line
        """
        if '=' not in line:
            return
        
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip()
        
        if key == 'ctrl_interface':
            self.ctrl_interface = value
        elif key == 'ctrl_interface_group':
            self.ctrl_interface_group = value
        elif key == 'update_config':
            try:
                self.update_config = int(value)
            except ValueError:
                self.update_config = 1
        else:
            self.global_params[key] = value
    
    def save(self, backup: bool = True) -> bool:
        """
        Save configuration to wpa_supplicant.conf atomically.
        
        Args:
            backup: Whether to create a backup
        
        Returns:
            True if successful
        """
        if not self._loaded:
            self.logger.error("Cannot save: wpa_supplicant.conf not loaded")
            return False
        
        try:
            path = Path(self.wpa_conf_path)
            
            # Create backup if requested and file exists
            if backup and path.exists():
                import shutil
                backup_path = Path(f"{self.wpa_conf_path}.bak")
                shutil.copy2(path, backup_path)
                self.logger.info(f"Created backup: {backup_path}")
            
            # Generate content
            content = self._generate_content()
            
            # Write to temporary file first (atomic write)
            temp_path = Path(f"{self.wpa_conf_path}.tmp")
            with open(temp_path, 'w') as f:
                f.write(content)
            
            # Move temp file to actual file
            import shutil
            shutil.move(str(temp_path), str(path))
            
            # Set permissions (readable only by root)
            import os
            os.chmod(path, 0o600)
            
            self.logger.info(f"Successfully wrote configuration to {self.wpa_conf_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving wpa_supplicant.conf: {e}")
            if temp_path.exists():
                temp_path.unlink()
            return False
    
    def _generate_content(self) -> str:
        """
        Generate wpa_supplicant.conf content.
        
        Returns:
            Configuration content as string
        """
        lines = []
        
        # Add header comments
        for comment in self.header_comments:
            lines.append(f"# {comment}")
        
        if self.header_comments:
            lines.append("")
        
        # Add global parameters
        if self.ctrl_interface:
            lines.append(f"ctrl_interface={self.ctrl_interface}")
        
        if self.ctrl_interface_group:
            lines.append(f"ctrl_interface_group={self.ctrl_interface_group}")
        
        lines.append(f"update_config={self.update_config}")
        
        # Add other global parameters
        for key, value in sorted(self.global_params.items()):
            lines.append(f"{key}={value}")
        
        if lines:
            lines.append("")
        
        # Add network blocks
        for network in self.networks:
            lines.append(network.to_block())
            lines.append("")
        
        return "\n".join(lines)
    
    def add_network(self, ssid: str, password: Optional[str] = None, 
                   security: str = "WPA2-PSK", priority: int = 0,
                   scan_ssid: bool = False) -> bool:
        """
        Add a new network configuration.
        
        Args:
            ssid: Network SSID
            password: Network password (None for open networks)
            security: Security type (WPA-PSK, WPA2-PSK, WPA3-SAE, NONE)
            priority: Connection priority (higher = more preferred)
            scan_ssid: Whether to scan for hidden networks
        
        Returns:
            True if successful
        """
        try:
            network = WPANetwork()
            network.ssid = ssid
            network.priority = priority
            network.scan_ssid = 1 if scan_ssid else 0
            
            # Set security
            if security.upper() == "NONE" or password is None:
                network.key_mgmt = "NONE"
                network.psk = None
            else:
                network.psk = password
                if "WPA3" in security.upper() or "SAE" in security.upper():
                    network.key_mgmt = "SAE"
                else:
                    network.key_mgmt = "WPA-PSK"
            
            self.networks.append(network)
            self.logger.info(f"Added network: {ssid} ({security})")
            return True
        except Exception as e:
            self.logger.error(f"Error adding network {ssid}: {e}")
            return False
    
    def remove_network(self, ssid: str) -> bool:
        """
        Remove a network by SSID.
        
        Args:
            ssid: Network SSID to remove
        
        Returns:
            True if removed, False if not found
        """
        original_count = len(self.networks)
        self.networks = [n for n in self.networks if n.ssid != ssid]
        
        if len(self.networks) < original_count:
            self.logger.info(f"Removed network: {ssid}")
            return True
        
        self.logger.warning(f"Network not found: {ssid}")
        return False
    
    def get_network(self, ssid: str) -> Optional[WPANetwork]:
        """
        Get a network by SSID.
        
        Args:
            ssid: Network SSID
        
        Returns:
            WPANetwork object or None
        """
        for network in self.networks:
            if network.ssid == ssid:
                return network
        return None
    
    def update_network(self, ssid: str, password: Optional[str] = None,
                      priority: Optional[int] = None) -> bool:
        """
        Update an existing network configuration.
        
        Args:
            ssid: Network SSID
            password: New password (None to keep unchanged)
            priority: New priority (None to keep unchanged)
        
        Returns:
            True if successful, False if network not found
        """
        network = self.get_network(ssid)
        if not network:
            self.logger.warning(f"Network not found: {ssid}")
            return False
        
        if password is not None:
            network.psk = password
        
        if priority is not None:
            network.priority = priority
        
        self.logger.info(f"Updated network: {ssid}")
        return True
    
    def list_networks(self) -> List[Dict[str, any]]:
        """
        List all configured networks.
        
        Returns:
            List of network dictionaries
        """
        result = []
        for network in self.networks:
            result.append({
                'ssid': network.ssid,
                'key_mgmt': network.key_mgmt,
                'priority': network.priority,
                'scan_ssid': network.scan_ssid,
                'disabled': network.disabled
            })
        return result
    
    def clear_networks(self):
        """Clear all network configurations."""
        self.networks = []
        self.logger.info("Cleared all networks")
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate the configuration.
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Check for duplicate SSIDs
        ssids = [n.ssid for n in self.networks if n.ssid]
        if len(ssids) != len(set(ssids)):
            duplicates = [s for s in ssids if ssids.count(s) > 1]
            errors.append(f"Duplicate SSIDs found: {set(duplicates)}")
        
        # Validate individual networks
        for i, network in enumerate(self.networks):
            if not network.ssid:
                errors.append(f"Network #{i} has no SSID")
            
            if network.key_mgmt not in ["NONE", "WPA-PSK", "WPA-EAP", "SAE"]:
                errors.append(f"Network {network.ssid}: Invalid key_mgmt: {network.key_mgmt}")
            
            if network.key_mgmt != "NONE" and not network.psk:
                errors.append(f"Network {network.ssid}: No password set for secured network")
        
        return len(errors) == 0, errors
