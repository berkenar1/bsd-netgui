"""Tests for wpa_supplicant.conf parser."""

import unittest
import tempfile
import os
from bsd_netgui.backend.wpa_conf_handler import WPAConfHandler, WPANetwork


class TestWPANetwork(unittest.TestCase):
    """Test cases for WPANetwork class."""
    
    def test_network_creation(self):
        """Test creating a WPANetwork."""
        network = WPANetwork()
        network.ssid = "TestNetwork"
        network.psk = "testpassword"
        network.priority = 5
        
        self.assertEqual(network.ssid, "TestNetwork")
        self.assertEqual(network.psk, "testpassword")
        self.assertEqual(network.priority, 5)
    
    def test_to_block_wpa2(self):
        """Test converting WPA2 network to block."""
        network = WPANetwork()
        network.ssid = "HomeWiFi"
        network.psk = "mypassword"
        network.key_mgmt = "WPA-PSK"
        
        block = network.to_block()
        
        self.assertIn('network={', block)
        self.assertIn('ssid="HomeWiFi"', block)
        self.assertIn('psk="mypassword"', block)
        self.assertIn('}', block)
    
    def test_to_block_open(self):
        """Test converting open network to block."""
        network = WPANetwork()
        network.ssid = "OpenNetwork"
        network.key_mgmt = "NONE"
        
        block = network.to_block()
        
        self.assertIn('ssid="OpenNetwork"', block)
        self.assertIn('key_mgmt=NONE', block)
        self.assertNotIn('psk', block)
    
    def test_to_block_with_priority(self):
        """Test network block with priority."""
        network = WPANetwork()
        network.ssid = "PriorityNetwork"
        network.psk = "password"
        network.priority = 10
        
        block = network.to_block()
        
        self.assertIn('priority=10', block)


class TestWPAConfHandler(unittest.TestCase):
    """Test cases for WPAConfHandler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.wpa_conf_path = os.path.join(self.test_dir, "wpa_supplicant.conf")
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def create_test_wpa_conf(self, content: str):
        """Create a test wpa_supplicant.conf file."""
        with open(self.wpa_conf_path, 'w') as f:
            f.write(content)
    
    def test_load_empty_file(self):
        """Test loading an empty wpa_supplicant.conf."""
        self.create_test_wpa_conf("")
        handler = WPAConfHandler(self.wpa_conf_path)
        self.assertTrue(handler.load())
        self.assertEqual(len(handler.networks), 0)
    
    def test_load_basic_config(self):
        """Test loading a basic wpa_supplicant.conf."""
        content = """ctrl_interface=/var/run/wpa_supplicant
update_config=1

network={
    ssid="HomeNetwork"
    psk="mypassword"
}
"""
        self.create_test_wpa_conf(content)
        handler = WPAConfHandler(self.wpa_conf_path)
        self.assertTrue(handler.load())
        
        self.assertEqual(len(handler.networks), 1)
        self.assertEqual(handler.networks[0].ssid, "HomeNetwork")
        self.assertEqual(handler.networks[0].psk, "mypassword")
    
    def test_load_multiple_networks(self):
        """Test loading multiple networks."""
        content = """ctrl_interface=/var/run/wpa_supplicant

network={
    ssid="Home"
    psk="password1"
    priority=5
}

network={
    ssid="Work"
    psk="password2"
    priority=10
}

network={
    ssid="Guest"
    key_mgmt=NONE
}
"""
        self.create_test_wpa_conf(content)
        handler = WPAConfHandler(self.wpa_conf_path)
        self.assertTrue(handler.load())
        
        self.assertEqual(len(handler.networks), 3)
        
        # Check priorities
        work_net = handler.get_network("Work")
        self.assertIsNotNone(work_net)
        self.assertEqual(work_net.priority, 10)
        
        # Check open network
        guest_net = handler.get_network("Guest")
        self.assertIsNotNone(guest_net)
        self.assertEqual(guest_net.key_mgmt, "NONE")
    
    def test_add_network(self):
        """Test adding a new network."""
        self.create_test_wpa_conf("")
        handler = WPAConfHandler(self.wpa_conf_path)
        handler.load()
        
        self.assertTrue(handler.add_network("NewNetwork", "password123", "WPA2-PSK", priority=5))
        
        self.assertEqual(len(handler.networks), 1)
        network = handler.networks[0]
        self.assertEqual(network.ssid, "NewNetwork")
        self.assertEqual(network.psk, "password123")
        self.assertEqual(network.priority, 5)
    
    def test_add_open_network(self):
        """Test adding an open network."""
        self.create_test_wpa_conf("")
        handler = WPAConfHandler(self.wpa_conf_path)
        handler.load()
        
        self.assertTrue(handler.add_network("OpenWiFi", None, "NONE"))
        
        network = handler.networks[0]
        self.assertEqual(network.ssid, "OpenWiFi")
        self.assertEqual(network.key_mgmt, "NONE")
        self.assertIsNone(network.psk)
    
    def test_remove_network(self):
        """Test removing a network."""
        content = """network={
    ssid="Network1"
    psk="password1"
}

