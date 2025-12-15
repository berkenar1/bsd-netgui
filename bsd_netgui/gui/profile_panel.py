"""Network profile management panel for BSD Network Manager."""

import wx
import logging
from ..backend.profile_manager import ProfileManager, NetworkProfile


class ProfilePanel(wx.Panel):
    """
    Panel for managing network configuration profiles.
    
    Provides interface to create, edit, apply, and manage network profiles.
    """
    
    def __init__(self, parent, network_manager):
        """
        Initialize the profile panel.
        
        Args:
            parent: Parent window
            network_manager: NetworkManager instance
        """
        super().__init__(parent)
        self.network_manager = network_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize profile manager
        self.profile_manager = ProfileManager()
        self.profile_manager.load_profiles()
        
        self._create_ui()
        self.refresh()
    
    def _create_ui(self):
        """Create the user interface."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Title
        title = wx.StaticText(self, label="Network Profiles")
        title_font = title.GetFont()
        title_font.PointSize += 2
        title_font = title_font.Bold()
        title.SetFont(title_font)
        main_sizer.Add(title, 0, wx.ALL, 10)
        
        # Profile list
        list_box = wx.StaticBox(self, label="Saved Profiles")
        list_sizer = wx.StaticBoxSizer(list_box, wx.VERTICAL)
        
        self.profile_list = wx.ListCtrl(
            self,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN
        )
        self.profile_list.AppendColumn("Profile Name", width=200)
        self.profile_list.AppendColumn("Type", width=100)
        self.profile_list.AppendColumn("Interface", width=100)
        self.profile_list.AppendColumn("Auto-Connect", width=100)
        
        self.profile_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_profile_selected)
        self.profile_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_apply_profile)
        list_sizer.Add(self.profile_list, 1, wx.EXPAND | wx.ALL, 5)
        
        main_sizer.Add(list_sizer, 1, wx.EXPAND | wx.ALL, 5)
        
        # Profile details
        details_box = wx.StaticBox(self, label="Profile Details")
        details_sizer = wx.StaticBoxSizer(details_box, wx.VERTICAL)
        
        self.details_text = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 100)
        )
        details_sizer.Add(self.details_text, 1, wx.EXPAND | wx.ALL, 5)
        
        main_sizer.Add(details_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Action buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.refresh_btn = wx.Button(self, label="Refresh")
        self.refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh)
        button_sizer.Add(self.refresh_btn, 0, wx.ALL, 5)
        
        button_sizer.AddStretchSpacer()
        
        self.new_btn = wx.Button(self, label="New Profile")
        self.new_btn.Bind(wx.EVT_BUTTON, self.on_new_profile)
        button_sizer.Add(self.new_btn, 0, wx.ALL, 5)
        
        self.edit_btn = wx.Button(self, label="Edit")
        self.edit_btn.Bind(wx.EVT_BUTTON, self.on_edit_profile)
        self.edit_btn.Enable(False)
        button_sizer.Add(self.edit_btn, 0, wx.ALL, 5)
        
        self.apply_btn = wx.Button(self, label="Apply Profile")
        self.apply_btn.Bind(wx.EVT_BUTTON, self.on_apply_profile)
        self.apply_btn.Enable(False)
        button_sizer.Add(self.apply_btn, 0, wx.ALL, 5)
        
        self.delete_btn = wx.Button(self, label="Delete")
        self.delete_btn.Bind(wx.EVT_BUTTON, self.on_delete_profile)
        self.delete_btn.Enable(False)
        button_sizer.Add(self.delete_btn, 0, wx.ALL, 5)
        
        button_sizer.AddStretchSpacer()
        
        self.import_btn = wx.Button(self, label="Import")
        self.import_btn.Bind(wx.EVT_BUTTON, self.on_import_profile)
        button_sizer.Add(self.import_btn, 0, wx.ALL, 5)
        
        self.export_btn = wx.Button(self, label="Export")
        self.export_btn.Bind(wx.EVT_BUTTON, self.on_export_profile)
        self.export_btn.Enable(False)
        button_sizer.Add(self.export_btn, 0, wx.ALL, 5)
        
        main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        self.SetSizer(main_sizer)
    
    def refresh(self):
        """Refresh the profile list."""
        self.logger.info("Refreshing profile list")
        self.profile_list.DeleteAllItems()
        
        try:
            self.profile_manager.load_profiles()
            profiles = self.profile_manager.list_profiles()
            
            for profile in profiles:
                index = self.profile_list.GetItemCount()
                self.profile_list.InsertItem(index, profile.name)
                self.profile_list.SetItem(index, 1, profile.type)
                self.profile_list.SetItem(index, 2, profile.interface)
                self.profile_list.SetItem(index, 3, "Yes" if profile.autoconnect else "No")
        except Exception as e:
            self.logger.error(f"Error refreshing profiles: {e}")
            wx.MessageBox(
                f"Error loading profiles:\n{str(e)}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )
    
    def on_profile_selected(self, event):
        """Handle profile selection."""
        index = self.profile_list.GetFirstSelected()
        if index == -1:
            return
        
        profile_name = self.profile_list.GetItemText(index, 0)
        profile = self.profile_manager.get_profile(profile_name)
        
        if profile:
            # Display profile details
            details = f"Profile: {profile.name}\n"
            details += f"Type: {profile.type}\n"
            details += f"Interface: {profile.interface}\n"
            details += f"Auto-Connect: {'Yes' if profile.autoconnect else 'No'}\n"
            details += f"\nConfiguration:\n"
            for key, value in profile.config.items():
                # Mask passwords
                if 'password' in key.lower() or 'psk' in key.lower():
                    value = '*' * 8
                details += f"  {key}: {value}\n"
            
            self.details_text.SetValue(details)
            
            # Enable buttons
            self.edit_btn.Enable(True)
            self.apply_btn.Enable(True)
            self.delete_btn.Enable(True)
            self.export_btn.Enable(True)
    
    def on_refresh(self, event):
        """Handle refresh button click."""
        self.refresh()
    
    def on_new_profile(self, event):
        """Handle new profile button click."""
        dialog = ProfileWizardDialog(self, self.profile_manager)
        if dialog.ShowModal() == wx.ID_OK:
            profile = dialog.get_profile()
            if profile:
                # Save profile
                if self.profile_manager.save_profile(profile):
                    wx.MessageBox(
                        f"Profile '{profile.name}' created successfully!",
                        "Success",
                        wx.OK | wx.ICON_INFORMATION
                    )
                    self.refresh()
                else:
                    wx.MessageBox(
                        "Failed to save profile.",
                        "Error",
                        wx.OK | wx.ICON_ERROR
                    )
        dialog.Destroy()
    
    def on_edit_profile(self, event):
        """Handle edit profile button click."""
        index = self.profile_list.GetFirstSelected()
        if index == -1:
            return
        
        profile_name = self.profile_list.GetItemText(index, 0)
        profile = self.profile_manager.get_profile(profile_name)
        
        if profile:
            dialog = ProfileWizardDialog(self, self.profile_manager, profile)
            if dialog.ShowModal() == wx.ID_OK:
                updated_profile = dialog.get_profile()
                if updated_profile:
                    # Delete old profile if name changed
                    if profile.name != updated_profile.name:
                        self.profile_manager.delete_profile(profile.name)
                    
                    # Save updated profile
                    if self.profile_manager.save_profile(updated_profile):
                        wx.MessageBox(
                            f"Profile '{updated_profile.name}' updated successfully!",
                            "Success",
                            wx.OK | wx.ICON_INFORMATION
                        )
                        self.refresh()
                    else:
                        wx.MessageBox(
                            "Failed to save profile.",
                            "Error",
                            wx.OK | wx.ICON_ERROR
                        )
            dialog.Destroy()
    
    def on_apply_profile(self, event):
        """Handle apply profile button click."""
        index = self.profile_list.GetFirstSelected()
        if index == -1:
            return
        
        profile_name = self.profile_list.GetItemText(index, 0)
        profile = self.profile_manager.get_profile(profile_name)
        
        if profile:
            # Confirm action
            result = wx.MessageBox(
                f"Apply profile '{profile.name}'?\n\n"
                f"This will modify network configuration files.\n"
                f"A backup will be created automatically.",
                "Confirm Profile Application",
                wx.YES_NO | wx.ICON_QUESTION
            )
            
            if result == wx.YES:
                try:
                    if self.profile_manager.apply_profile(profile, backup=True):
                        wx.MessageBox(
                            f"Profile '{profile.name}' applied successfully!\n\n"
                            f"You may need to restart network services or reboot.",
                            "Success",
                            wx.OK | wx.ICON_INFORMATION
                        )
                    else:
                        wx.MessageBox(
                            "Failed to apply profile. Check logs for details.",
                            "Error",
                            wx.OK | wx.ICON_ERROR
                        )
                except Exception as e:
                    wx.MessageBox(
                        f"Error applying profile:\n{str(e)}",
                        "Error",
                        wx.OK | wx.ICON_ERROR
                    )
    
    def on_delete_profile(self, event):
        """Handle delete profile button click."""
        index = self.profile_list.GetFirstSelected()
        if index == -1:
            return
        
        profile_name = self.profile_list.GetItemText(index, 0)
        
        # Confirm deletion
        result = wx.MessageBox(
            f"Delete profile '{profile_name}'?\n\nThis action cannot be undone.",
            "Confirm Deletion",
            wx.YES_NO | wx.ICON_WARNING
        )
        
        if result == wx.YES:
            if self.profile_manager.delete_profile(profile_name):
                wx.MessageBox(
                    f"Profile '{profile_name}' deleted successfully!",
                    "Success",
                    wx.OK | wx.ICON_INFORMATION
                )
                self.refresh()
            else:
                wx.MessageBox(
                    "Failed to delete profile.",
                    "Error",
                    wx.OK | wx.ICON_ERROR
                )
    
    def on_import_profile(self, event):
        """Handle import profile button click."""
        wildcard = "JSON files (*.json)|*.json|All files (*.*)|*.*"
        dialog = wx.FileDialog(
            self,
            "Import Profile",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        )
        
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            profile = self.profile_manager.import_profile(path)
            if profile:
                # Save imported profile
                if self.profile_manager.save_profile(profile):
                    wx.MessageBox(
                        f"Profile '{profile.name}' imported successfully!",
                        "Success",
                        wx.OK | wx.ICON_INFORMATION
                    )
                    self.refresh()
                else:
                    wx.MessageBox(
                        "Failed to save imported profile.",
                        "Error",
                        wx.OK | wx.ICON_ERROR
                    )
            else:
                wx.MessageBox(
                    "Failed to import profile. Invalid file format.",
                    "Error",
                    wx.OK | wx.ICON_ERROR
                )
        
        dialog.Destroy()
    
    def on_export_profile(self, event):
        """Handle export profile button click."""
        index = self.profile_list.GetFirstSelected()
        if index == -1:
            return
        
        profile_name = self.profile_list.GetItemText(index, 0)
        profile = self.profile_manager.get_profile(profile_name)
        
        if profile:
            wildcard = "JSON files (*.json)|*.json|All files (*.*)|*.*"
            dialog = wx.FileDialog(
                self,
                "Export Profile",
                defaultFile=f"{profile_name.replace(' ', '_')}.json",
                wildcard=wildcard,
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
            )
            
            if dialog.ShowModal() == wx.ID_OK:
                path = dialog.GetPath()
                if self.profile_manager.export_profile(profile, path):
                    wx.MessageBox(
                        f"Profile '{profile.name}' exported successfully!",
                        "Success",
                        wx.OK | wx.ICON_INFORMATION
                    )
                else:
                    wx.MessageBox(
                        "Failed to export profile.",
                        "Error",
                        wx.OK | wx.ICON_ERROR
                    )
            
            dialog.Destroy()


class ProfileWizardDialog(wx.Dialog):
    """Dialog for creating/editing network profiles."""
    
    def __init__(self, parent, profile_manager, profile=None):
        """
        Initialize the profile wizard dialog.
        
        Args:
            parent: Parent window
            profile_manager: ProfileManager instance
            profile: Existing profile to edit (None for new profile)
        """
        title = "Edit Profile" if profile else "New Profile"
        super().__init__(parent, title=title, size=(500, 600))
        
        self.profile_manager = profile_manager
        self.existing_profile = profile
        self.logger = logging.getLogger(__name__)
        
        self._create_ui()
        
        # Load existing profile data
        if profile:
            self._load_profile_data(profile)
    
    def _create_ui(self):
        """Create the user interface."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Profile name
        name_label = wx.StaticText(self, label="Profile Name:")
        main_sizer.Add(name_label, 0, wx.ALL, 5)
        
        self.name_text = wx.TextCtrl(self)
        main_sizer.Add(self.name_text, 0, wx.EXPAND | wx.ALL, 5)
        
        # Template selection (for new profiles only)
        if not self.existing_profile:
            template_label = wx.StaticText(self, label="Start from Template (optional):")
            main_sizer.Add(template_label, 0, wx.ALL, 5)
            
            templates = ["None"] + ProfileManager.get_available_templates()
            self.template_choice = wx.Choice(self, choices=templates)
            self.template_choice.SetSelection(0)
            self.template_choice.Bind(wx.EVT_CHOICE, self.on_template_selected)
            main_sizer.Add(self.template_choice, 0, wx.EXPAND | wx.ALL, 5)
        
        # Profile type
        type_label = wx.StaticText(self, label="Connection Type:")
        main_sizer.Add(type_label, 0, wx.ALL, 5)
        
        self.type_choice = wx.Choice(self, choices=["ethernet", "wifi", "tethering"])
        self.type_choice.SetSelection(0)
        self.type_choice.Bind(wx.EVT_CHOICE, self.on_type_changed)
        main_sizer.Add(self.type_choice, 0, wx.EXPAND | wx.ALL, 5)
        
        # Interface
        iface_label = wx.StaticText(self, label="Interface:")
        main_sizer.Add(iface_label, 0, wx.ALL, 5)
        
        self.interface_text = wx.TextCtrl(self, value="em0")
        main_sizer.Add(self.interface_text, 0, wx.EXPAND | wx.ALL, 5)
        
        # Auto-connect checkbox
        self.autoconnect_check = wx.CheckBox(self, label="Enable auto-connect on boot")
        self.autoconnect_check.SetValue(True)
        main_sizer.Add(self.autoconnect_check, 0, wx.ALL, 5)
        
        # Configuration panel (type-specific)
        config_box = wx.StaticBox(self, label="Configuration")
        self.config_sizer = wx.StaticBoxSizer(config_box, wx.VERTICAL)
        
        main_sizer.Add(self.config_sizer, 1, wx.EXPAND | wx.ALL, 5)
        
        # Create config panels
        self._create_ethernet_config()
        self._create_wifi_config()
        
        # Show appropriate panel
        self._show_config_panel("ethernet")
        
        # Dialog buttons
        button_sizer = wx.StdDialogButtonSizer()
        
        ok_button = wx.Button(self, wx.ID_OK, "Save")
        ok_button.Bind(wx.EVT_BUTTON, self.on_save)
        button_sizer.AddButton(ok_button)
        
        cancel_button = wx.Button(self, wx.ID_CANCEL, "Cancel")
        button_sizer.AddButton(cancel_button)
        
        button_sizer.Realize()
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        self.SetSizer(main_sizer)
    
    def _create_ethernet_config(self):
        """Create Ethernet configuration panel."""
        self.ethernet_panel = wx.Panel(self)
        ethernet_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # DHCP checkbox
        self.dhcp_check = wx.CheckBox(self.ethernet_panel, label="Use DHCP")
        self.dhcp_check.SetValue(True)
        self.dhcp_check.Bind(wx.EVT_CHECKBOX, self.on_dhcp_changed)
        ethernet_sizer.Add(self.dhcp_check, 0, wx.ALL, 5)
        
        # Static IP fields
        self.static_panel = wx.Panel(self.ethernet_panel)
        static_sizer = wx.FlexGridSizer(4, 2, 5, 5)
        static_sizer.AddGrowableCol(1)
        
        # IP Address
        static_sizer.Add(wx.StaticText(self.static_panel, label="IP Address:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.ip_text = wx.TextCtrl(self.static_panel)
        static_sizer.Add(self.ip_text, 0, wx.EXPAND)
        
        # Netmask
        static_sizer.Add(wx.StaticText(self.static_panel, label="Netmask:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.netmask_text = wx.TextCtrl(self.static_panel, value="255.255.255.0")
        static_sizer.Add(self.netmask_text, 0, wx.EXPAND)
        
        # Gateway
        static_sizer.Add(wx.StaticText(self.static_panel, label="Gateway:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.gateway_text = wx.TextCtrl(self.static_panel)
        static_sizer.Add(self.gateway_text, 0, wx.EXPAND)
        
        self.static_panel.SetSizer(static_sizer)
        ethernet_sizer.Add(self.static_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        self.ethernet_panel.SetSizer(ethernet_sizer)
        self.config_sizer.Add(self.ethernet_panel, 1, wx.EXPAND)
        
        self.on_dhcp_changed(None)
    
    def _create_wifi_config(self):
        """Create WiFi configuration panel."""
        self.wifi_panel = wx.Panel(self)
        wifi_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # SSID
        ssid_label = wx.StaticText(self.wifi_panel, label="Network Name (SSID):")
        wifi_sizer.Add(ssid_label, 0, wx.ALL, 5)
        self.ssid_text = wx.TextCtrl(self.wifi_panel)
        wifi_sizer.Add(self.ssid_text, 0, wx.EXPAND | wx.ALL, 5)
        
        # Security type
        security_label = wx.StaticText(self.wifi_panel, label="Security:")
        wifi_sizer.Add(security_label, 0, wx.ALL, 5)
        self.security_choice = wx.Choice(self.wifi_panel, choices=["NONE", "WPA2-PSK", "WPA3-SAE"])
        self.security_choice.SetSelection(1)
        self.security_choice.Bind(wx.EVT_CHOICE, self.on_security_changed)
        wifi_sizer.Add(self.security_choice, 0, wx.EXPAND | wx.ALL, 5)
        
        # Password
        password_label = wx.StaticText(self.wifi_panel, label="Password:")
        wifi_sizer.Add(password_label, 0, wx.ALL, 5)
        self.password_text = wx.TextCtrl(self.wifi_panel, style=wx.TE_PASSWORD)
        wifi_sizer.Add(self.password_text, 0, wx.EXPAND | wx.ALL, 5)
        
        # Hidden network checkbox
        self.hidden_check = wx.CheckBox(self.wifi_panel, label="Hidden network (scan SSID)")
        wifi_sizer.Add(self.hidden_check, 0, wx.ALL, 5)
        
        # DHCP checkbox
        self.wifi_dhcp_check = wx.CheckBox(self.wifi_panel, label="Use DHCP")
        self.wifi_dhcp_check.SetValue(True)
        wifi_sizer.Add(self.wifi_dhcp_check, 0, wx.ALL, 5)
        
        self.wifi_panel.SetSizer(wifi_sizer)
        self.config_sizer.Add(self.wifi_panel, 1, wx.EXPAND)
        self.wifi_panel.Hide()
        
        self.on_security_changed(None)
    
    def on_template_selected(self, event):
        """Handle template selection."""
        selection = self.template_choice.GetSelection()
        if selection == 0:  # "None"
            return
        
        template_name = self.template_choice.GetString(selection)
        profile = self.profile_manager.create_from_template(template_name)
        
        if profile:
            self._load_profile_data(profile)
    
    def on_type_changed(self, event):
        """Handle connection type change."""
        conn_type = self.type_choice.GetStringSelection()
        self._show_config_panel(conn_type)
    
    def _show_config_panel(self, conn_type):
        """Show the appropriate configuration panel."""
        if conn_type == "wifi":
            self.ethernet_panel.Hide()
            self.wifi_panel.Show()
        else:
            self.wifi_panel.Hide()
            self.ethernet_panel.Show()
        
        self.Layout()
    
    def on_dhcp_changed(self, event):
        """Handle DHCP checkbox change."""
        use_dhcp = self.dhcp_check.GetValue()
        self.static_panel.Enable(not use_dhcp)
    
    def on_security_changed(self, event):
        """Handle security type change."""
        security = self.security_choice.GetStringSelection()
        self.password_text.Enable(security != "NONE")
    
    def _load_profile_data(self, profile):
        """Load data from an existing profile."""
        self.name_text.SetValue(profile.name)
        self.type_choice.SetStringSelection(profile.type)
        self.interface_text.SetValue(profile.interface)
        self.autoconnect_check.SetValue(profile.autoconnect)
        
        # Load type-specific config
        if profile.type == "wifi":
            self._show_config_panel("wifi")
            self.ssid_text.SetValue(profile.config.get('ssid', ''))
            self.security_choice.SetStringSelection(profile.config.get('security', 'WPA2-PSK'))
            self.password_text.SetValue(profile.config.get('password', ''))
            self.hidden_check.SetValue(profile.config.get('scan_ssid', False))
            self.wifi_dhcp_check.SetValue(profile.config.get('dhcp', True))
        else:
            self._show_config_panel("ethernet")
            self.dhcp_check.SetValue(profile.config.get('dhcp', True))
            if not profile.config.get('dhcp', True):
                self.ip_text.SetValue(profile.config.get('ip', ''))
                self.netmask_text.SetValue(profile.config.get('netmask', '255.255.255.0'))
                self.gateway_text.SetValue(profile.config.get('gateway', ''))
    
    def on_save(self, event):
        """Handle save button click."""
        # Validate inputs
        name = self.name_text.GetValue().strip()
        if not name:
            wx.MessageBox("Please enter a profile name.", "Validation Error", wx.OK | wx.ICON_ERROR)
            return
        
        conn_type = self.type_choice.GetStringSelection()
        interface = self.interface_text.GetValue().strip()
        
        if not interface:
            wx.MessageBox("Please enter an interface name.", "Validation Error", wx.OK | wx.ICON_ERROR)
            return
        
        # Create profile
        profile = NetworkProfile()
        profile.name = name
        profile.type = conn_type
        profile.interface = interface
        profile.autoconnect = self.autoconnect_check.GetValue()
        
        # Get type-specific configuration
        if conn_type == "wifi":
            ssid = self.ssid_text.GetValue().strip()
            if not ssid:
                wx.MessageBox("Please enter a network SSID.", "Validation Error", wx.OK | wx.ICON_ERROR)
                return
            
            profile.config = {
                'ssid': ssid,
                'security': self.security_choice.GetStringSelection(),
                'password': self.password_text.GetValue(),
                'scan_ssid': self.hidden_check.GetValue(),
                'dhcp': self.wifi_dhcp_check.GetValue()
            }
        else:
            use_dhcp = self.dhcp_check.GetValue()
            profile.config = {'dhcp': use_dhcp}
            
            if not use_dhcp:
                from ..utils.system_utils import validate_ip_address, validate_netmask
                
                ip = self.ip_text.GetValue().strip()
                netmask = self.netmask_text.GetValue().strip()
                gateway = self.gateway_text.GetValue().strip()
                
                if not ip or not validate_ip_address(ip):
                    wx.MessageBox("Please enter a valid IP address.", "Validation Error", wx.OK | wx.ICON_ERROR)
                    return
                
                if not netmask or not validate_netmask(netmask):
                    wx.MessageBox("Please enter a valid netmask.", "Validation Error", wx.OK | wx.ICON_ERROR)
                    return
                
                profile.config['ip'] = ip
                profile.config['netmask'] = netmask
                
                if gateway:
                    if not validate_ip_address(gateway):
                        wx.MessageBox("Please enter a valid gateway IP.", "Validation Error", wx.OK | wx.ICON_ERROR)
                        return
                    profile.config['gateway'] = gateway
        
        self.profile = profile
        event.Skip()
    
    def get_profile(self):
        """Get the created/edited profile."""
        return getattr(self, 'profile', None)
