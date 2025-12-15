"""Tests for rc.conf parser."""

import unittest
import tempfile
import os
from pathlib import Path
from bsd_netgui.backend.rc_conf_handler import RCConfHandler


class TestRCConfHandler(unittest.TestCase):
    """Test cases for RCConfHandler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.rc_conf_path = os.path.join(self.test_dir, "rc.conf")
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def create_test_rc_conf(self, content: str):
        """Create a test rc.conf file."""
        with open(self.rc_conf_path, 'w') as f:
            f.write(content)
    
    def test_load_empty_file(self):
        """Test loading an empty rc.conf."""
        self.create_test_rc_conf("")
        handler = RCConfHandler(self.rc_conf_path)
        self.assertTrue(handler.load())
    
    def test_load_basic_config(self):
        """Test loading a basic rc.conf."""
        content = """# Basic configuration
hostname="freebsd.local"
ifconfig_em0="DHCP"
defaultrouter="192.168.1.1"
"""
        self.create_test_rc_conf(content)
        handler = RCConfHandler(self.rc_conf_path)
        self.assertTrue(handler.load())
        
        # Check values
        self.assertEqual(handler.get_hostname(), '"freebsd.local"')
        self.assertEqual(handler.get_interface_config('em0'), '"DHCP"')
        self.assertEqual(handler.get_default_router(), '"192.168.1.1"')
    
    def test_set_interface_dhcp(self):
        """Test setting interface to DHCP."""
        self.create_test_rc_conf("")
        handler = RCConfHandler(self.rc_conf_path)
        handler.load()
        
        self.assertTrue(handler.set_interface_dhcp('em0'))
        self.assertEqual(handler.get_interface_config('em0'), 'DHCP')
    
    def test_set_interface_static(self):
        """Test setting interface to static IP."""
        self.create_test_rc_conf("")
        handler = RCConfHandler(self.rc_conf_path)
        handler.load()
        
        self.assertTrue(handler.set_interface_static('em0', '192.168.1.100', '255.255.255.0'))
        config = handler.get_interface_config('em0')
        self.assertIn('192.168.1.100', config)
        self.assertIn('255.255.255.0', config)
    
    def test_set_invalid_ip(self):
        """Test setting invalid IP address."""
        self.create_test_rc_conf("")
        handler = RCConfHandler(self.rc_conf_path)
        handler.load()
        
        self.assertFalse(handler.set_interface_static('em0', 'invalid', '255.255.255.0'))
    
    def test_set_default_router(self):
        """Test setting default router."""
        self.create_test_rc_conf("")
        handler = RCConfHandler(self.rc_conf_path)
        handler.load()
        
        self.assertTrue(handler.set_default_router('192.168.1.1'))
        self.assertEqual(handler.get_default_router(), '192.168.1.1')
    
    def test_remove_interface_config(self):
        """Test removing interface configuration."""
        content = """ifconfig_em0="DHCP"
ifconfig_em1="inet 192.168.1.100 netmask 255.255.255.0"
"""
        self.create_test_rc_conf(content)
        handler = RCConfHandler(self.rc_conf_path)
        handler.load()
        
        self.assertTrue(handler.remove_interface_config('em0'))
        self.assertIsNone(handler.get_interface_config('em0'))
        self.assertIsNotNone(handler.get_interface_config('em1'))
    
    def test_get_all_interface_configs(self):
        """Test getting all interface configurations."""
        content = """ifconfig_em0="DHCP"
ifconfig_em1="inet 192.168.1.100 netmask 255.255.255.0"
ifconfig_wlan0="WPA DHCP"
hostname="test"
"""
        self.create_test_rc_conf(content)
        handler = RCConfHandler(self.rc_conf_path)
        handler.load()
        
        configs = handler.get_all_interface_configs()
        self.assertEqual(len(configs), 3)
        self.assertIn('em0', configs)
        self.assertIn('em1', configs)
        self.assertIn('wlan0', configs)
    
    def test_service_management(self):
        """Test service enable/disable."""
        self.create_test_rc_conf("")
        handler = RCConfHandler(self.rc_conf_path)
        handler.load()
        
        # Enable service
        self.assertTrue(handler.enable_service('sshd'))
        self.assertTrue(handler.is_service_enabled('sshd'))
        
        # Disable service
        self.assertTrue(handler.disable_service('sshd'))
        self.assertFalse(handler.is_service_enabled('sshd'))
    
    def test_wlan_parent_config(self):
        """Test WLAN parent interface configuration."""
        self.create_test_rc_conf("")
        handler = RCConfHandler(self.rc_conf_path)
        handler.load()
        
        self.assertTrue(handler.set_wlan_parent('iwn0', 'wlan0'))
        self.assertEqual(handler.get_wlan_parent('wlan0'), 'iwn0')
    
    def test_preserve_comments(self):
        """Test that comments are preserved."""
        content = """# Network configuration for FreeBSD
hostname="freebsd.local"  # Main hostname
# Interface configuration
ifconfig_em0="DHCP"
"""
        self.create_test_rc_conf(content)
        handler = RCConfHandler(self.rc_conf_path)
        handler.load()
        handler.set_interface_static('em1', '10.0.0.1', '255.255.255.0')
        handler.save(backup=False)
        
        # Read back and check comments are preserved
        with open(self.rc_conf_path, 'r') as f:
            content = f.read()
        
        self.assertIn('# Network configuration', content)
        self.assertIn('# Interface configuration', content)
    
    def test_save_and_reload(self):
        """Test saving and reloading configuration."""
        self.create_test_rc_conf("")
        handler = RCConfHandler(self.rc_conf_path)
        handler.load()
        
        handler.set_hostname('test-host')
        handler.set_interface_dhcp('em0')
        handler.set_default_router('192.168.1.1')
        
        self.assertTrue(handler.save(backup=False))
        
        # Reload and verify
        handler2 = RCConfHandler(self.rc_conf_path)
        handler2.load()
        
        self.assertEqual(handler2.get_hostname(), 'test-host')
        self.assertEqual(handler2.get_interface_config('em0'), 'DHCP')
        self.assertEqual(handler2.get_default_router(), '192.168.1.1')
    
    def test_backup_creation(self):
        """Test that backup is created on save."""
        content = """hostname="original"
"""
        self.create_test_rc_conf(content)
        handler = RCConfHandler(self.rc_conf_path)
        handler.load()
        
        handler.set_hostname('modified')
        handler.save(backup=True)
        
        # Check backup exists
        backup_path = f"{self.rc_conf_path}.bak"
        self.assertTrue(os.path.exists(backup_path))
        
        # Check backup has original content
        with open(backup_path, 'r') as f:
            backup_content = f.read()
        self.assertIn('original', backup_content)
    
    def test_validation(self):
        """Test configuration validation."""
        self.create_test_rc_conf("")
        handler = RCConfHandler(self.rc_conf_path)
        handler.load()
        
        # Valid configuration
        handler.set_default_router('192.168.1.1')
        valid, errors = handler.validate()
        self.assertTrue(valid)
        
        # Invalid IP
        handler.set('defaultrouter', 'invalid-ip')
        valid, errors = handler.validate()
        self.assertFalse(valid)
        self.assertGreater(len(errors), 0)


if __name__ == '__main__':
    unittest.main()
