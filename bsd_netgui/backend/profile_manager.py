"""Network profile management system.

This module provides a profile abstraction layer that combines rc.conf
and wpa_supplicant.conf settings into reusable network profiles.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from .rc_conf_handler import RCConfHandler
from .wpa_conf_handler import WPAConfHandler


class NetworkProfile:
    """Represents a network configuration profile."""
    
    def __init__(self):
        """Initialize a NetworkProfile."""
        self.name: str = "Unnamed Profile"
        self.type: str = "ethernet"  # ethernet, wifi, tethering
        self.interface: str = "em0"
        self.autoconnect: bool = True
        self.config: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert profile to dictionary for JSON export.
        
        Returns:
            Profile as dictionary
        """
        return {
            'name': self.name,
            'type': self.type,
            'interface': self.interface,
            'autoconnect': self.autoconnect,
            'config': self.config
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NetworkProfile':
        """
        Create profile from dictionary.
        
        Args:
            data: Profile dictionary
        
        Returns:
            NetworkProfile instance
        """
        profile = cls()
        profile.name = data.get('name', 'Unnamed Profile')
        profile.type = data.get('type', 'ethernet')
        profile.interface = data.get('interface', 'em0')
        profile.autoconnect = data.get('autoconnect', True)
        profile.config = data.get('config', {})
        return profile
    
    def __repr__(self):
        """String representation."""
        return f"NetworkProfile(name={self.name}, type={self.type}, interface={self.interface})"


class ProfileManager:
    """
    Manages network configuration profiles.
    
    Profiles combine rc.conf and wpa_supplicant.conf settings into
    reusable configurations that can be easily applied.
    """
    
    # Built-in profile templates
    TEMPLATES = {
        'lan_dhcp': {
            'name': 'LAN (DHCP)',
            'type': 'ethernet',
            'interface': 'em0',
            'autoconnect': True,
            'config': {
                'dhcp': True
            }
        },
        'lan_static': {
            'name': 'LAN (Static IP)',
            'type': 'ethernet',
            'interface': 'em0',
            'autoconnect': True,
            'config': {
                'dhcp': False,
                'ip': '192.168.1.100',
                'netmask': '255.255.255.0',
                'gateway': '192.168.1.1'
            }
        },
        'wifi_wpa2': {
            'name': 'Home WiFi (WPA2)',
            'type': 'wifi',
            'interface': 'wlan0',
            'autoconnect': True,
            'config': {
                'ssid': 'MyNetwork',
                'security': 'WPA2-PSK',
                'password': '',
                'dhcp': True
            }
        },
        'wifi_open': {
            'name': 'Guest WiFi (Open)',
            'type': 'wifi',
            'interface': 'wlan0',
            'autoconnect': False,
            'config': {
                'ssid': 'GuestNetwork',
                'security': 'NONE',
                'dhcp': True
            }
        },
        'mobile_tethering': {
            'name': 'Mobile Tethering',
            'type': 'tethering',
            'interface': 'ue0',
            'autoconnect': False,
            'config': {
                'dhcp': True
            }
        }
    }
    
    def __init__(self, 
                 rc_conf_path: str = "/etc/rc.conf",
                 wpa_conf_path: str = "/etc/wpa_supplicant.conf",
                 profiles_dir: str = "/var/db/bsd-netgui/profiles"):
        """
        Initialize the ProfileManager.
        
        Args:
            rc_conf_path: Path to rc.conf
            wpa_conf_path: Path to wpa_supplicant.conf
            profiles_dir: Directory for storing profile JSON files
        """
        self.logger = logging.getLogger(__name__)
        self.rc_conf_path = rc_conf_path
        self.wpa_conf_path = wpa_conf_path
        self.profiles_dir = Path(profiles_dir)
        
        # Create profiles directory if it doesn't exist
        try:
            self.profiles_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.warning(f"Could not create profiles directory: {e}")
        
        self.profiles: List[NetworkProfile] = []
        self._loaded = False
    
    def load_profiles(self) -> bool:
        """
        Load all saved profiles from disk.
        
        Returns:
            True if successful
        """
        try:
            self.profiles = []
            
            if not self.profiles_dir.exists():
                self.logger.warning(f"Profiles directory does not exist: {self.profiles_dir}")
                self._loaded = True
                return True
            
            # Load all JSON files from profiles directory
            for profile_file in self.profiles_dir.glob('*.json'):
                try:
                    with open(profile_file, 'r') as f:
                        data = json.load(f)
                    profile = NetworkProfile.from_dict(data)
                    self.profiles.append(profile)
                    self.logger.debug(f"Loaded profile: {profile.name}")
                except Exception as e:
                    self.logger.error(f"Error loading profile {profile_file}: {e}")
            
            self.logger.info(f"Loaded {len(self.profiles)} profiles")
            self._loaded = True
            return True
        except Exception as e:
            self.logger.error(f"Error loading profiles: {e}")
            return False
    
    def save_profile(self, profile: NetworkProfile) -> bool:
        """
        Save a profile to disk.
        
        Args:
            profile: Profile to save
        
        Returns:
            True if successful
        """
        try:
            # Sanitize filename
            filename = profile.name.lower().replace(' ', '_').replace('/', '_')
            filename = ''.join(c for c in filename if c.isalnum() or c in ('_', '-'))
            profile_file = self.profiles_dir / f"{filename}.json"
            
            # Write profile as JSON
            with open(profile_file, 'w') as f:
                json.dump(profile.to_dict(), f, indent=2)
            
            self.logger.info(f"Saved profile: {profile.name} to {profile_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving profile {profile.name}: {e}")
            return False
    
    def delete_profile(self, profile_name: str) -> bool:
        """
        Delete a profile from disk.
        
        Args:
            profile_name: Name of profile to delete
        
        Returns:
            True if deleted
        """
        try:
            # Find profile file
            filename = profile_name.lower().replace(' ', '_').replace('/', '_')
            filename = ''.join(c for c in filename if c.isalnum() or c in ('_', '-'))
            profile_file = self.profiles_dir / f"{filename}.json"
            
            if profile_file.exists():
                profile_file.unlink()
                self.logger.info(f"Deleted profile: {profile_name}")
                
                # Remove from loaded profiles
                self.profiles = [p for p in self.profiles if p.name != profile_name]
                return True
            
            self.logger.warning(f"Profile file not found: {profile_file}")
            return False
        except Exception as e:
            self.logger.error(f"Error deleting profile {profile_name}: {e}")
            return False
    
    def get_profile(self, profile_name: str) -> Optional[NetworkProfile]:
        """
        Get a profile by name.
        
        Args:
            profile_name: Profile name
        
        Returns:
            NetworkProfile or None
        """
        for profile in self.profiles:
            if profile.name == profile_name:
                return profile
        return None
    
    def list_profiles(self) -> List[NetworkProfile]:
        """
        List all loaded profiles.
        
        Returns:
            List of profiles
        """
        return self.profiles.copy()
    
    def create_from_template(self, template_name: str, name: Optional[str] = None) -> Optional[NetworkProfile]:
        """
        Create a profile from a template.
        
        Args:
            template_name: Template name (e.g., 'lan_dhcp', 'wifi_wpa2')
            name: Optional custom name for the profile
        
        Returns:
            NetworkProfile or None if template not found
        """
        if template_name not in self.TEMPLATES:
            self.logger.error(f"Template not found: {template_name}")
            return None
        
        template = self.TEMPLATES[template_name]
        profile = NetworkProfile.from_dict(template)
        
        if name:
            profile.name = name
        
        self.logger.info(f"Created profile from template: {template_name}")
        return profile
    
    def apply_profile(self, profile: NetworkProfile, backup: bool = True) -> bool:
        """
        Apply a profile to the system.
        
        This updates rc.conf and wpa_supplicant.conf as needed.
        
        Args:
            profile: Profile to apply
            backup: Whether to backup config files
        
        Returns:
            True if successful
        """
        try:
            self.logger.info(f"Applying profile: {profile.name}")
            
            # Load handlers
            rc_conf = RCConfHandler(self.rc_conf_path)
            if not rc_conf.load():
                self.logger.error("Failed to load rc.conf")
                return False
            
            # Apply based on profile type
            if profile.type == 'ethernet' or profile.type == 'tethering':
                return self._apply_ethernet_profile(profile, rc_conf, backup)
            elif profile.type == 'wifi':
                return self._apply_wifi_profile(profile, rc_conf, backup)
            else:
                self.logger.error(f"Unknown profile type: {profile.type}")
                return False
        except Exception as e:
            self.logger.error(f"Error applying profile: {e}")
            return False
    
    def _apply_ethernet_profile(self, profile: NetworkProfile, 
                               rc_conf: RCConfHandler, backup: bool) -> bool:
        """
        Apply an ethernet or tethering profile.
        
        Args:
            profile: Profile to apply
            rc_conf: RCConfHandler instance
            backup: Whether to backup
        
        Returns:
            True if successful
        """
        config = profile.config
        interface = profile.interface
        
        # Configure interface
        if config.get('dhcp', True):
            rc_conf.set_interface_dhcp(interface)
        else:
            ip = config.get('ip')
            netmask = config.get('netmask')
            if not ip or not netmask:
                self.logger.error("Static IP configuration requires 'ip' and 'netmask'")
                return False
            
            rc_conf.set_interface_static(interface, ip, netmask)
            
            # Set gateway if provided
            gateway = config.get('gateway')
            if gateway:
                rc_conf.set_default_router(gateway)
        
        # Save rc.conf
        if not rc_conf.save(backup=backup):
            self.logger.error("Failed to save rc.conf")
            return False
        
        self.logger.info(f"Applied ethernet profile: {profile.name}")
        return True
    
    def _apply_wifi_profile(self, profile: NetworkProfile, 
                           rc_conf: RCConfHandler, backup: bool) -> bool:
        """
        Apply a WiFi profile.
        
        Args:
            profile: Profile to apply
            rc_conf: RCConfHandler instance
            backup: Whether to backup
        
        Returns:
            True if successful
        """
        config = profile.config
        interface = profile.interface
        
        # Load wpa_supplicant.conf
        wpa_conf = WPAConfHandler(self.wpa_conf_path)
        if not wpa_conf.load():
            self.logger.error("Failed to load wpa_supplicant.conf")
            return False
        
        # Add/update network in wpa_supplicant.conf
        ssid = config.get('ssid')
        if not ssid:
            self.logger.error("WiFi profile requires 'ssid'")
            return False
        
        password = config.get('password')
        security = config.get('security', 'WPA2-PSK')
        priority = config.get('priority', 5)
        scan_ssid = config.get('scan_ssid', False)
        
        # Remove existing network with same SSID if present
        wpa_conf.remove_network(ssid)
        
        # Add new network
        if not wpa_conf.add_network(ssid, password, security, priority, scan_ssid):
            self.logger.error(f"Failed to add network to wpa_supplicant.conf")
            return False
        
        # Save wpa_supplicant.conf
        if not wpa_conf.save(backup=backup):
            self.logger.error("Failed to save wpa_supplicant.conf")
            return False
        
        # Configure interface in rc.conf
        if config.get('dhcp', True):
            # For WiFi with DHCP, use "WPA DHCP"
            rc_conf.set(f"ifconfig_{interface}", "WPA DHCP")
        else:
            ip = config.get('ip')
            netmask = config.get('netmask')
            if not ip or not netmask:
                self.logger.error("Static IP configuration requires 'ip' and 'netmask'")
                return False
            
            rc_conf.set(f"ifconfig_{interface}", f"WPA inet {ip} netmask {netmask}")
            
            # Set gateway if provided
            gateway = config.get('gateway')
            if gateway:
                rc_conf.set_default_router(gateway)
        
        # Save rc.conf
        if not rc_conf.save(backup=backup):
            self.logger.error("Failed to save rc.conf")
            return False
        
        self.logger.info(f"Applied WiFi profile: {profile.name}")
        return True
    
    def export_profile(self, profile: NetworkProfile, export_path: str) -> bool:
        """
        Export a profile to a JSON file.
        
        Args:
            profile: Profile to export
            export_path: Path to export file
        
        Returns:
            True if successful
        """
        try:
            with open(export_path, 'w') as f:
                json.dump(profile.to_dict(), f, indent=2)
            
            self.logger.info(f"Exported profile {profile.name} to {export_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error exporting profile: {e}")
            return False
    
    def import_profile(self, import_path: str) -> Optional[NetworkProfile]:
        """
        Import a profile from a JSON file.
        
        Args:
            import_path: Path to import file
        
        Returns:
            NetworkProfile or None if import failed
        """
        try:
            with open(import_path, 'r') as f:
                data = json.load(f)
            
            profile = NetworkProfile.from_dict(data)
            self.logger.info(f"Imported profile: {profile.name}")
            return profile
        except Exception as e:
            self.logger.error(f"Error importing profile: {e}")
            return None
    
    def get_current_profile(self) -> Optional[Dict[str, Any]]:
        """
        Get the current system network configuration as a profile.
        
        Returns:
            Dictionary representing current configuration
        """
        try:
            rc_conf = RCConfHandler(self.rc_conf_path)
            if not rc_conf.load():
                return None
            
            # Get all interface configs
            interfaces = rc_conf.get_all_interface_configs()
            default_router = rc_conf.get_default_router()
            
            return {
                'interfaces': interfaces,
                'default_router': default_router
            }
        except Exception as e:
            self.logger.error(f"Error getting current profile: {e}")
            return None
    
    @classmethod
    def get_available_templates(cls) -> List[str]:
        """
        Get list of available profile templates.
        
        Returns:
            List of template names
        """
        return list(cls.TEMPLATES.keys())
    
    @classmethod
    def get_template_info(cls, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a template.
        
        Args:
            template_name: Template name
        
        Returns:
            Template dictionary or None
        """
        return cls.TEMPLATES.get(template_name)
