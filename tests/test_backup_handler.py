"""Tests for backup handler."""

import unittest
import tempfile
import os
import shutil
from pathlib import Path
from bsd_netgui.backend.backup_handler import BackupHandler, BackupMetadata


class TestBackupMetadata(unittest.TestCase):
    """Test cases for BackupMetadata."""
    
    def test_metadata_creation(self):
        """Test creating metadata."""
        metadata = BackupMetadata()
        self.assertIsNotNone(metadata.timestamp)
        self.assertEqual(metadata.method, "file")
    
    def test_metadata_to_dict(self):
        """Test converting metadata to dict."""
        metadata = BackupMetadata()
        metadata.reason = "Test backup"
        metadata.files = ['rc.conf', 'wpa_supplicant.conf']
        
        data = metadata.to_dict()
        
        self.assertIn('timestamp', data)
        self.assertEqual(data['method'], 'file')
        self.assertEqual(data['reason'], 'Test backup')
        self.assertEqual(len(data['files']), 2)
    
    def test_metadata_from_dict(self):
        """Test creating metadata from dict."""
        data = {
            'timestamp': '2025-12-15T10:00:00',
            'method': 'zfs',
            'files': ['rc.conf'],
            'reason': 'Test',
            'user': 'root',
            'hostname': 'test-host',
            'snapshot_name': 'tank@netgui-20251215'
        }
        
        metadata = BackupMetadata.from_dict(data)
        
        self.assertEqual(metadata.timestamp, '2025-12-15T10:00:00')
        self.assertEqual(metadata.method, 'zfs')
        self.assertEqual(metadata.reason, 'Test')


class TestBackupHandler(unittest.TestCase):
    """Test cases for BackupHandler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.backup_dir = os.path.join(self.test_dir, "backups")
        self.config_dir = os.path.join(self.test_dir, "etc")
        os.makedirs(self.config_dir)
        
        # Create test config files
        self.test_configs = {
            'rc.conf': 'hostname="test"\nifconfig_em0="DHCP"\n',
            'wpa_supplicant.conf': 'network={\n    ssid="Test"\n}\n',
            'resolv.conf': 'nameserver 8.8.8.8\n'
        }
        
        for filename, content in self.test_configs.items():
            with open(os.path.join(self.config_dir, filename), 'w') as f:
                f.write(content)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_handler_creation(self):
        """Test creating a backup handler."""
        handler = BackupHandler(self.backup_dir)
        self.assertEqual(str(handler.backup_dir), self.backup_dir)
    
    def test_zfs_detection(self):
        """Test ZFS availability detection."""
        handler = BackupHandler(self.backup_dir)
        # Just check it doesn't crash
        self.assertIsNotNone(handler.zfs_available)
    
    def test_file_backup_creation(self):
        """Test creating a file-based backup."""
        handler = BackupHandler(self.backup_dir)
        
        # Temporarily override CONFIG_FILES to point to test directory
        original_files = handler.CONFIG_FILES
        handler.CONFIG_FILES = [
            os.path.join(self.config_dir, 'rc.conf'),
            os.path.join(self.config_dir, 'wpa_supplicant.conf'),
            os.path.join(self.config_dir, 'resolv.conf')
        ]
        
        backup_id = handler._create_file_backup("Test backup")
        
        self.assertIsNotNone(backup_id)
        self.assertTrue(os.path.exists(self.backup_dir))
        
        # Check backup directory exists
        backup_path = os.path.join(self.backup_dir, backup_id)
        self.assertTrue(os.path.exists(backup_path))
        
        # Check metadata exists
        metadata_path = os.path.join(backup_path, "backup.json")
        self.assertTrue(os.path.exists(metadata_path))
        
        # Check files were backed up
        for filename in self.test_configs.keys():
            backed_up_file = os.path.join(backup_path, filename)
            self.assertTrue(os.path.exists(backed_up_file))
        
        handler.CONFIG_FILES = original_files
    
    def test_list_backups(self):
        """Test listing backups."""
        handler = BackupHandler(self.backup_dir)
        
        # Override CONFIG_FILES
        original_files = handler.CONFIG_FILES
        handler.CONFIG_FILES = [
            os.path.join(self.config_dir, 'rc.conf')
        ]
        
        # Create a backup
        handler._create_file_backup("First backup")
        
        # List backups
        backups = handler.list_backups()
        
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].reason, "First backup")
        
        handler.CONFIG_FILES = original_files
    
    def test_restore_file_backup(self):
        """Test restoring from a file backup."""
        handler = BackupHandler(self.backup_dir)
        
        # Override CONFIG_FILES
        original_files = handler.CONFIG_FILES
        handler.CONFIG_FILES = [
            os.path.join(self.config_dir, 'rc.conf')
        ]
        
        # Create backup
        backup_id = handler._create_file_backup("Test backup")
        
        # Modify original file
        rc_conf_path = os.path.join(self.config_dir, 'rc.conf')
        with open(rc_conf_path, 'w') as f:
            f.write('hostname="modified"\n')
        
        # Restore backup
        success = handler._restore_file_backup(backup_id)
        self.assertTrue(success)
        
        # Check file was restored
        with open(rc_conf_path, 'r') as f:
            content = f.read()
        self.assertIn('test', content)
        self.assertNotIn('modified', content)
        
        handler.CONFIG_FILES = original_files
    
    def test_delete_file_backup(self):
        """Test deleting a file backup."""
        handler = BackupHandler(self.backup_dir)
        
        # Override CONFIG_FILES
        original_files = handler.CONFIG_FILES
        handler.CONFIG_FILES = [
            os.path.join(self.config_dir, 'rc.conf')
        ]
        
        # Create backup
        backup_id = handler._create_file_backup("Test backup")
        backup_path = os.path.join(self.backup_dir, backup_id)
        
        self.assertTrue(os.path.exists(backup_path))
        
        # Delete backup
        success = handler._delete_file_backup(backup_id)
        self.assertTrue(success)
        self.assertFalse(os.path.exists(backup_path))
        
        handler.CONFIG_FILES = original_files
    
    def test_cleanup_file_backups(self):
        """Test automatic cleanup of old backups."""
        handler = BackupHandler(self.backup_dir)
        
        # Override CONFIG_FILES
        original_files = handler.CONFIG_FILES
        handler.CONFIG_FILES = [
            os.path.join(self.config_dir, 'rc.conf')
        ]
        
        # Create multiple backups
        backup_ids = []
        for i in range(5):
            backup_id = handler._create_file_backup(f"Backup {i}")
            backup_ids.append(backup_id)
            import time
            time.sleep(0.1)  # Ensure different timestamps
        
        # Keep only 2
        handler._cleanup_file_backups(keep=2)
        
        # Check only 2 remain
        remaining = []
        for item in Path(self.backup_dir).iterdir():
            if item.is_dir():
                remaining.append(item.name)
        
        self.assertEqual(len(remaining), 2)
        
        # Most recent should remain
        self.assertIn(backup_ids[-1], remaining)
        self.assertIn(backup_ids[-2], remaining)
        
        handler.CONFIG_FILES = original_files


if __name__ == '__main__':
    unittest.main()
