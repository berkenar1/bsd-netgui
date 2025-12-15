"""Backup and restore system for network configuration files.

This module provides backup functionality with ZFS snapshot support
and file-based backup as a fallback.
"""

import os
import json
import shutil
import logging
import subprocess
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from ..utils.system_utils import execute_command


class BackupMetadata:
    """Represents backup metadata."""
    
    def __init__(self):
        """Initialize BackupMetadata."""
        self.timestamp: str = datetime.now().isoformat()
        self.method: str = "file"  # "zfs" or "file"
        self.files: List[str] = []
        self.reason: str = ""
        self.user: str = ""
        self.hostname: str = ""
        self.snapshot_name: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp,
            'method': self.method,
            'files': self.files,
            'reason': self.reason,
            'user': self.user,
            'hostname': self.hostname,
            'snapshot_name': self.snapshot_name
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BackupMetadata':
        """Create from dictionary."""
        metadata = cls()
        metadata.timestamp = data.get('timestamp', '')
        metadata.method = data.get('method', 'file')
        metadata.files = data.get('files', [])
        metadata.reason = data.get('reason', '')
        metadata.user = data.get('user', '')
        metadata.hostname = data.get('hostname', '')
        metadata.snapshot_name = data.get('snapshot_name')
        return metadata


class BackupHandler:
    """
    Handles backup and restore of network configuration files.
    
    Features:
    - ZFS snapshot support when available
    - File-based backup as fallback
    - Automatic cleanup of old backups
    - Backup metadata tracking
    """
    
    # Files to backup
    CONFIG_FILES = [
        '/etc/rc.conf',
        '/etc/rc.conf.local',
        '/etc/wpa_supplicant.conf',
        '/etc/resolv.conf',
        '/etc/dhclient.conf'
    ]
    
    def __init__(self, backup_dir: str = "/var/backups/bsd-netgui"):
        """
        Initialize the BackupHandler.
        
        Args:
            backup_dir: Directory for file-based backups
        """
        self.logger = logging.getLogger(__name__)
        self.backup_dir = Path(backup_dir)
        self.zfs_available = self._check_zfs_available()
        self.etc_dataset = self._get_etc_dataset() if self.zfs_available else None
        
        # Create backup directory if using file-based backup
        if not self.zfs_available:
            try:
                self.backup_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.logger.error(f"Could not create backup directory: {e}")
    
    def _check_zfs_available(self) -> bool:
        """
        Check if ZFS is available on the system.
        
        Returns:
            True if ZFS is available
        """
        try:
            success, stdout, stderr = execute_command(['which', 'zfs'])
            if success:
                self.logger.info("ZFS is available")
                return True
            return False
        except Exception as e:
            self.logger.debug(f"ZFS not available: {e}")
            return False
    
    def _get_etc_dataset(self) -> Optional[str]:
        """
        Get the ZFS dataset that contains /etc.
        
        Returns:
            Dataset name or None
        """
        try:
            success, stdout, stderr = execute_command(['zfs', 'list', '-H', '-o', 'name,mountpoint'])
            if not success:
                return None
            
            # Parse output to find dataset mounted at /etc or parent of /etc
            for line in stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    dataset, mountpoint = parts[0], parts[1]
                    # Check if /etc is under this mountpoint
                    if mountpoint == '/etc' or (mountpoint == '/' or '/etc'.startswith(mountpoint + '/')):
                        self.logger.info(f"Found ZFS dataset for /etc: {dataset}")
                        return dataset
            
            return None
        except Exception as e:
            self.logger.error(f"Error getting ZFS dataset: {e}")
            return None
    
    def create_backup(self, reason: str = "Manual backup") -> Optional[str]:
        """
        Create a backup of network configuration files.
        
        Args:
            reason: Reason for the backup
        
        Returns:
            Backup identifier (timestamp or snapshot name) or None on failure
        """
        try:
            # Use ZFS snapshot if available
            if self.zfs_available and self.etc_dataset:
                return self._create_zfs_backup(reason)
            else:
                return self._create_file_backup(reason)
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return None
    
    def _create_zfs_backup(self, reason: str) -> Optional[str]:
        """
        Create a ZFS snapshot backup.
        
        Args:
            reason: Reason for backup
        
        Returns:
            Snapshot name or None
        """
        try:
            # Generate snapshot name
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            snapshot_name = f"{self.etc_dataset}@netgui-{timestamp}"
            
            # Create snapshot
            success, stdout, stderr = execute_command(['zfs', 'snapshot', snapshot_name])
            if not success:
                self.logger.error(f"Failed to create ZFS snapshot: {stderr}")
                return None
            
            # Create metadata
            metadata = BackupMetadata()
            metadata.method = "zfs"
            metadata.reason = reason
            metadata.snapshot_name = snapshot_name
            metadata.user = os.getenv('USER', 'root')
            
            # Get hostname
            try:
                import socket
                metadata.hostname = socket.gethostname()
            except:
                metadata.hostname = "unknown"
            
            # Save metadata in backup dir
            metadata_path = self.backup_dir / f"snapshot-{timestamp}.json"
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            with open(metadata_path, 'w') as f:
                json.dump(metadata.to_dict(), f, indent=2)
            
            self.logger.info(f"Created ZFS snapshot: {snapshot_name}")
            
            # Cleanup old snapshots
            self._cleanup_zfs_snapshots()
            
            return snapshot_name
        except Exception as e:
            self.logger.error(f"Error creating ZFS snapshot: {e}")
            return None
    
    def _create_file_backup(self, reason: str) -> Optional[str]:
        """
        Create a file-based backup.
        
        Args:
            reason: Reason for backup
        
        Returns:
            Backup timestamp or None
        """
        try:
            # Generate backup directory name
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_path = self.backup_dir / timestamp
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Create metadata
            metadata = BackupMetadata()
            metadata.method = "file"
            metadata.reason = reason
            metadata.user = os.getenv('USER', 'root')
            
            # Get hostname
            try:
                import socket
                metadata.hostname = socket.gethostname()
            except:
                metadata.hostname = "unknown"
            
            # Backup each config file
            for config_file in self.CONFIG_FILES:
                source_path = Path(config_file)
                if not source_path.exists():
                    self.logger.debug(f"Config file does not exist: {config_file}")
                    continue
                
                # Copy file preserving permissions and timestamps
                dest_path = backup_path / source_path.name
                shutil.copy2(source_path, dest_path)
                metadata.files.append(source_path.name)
                self.logger.debug(f"Backed up: {config_file}")
            
            # Save metadata
            metadata_path = backup_path / "backup.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata.to_dict(), f, indent=2)
            
            self.logger.info(f"Created file backup: {backup_path}")
            
            # Cleanup old backups
            self._cleanup_file_backups()
            
            return timestamp
        except Exception as e:
            self.logger.error(f"Error creating file backup: {e}")
            return None
    
    def list_backups(self) -> List[BackupMetadata]:
        """
        List all available backups.
        
        Returns:
            List of BackupMetadata objects
        """
        backups = []
        
        try:
            # List file-based backups
            if self.backup_dir.exists():
                for item in self.backup_dir.iterdir():
                    if item.is_dir():
                        # Directory-based backup
                        metadata_path = item / "backup.json"
                        if metadata_path.exists():
                            with open(metadata_path, 'r') as f:
                                data = json.load(f)
                            backups.append(BackupMetadata.from_dict(data))
                    elif item.suffix == '.json' and item.name.startswith('snapshot-'):
                        # ZFS snapshot metadata
                        with open(item, 'r') as f:
                            data = json.load(f)
                        backups.append(BackupMetadata.from_dict(data))
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x.timestamp, reverse=True)
        except Exception as e:
            self.logger.error(f"Error listing backups: {e}")
        
        return backups
    
    def restore_backup(self, backup_id: str) -> bool:
        """
        Restore from a backup.
        
        Args:
            backup_id: Backup identifier (timestamp or snapshot name)
        
        Returns:
            True if successful
        """
        try:
            # Check if it's a ZFS snapshot
            if '@netgui-' in backup_id:
                return self._restore_zfs_backup(backup_id)
            else:
                return self._restore_file_backup(backup_id)
        except Exception as e:
            self.logger.error(f"Error restoring backup: {e}")
            return False
    
    def _restore_zfs_backup(self, snapshot_name: str) -> bool:
        """
        Restore from a ZFS snapshot.
        
        Args:
            snapshot_name: Full snapshot name
        
        Returns:
            True if successful
        """
        try:
            # Rollback to snapshot
            success, stdout, stderr = execute_command(['zfs', 'rollback', snapshot_name])
            if not success:
                self.logger.error(f"Failed to rollback ZFS snapshot: {stderr}")
                return False
            
            self.logger.info(f"Restored from ZFS snapshot: {snapshot_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error restoring ZFS snapshot: {e}")
            return False
    
    def _restore_file_backup(self, timestamp: str) -> bool:
        """
        Restore from a file-based backup.
        
        Args:
            timestamp: Backup timestamp
        
        Returns:
            True if successful
        """
        try:
            backup_path = self.backup_dir / timestamp
            if not backup_path.exists():
                self.logger.error(f"Backup not found: {backup_path}")
                return False
            
            # Load metadata
            metadata_path = backup_path / "backup.json"
            if not metadata_path.exists():
                self.logger.error(f"Backup metadata not found: {metadata_path}")
                return False
            
            with open(metadata_path, 'r') as f:
                metadata = BackupMetadata.from_dict(json.load(f))
            
            # Restore each file
            for filename in metadata.files:
                source_path = backup_path / filename
                dest_path = None
                
                # Find the original path for this file
                for config_file in self.CONFIG_FILES:
                    if Path(config_file).name == filename:
                        dest_path = Path(config_file)
                        break
                
                if not dest_path:
                    self.logger.warning(f"Unknown config file: {filename}")
                    continue
                
                if not source_path.exists():
                    self.logger.warning(f"Backup file not found: {source_path}")
                    continue
                
                # Restore file
                shutil.copy2(source_path, dest_path)
                self.logger.info(f"Restored: {dest_path}")
            
            self.logger.info(f"Restored from file backup: {timestamp}")
            return True
        except Exception as e:
            self.logger.error(f"Error restoring file backup: {e}")
            return False
    
    def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a backup.
        
        Args:
            backup_id: Backup identifier
        
        Returns:
            True if successful
        """
        try:
            # Check if it's a ZFS snapshot
            if '@netgui-' in backup_id:
                return self._delete_zfs_backup(backup_id)
            else:
                return self._delete_file_backup(backup_id)
        except Exception as e:
            self.logger.error(f"Error deleting backup: {e}")
            return False
    
    def _delete_zfs_backup(self, snapshot_name: str) -> bool:
        """Delete a ZFS snapshot."""
        try:
            success, stdout, stderr = execute_command(['zfs', 'destroy', snapshot_name])
            if not success:
                self.logger.error(f"Failed to destroy ZFS snapshot: {stderr}")
                return False
            
            # Also delete metadata file
            timestamp = snapshot_name.split('@netgui-')[1] if '@netgui-' in snapshot_name else None
            if timestamp:
                metadata_path = self.backup_dir / f"snapshot-{timestamp}.json"
                if metadata_path.exists():
                    metadata_path.unlink()
            
            self.logger.info(f"Deleted ZFS snapshot: {snapshot_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting ZFS snapshot: {e}")
            return False
    
    def _delete_file_backup(self, timestamp: str) -> bool:
        """Delete a file-based backup."""
        try:
            backup_path = self.backup_dir / timestamp
            if backup_path.exists():
                shutil.rmtree(backup_path)
                self.logger.info(f"Deleted file backup: {timestamp}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting file backup: {e}")
            return False
    
    def _cleanup_zfs_snapshots(self, keep: int = 10):
        """
        Cleanup old ZFS snapshots, keeping the most recent ones.
        
        Args:
            keep: Number of snapshots to keep
        """
        try:
            # List all netgui snapshots
            success, stdout, stderr = execute_command(['zfs', 'list', '-H', '-t', 'snapshot', '-o', 'name'])
            if not success:
                return
            
            snapshots = []
            for line in stdout.strip().split('\n'):
                if '@netgui-' in line:
                    snapshots.append(line.strip())
            
            # Sort by name (which includes timestamp)
            snapshots.sort()
            
            # Delete old snapshots
            if len(snapshots) > keep:
                for snapshot in snapshots[:-keep]:
                    self._delete_zfs_backup(snapshot)
                    self.logger.info(f"Cleaned up old snapshot: {snapshot}")
        except Exception as e:
            self.logger.error(f"Error cleaning up ZFS snapshots: {e}")
    
    def _cleanup_file_backups(self, keep: int = 20):
        """
        Cleanup old file-based backups.
        
        Args:
            keep: Number of backups to keep
        """
        try:
            if not self.backup_dir.exists():
                return
            
            # List all backup directories
            backups = []
            for item in self.backup_dir.iterdir():
                if item.is_dir():
                    backups.append(item)
            
            # Sort by name (timestamp)
            backups.sort()
            
            # Delete old backups
            if len(backups) > keep:
                for backup in backups[:-keep]:
                    shutil.rmtree(backup)
                    self.logger.info(f"Cleaned up old backup: {backup.name}")
        except Exception as e:
            self.logger.error(f"Error cleaning up file backups: {e}")
    
    def get_backup_info(self, backup_id: str) -> Optional[BackupMetadata]:
        """
        Get information about a specific backup.
        
        Args:
            backup_id: Backup identifier
        
        Returns:
            BackupMetadata or None
        """
        backups = self.list_backups()
        for backup in backups:
            if backup.snapshot_name == backup_id or backup.timestamp.replace(':', '').replace('-', '')[:15] in backup_id:
                return backup
        return None
    
    def is_zfs_available(self) -> bool:
        """
        Check if ZFS backup is available.
        
        Returns:
            True if ZFS is available
        """
        return self.zfs_available and self.etc_dataset is not None