network={
    ssid="Network2"
    psk="password2"
}
"""
        self.create_test_wpa_conf(content)
        handler = WPAConfHandler(self.wpa_conf_path)
        handler.load()
        
        self.assertEqual(len(handler.networks), 2)
        
        self.assertTrue(handler.remove_network("Network1"))
        self.assertEqual(len(handler.networks), 1)
        self.assertEqual(handler.networks[0].ssid, "Network2")
    
    def test_update_network(self):
        """Test updating a network."""
        content = """network={
    ssid="MyNetwork"
    psk="oldpassword"
    priority=5
}
"""
        self.create_test_wpa_conf(content)
        handler = WPAConfHandler(self.wpa_conf_path)
        handler.load()
        
        self.assertTrue(handler.update_network("MyNetwork", password="newpassword", priority=10))
        
        network = handler.get_network("MyNetwork")
        self.assertEqual(network.psk, "newpassword")
        self.assertEqual(network.priority, 10)
    
    def test_list_networks(self):
        """Test listing all networks."""
        content = """network={
    ssid="Net1"
    psk="pass1"
    priority=1
}

network={
    ssid="Net2"
    psk="pass2"
    priority=2
}
"""
        self.create_test_wpa_conf(content)
        handler = WPAConfHandler(self.wpa_conf_path)
        handler.load()
        
        networks = handler.list_networks()
        self.assertEqual(len(networks), 2)
        
        ssids = [n['ssid'] for n in networks]
        self.assertIn('Net1', ssids)
        self.assertIn('Net2', ssids)
    
    def test_save_and_reload(self):
        """Test saving and reloading configuration."""
        self.create_test_wpa_conf("")
        handler = WPAConfHandler(self.wpa_conf_path)
        handler.load()
        
        handler.ctrl_interface = "/var/run/wpa_supplicant"
        handler.add_network("TestNet", "testpass", priority=5)
        
        self.assertTrue(handler.save(backup=False))
        
        # Reload and verify
        handler2 = WPAConfHandler(self.wpa_conf_path)
        handler2.load()
        
        self.assertEqual(handler2.ctrl_interface, "/var/run/wpa_supplicant")
        self.assertEqual(len(handler2.networks), 1)
        
        network = handler2.networks[0]
        self.assertEqual(network.ssid, "TestNet")
        self.assertEqual(network.psk, "testpass")
        self.assertEqual(network.priority, 5)
    
    def test_backup_creation(self):
        """Test that backup is created on save."""
        content = """network={
    ssid="Original"
    psk="original"
}
"""
        self.create_test_wpa_conf(content)
        handler = WPAConfHandler(self.wpa_conf_path)
        handler.load()
        
        handler.add_network("New", "newpass")
        handler.save(backup=True)
        
        # Check backup exists
        backup_path = f"{self.wpa_conf_path}.bak"
        self.assertTrue(os.path.exists(backup_path))
        
        # Check backup has original content
        with open(backup_path, 'r') as f:
            backup_content = f.read()
        self.assertIn('Original', backup_content)
    
    def test_clear_networks(self):
        """Test clearing all networks."""
        content = """network={
    ssid="Net1"
    psk="pass1"
}

network={
    ssid="Net2"
    psk="pass2"
}
"""
        self.create_test_wpa_conf(content)
        handler = WPAConfHandler(self.wpa_conf_path)
        handler.load()
        
        self.assertEqual(len(handler.networks), 2)
        
        handler.clear_networks()
        self.assertEqual(len(handler.networks), 0)
    
    def test_validation_duplicate_ssid(self):
        """Test validation catches duplicate SSIDs."""
        self.create_test_wpa_conf("")
        handler = WPAConfHandler(self.wpa_conf_path)
        handler.load()
        
        handler.add_network("Duplicate", "pass1")
        handler.add_network("Duplicate", "pass2")
        
        valid, errors = handler.validate()
        self.assertFalse(valid)
        self.assertGreater(len(errors), 0)
    
    def test_validation_no_ssid(self):
        """Test validation catches missing SSID."""
        self.create_test_wpa_conf("")
        handler = WPAConfHandler(self.wpa_conf_path)
        handler.load()
        
        network = WPANetwork()
        network.psk = "password"
        handler.networks.append(network)
        
        valid, errors = handler.validate()
        self.assertFalse(valid)
    
    def test_hidden_network(self):
        """Test adding a hidden network."""
        self.create_test_wpa_conf("")
        handler = WPAConfHandler(self.wpa_conf_path)
        handler.load()
        
        handler.add_network("HiddenSSID", "password", scan_ssid=True)
        
        network = handler.get_network("HiddenSSID")
        self.assertEqual(network.scan_ssid, 1)
    
    def test_parse_with_comments(self):
        """Test parsing configuration with comments."""
        content = """# Main configuration file
ctrl_interface=/var/run/wpa_supplicant

# Home network
network={
    ssid="Home"
    psk="password"
}

# Work network
network={
    ssid="Work"
    psk="workpass"
}
"""
        self.create_test_wpa_conf(content)
        handler = WPAConfHandler(self.wpa_conf_path)
        self.assertTrue(handler.load())
        
        self.assertEqual(len(handler.networks), 2)
        self.assertGreater(len(handler.header_comments), 0)


if __name__ == '__main__':
    unittest.main()
