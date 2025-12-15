"""Backup management panel for BSD Network Manager."""

import wx
import logging
from ..backend.backup_handler import BackupHandler


class BackupPanel(wx.Panel):
    """
    Panel for managing network configuration backups.
    
    Provides interface to list, create, restore, and delete backups.
    """
    
    def __init__(self, parent, network_manager):
        """
        Initialize the backup panel.
        
        Args:
            parent: Parent window
            network_manager: NetworkManager instance
        """
        super().__init__(parent)
        self.network_manager = network_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize backup handler
        self.backup_handler = BackupHandler()
        
        self._create_ui()
        self.refresh()
    
    def _create_ui(self):
        """Create the user interface."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Title
        title = wx.StaticText(self, label="Configuration Backups")
        title_font = title.GetFont()
        title_font.PointSize += 2
        title_font = title_font.Bold()
        title.SetFont(title_font)
        main_sizer.Add(title, 0, wx.ALL, 10)
        
        # Backup method info
        if self.backup_handler.is_zfs_available():
            info_text = "Backup Method: ZFS Snapshots (enabled)"
            info_color = wx.Colour(0, 150, 0)
        else:
            info_text = "Backup Method: File-based backup"
            info_color = wx.Colour(100, 100, 100)
        
        info_label = wx.StaticText(self, label=info_text)
        info_label.SetForegroundColour(info_color)
        main_sizer.Add(info_label, 0, wx.ALL, 5)
        
        # Backup list
        list_box = wx.StaticBox(self, label="Available Backups")
        list_sizer = wx.StaticBoxSizer(list_box, wx.VERTICAL)
        
        self.backup_list = wx.ListCtrl(
            self,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN
        )
        self.backup_list.AppendColumn("Timestamp", width=180)
        self.backup_list.AppendColumn("Method", width=80)
        self.backup_list.AppendColumn("Reason", width=300)
        self.backup_list.AppendColumn("Hostname", width=150)
        
        self.backup_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_backup_selected)
        self.backup_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_restore_backup)
        list_sizer.Add(self.backup_list, 1, wx.EXPAND | wx.ALL, 5)
        
        main_sizer.Add(list_sizer, 1, wx.EXPAND | wx.ALL, 5)
        
        # Backup details
        details_box = wx.StaticBox(self, label="Backup Details")
        details_sizer = wx.StaticBoxSizer(details_box, wx.VERTICAL)
        
        self.details_text = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 80)
        )
        details_sizer.Add(self.details_text, 1, wx.EXPAND | wx.ALL, 5)
        
        main_sizer.Add(details_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Action buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.refresh_btn = wx.Button(self, label="Refresh")
        self.refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh)
        button_sizer.Add(self.refresh_btn, 0, wx.ALL, 5)
        
        button_sizer.AddStretchSpacer()
        
        self.create_btn = wx.Button(self, label="Create Backup Now")
        self.create_btn.Bind(wx.EVT_BUTTON, self.on_create_backup)
        button_sizer.Add(self.create_btn, 0, wx.ALL, 5)
        
        self.restore_btn = wx.Button(self, label="Restore")
        self.restore_btn.Bind(wx.EVT_BUTTON, self.on_restore_backup)
        self.restore_btn.Enable(False)
        button_sizer.Add(self.restore_btn, 0, wx.ALL, 5)
        
        self.delete_btn = wx.Button(self, label="Delete")
        self.delete_btn.Bind(wx.EVT_BUTTON, self.on_delete_backup)
        self.delete_btn.Enable(False)
        button_sizer.Add(self.delete_btn, 0, wx.ALL, 5)
        
        main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Help text
        help_text = wx.StaticText(
            self,
            label="Tip: Backups are created automatically before applying configuration changes.\n"
                  "Double-click a backup to restore it."
        )
        help_text.SetForegroundColour(wx.Colour(100, 100, 100))
        main_sizer.Add(help_text, 0, wx.ALL, 10)
        
        self.SetSizer(main_sizer)
    
    def refresh(self):
        """Refresh the backup list."""
        self.logger.info("Refreshing backup list")
        self.backup_list.DeleteAllItems()
        
        try:
            backups = self.backup_handler.list_backups()
            
            for backup in backups:
                index = self.backup_list.GetItemCount()
                self.backup_list.InsertItem(index, backup.timestamp)
                self.backup_list.SetItem(index, 1, backup.method)
                self.backup_list.SetItem(index, 2, backup.reason or "No reason specified")
                self.backup_list.SetItem(index, 3, backup.hostname or "Unknown")
                
                # Store backup ID in item data
                if backup.method == 'zfs' and backup.snapshot_name:
                    self.backup_list.SetItemData(index, hash(backup.snapshot_name))
                else:
                    # Extract timestamp from ISO format
                    timestamp = backup.timestamp.replace(':', '').replace('-', '')[:15]
                    self.backup_list.SetItemData(index, hash(timestamp))
        except Exception as e:
            self.logger.error(f"Error refreshing backups: {e}")
            wx.MessageBox(
                f"Error loading backups:\n{str(e)}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )
    
    def on_backup_selected(self, event):
        """Handle backup selection."""
        index = self.backup_list.GetFirstSelected()
        if index == -1:
            return
        
        # Get backup details
        timestamp = self.backup_list.GetItemText(index, 0)
        method = self.backup_list.GetItemText(index, 1)
        reason = self.backup_list.GetItemText(index, 2)
        hostname = self.backup_list.GetItemText(index, 3)
        
        # Find the actual backup
        backups = self.backup_handler.list_backups()
        selected_backup = None
        for backup in backups:
            if backup.timestamp == timestamp:
                selected_backup = backup
                break
        
        # Display details
        details = f"Timestamp: {timestamp}\n"
        details += f"Method: {method}\n"
        details += f"Reason: {reason}\n"
        details += f"Hostname: {hostname}\n"
        
        if selected_backup:
            if selected_backup.user:
                details += f"User: {selected_backup.user}\n"
            if selected_backup.files:
                details += f"Files: {', '.join(selected_backup.files)}\n"
            if selected_backup.snapshot_name:
                details += f"Snapshot: {selected_backup.snapshot_name}\n"
        
        self.details_text.SetValue(details)
        
        # Enable buttons
        self.restore_btn.Enable(True)
        self.delete_btn.Enable(True)
    
    def on_refresh(self, event):
        """Handle refresh button click."""
        self.refresh()
    
    def on_create_backup(self, event):
        """Handle create backup button click."""
        # Get reason from user
        dialog = wx.TextEntryDialog(
            self,
            "Enter a reason for this backup:",
            "Create Backup",
            "Manual backup"
        )
        
        if dialog.ShowModal() == wx.ID_OK:
            reason = dialog.GetValue()
            
            try:
                backup_id = self.backup_handler.create_backup(reason)
                
                if backup_id:
                    wx.MessageBox(
                        f"Backup created successfully!\n\n"
                        f"Backup ID: {backup_id}",
                        "Success",
                        wx.OK | wx.ICON_INFORMATION
                    )
                    self.refresh()
                else:
                    wx.MessageBox(
                        "Failed to create backup. Check logs for details.",
                        "Error",
                        wx.OK | wx.ICON_ERROR
                    )
            except Exception as e:
                self.logger.error(f"Error creating backup: {e}")
                wx.MessageBox(
                    f"Error creating backup:\n{str(e)}",
                    "Error",
                    wx.OK | wx.ICON_ERROR
                )
        
        dialog.Destroy()
    
    def on_restore_backup(self, event):
        """Handle restore backup button click."""
        index = self.backup_list.GetFirstSelected()
        if index == -1:
            return
        
        timestamp = self.backup_list.GetItemText(index, 0)
        method = self.backup_list.GetItemText(index, 1)
        
        # Find the backup
        backups = self.backup_handler.list_backups()
        selected_backup = None
        for backup in backups:
            if backup.timestamp == timestamp:
                selected_backup = backup
                break
        
        if not selected_backup:
            wx.MessageBox(
                "Could not find backup details.",
                "Error",
                wx.OK | wx.ICON_ERROR
            )
            return
        
        # Confirm restoration
        result = wx.MessageBox(
            f"Restore configuration from backup?\n\n"
            f"Timestamp: {timestamp}\n"
            f"Method: {method}\n"
            f"Reason: {selected_backup.reason}\n\n"
            f"WARNING: This will overwrite current configuration!\n"
            f"Current configuration will be backed up first.",
            "Confirm Restore",
            wx.YES_NO | wx.ICON_WARNING
        )
        
        if result == wx.YES:
            try:
                # Create backup of current state first
                self.backup_handler.create_backup("Before restore")
                
                # Determine backup ID
                if method == 'zfs' and selected_backup.snapshot_name:
                    backup_id = selected_backup.snapshot_name
                else:
                    # Extract timestamp
                    backup_id = selected_backup.timestamp.replace(':', '').replace('-', '')[:15]
                
                # Restore
                if self.backup_handler.restore_backup(backup_id):
                    wx.MessageBox(
                        f"Configuration restored successfully!\n\n"
                        f"You may need to restart network services or reboot\n"
                        f"for changes to take effect.",
                        "Success",
                        wx.OK | wx.ICON_INFORMATION
                    )
                    self.refresh()
                else:
                    wx.MessageBox(
                        "Failed to restore backup. Check logs for details.",
                        "Error",
                        wx.OK | wx.ICON_ERROR
                    )
            except Exception as e:
                self.logger.error(f"Error restoring backup: {e}")
                wx.MessageBox(
                    f"Error restoring backup:\n{str(e)}",
                    "Error",
                    wx.OK | wx.ICON_ERROR
                )
    
    def on_delete_backup(self, event):
        """Handle delete backup button click."""
        index = self.backup_list.GetFirstSelected()
        if index == -1:
            return
        
        timestamp = self.backup_list.GetItemText(index, 0)
        method = self.backup_list.GetItemText(index, 1)
        
        # Find the backup
        backups = self.backup_handler.list_backups()
        selected_backup = None
        for backup in backups:
            if backup.timestamp == timestamp:
                selected_backup = backup
                break
        
        if not selected_backup:
            wx.MessageBox(
                "Could not find backup details.",
                "Error",
                wx.OK | wx.ICON_ERROR
            )
            return
        
        # Confirm deletion
        result = wx.MessageBox(
            f"Delete backup?\n\n"
            f"Timestamp: {timestamp}\n"
            f"Method: {method}\n\n"
            f"This action cannot be undone.",
            "Confirm Deletion",
            wx.YES_NO | wx.ICON_WARNING
        )
        
        if result == wx.YES:
            try:
                # Determine backup ID
                if method == 'zfs' and selected_backup.snapshot_name:
                    backup_id = selected_backup.snapshot_name
                else:
                    backup_id = selected_backup.timestamp.replace(':', '').replace('-', '')[:15]
                
                # Delete
                if self.backup_handler.delete_backup(backup_id):
                    wx.MessageBox(
                        "Backup deleted successfully!",
                        "Success",
                        wx.OK | wx.ICON_INFORMATION
                    )
                    self.refresh()
                else:
                    wx.MessageBox(
                        "Failed to delete backup. Check logs for details.",
                        "Error",
                        wx.OK | wx.ICON_ERROR
                    )
            except Exception as e:
                self.logger.error(f"Error deleting backup: {e}")
                wx.MessageBox(
                    f"Error deleting backup:\n{str(e)}",
                    "Error",
                    wx.OK | wx.ICON_ERROR
                )
