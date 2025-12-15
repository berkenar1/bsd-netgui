"""DNS configuration panel for BSD Network Manager."""

import wx
import logging
from ..utils.system_utils import validate_ip_address


class DNSPanel(wx.Panel):
    """
    Panel for managing DNS configuration.
    
    Provides interface to add, remove, and modify DNS servers.
    """
    
    def __init__(self, parent, network_manager):
        """
        Initialize the DNS panel.
        
        Args:
            parent: Parent window
            network_manager: NetworkManager instance
        """
        super().__init__(parent)
        self.network_manager = network_manager
        self.logger = logging.getLogger(__name__)
        
        self._create_ui()
        self.refresh()
    
    def _create_ui(self):
        """Create the user interface."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Instructions
        info_text = "Configure DNS servers for your system. Changes will be written to /etc/resolv.conf"
        info_label = wx.StaticText(self, label=info_text)
        main_sizer.Add(info_label, 0, wx.ALL, 10)
        
        # DNS servers list
        list_label = wx.StaticText(self, label="Current DNS Servers:")
        main_sizer.Add(list_label, 0, wx.ALL, 5)
        
        self.dns_listbox = wx.ListBox(self, style=wx.LB_SINGLE)
        main_sizer.Add(self.dns_listbox, 1, wx.EXPAND | wx.ALL, 5)
        
        # Add DNS server section
        add_box = wx.StaticBox(self, label="Add DNS Server")
        add_sizer = wx.StaticBoxSizer(add_box, wx.HORIZONTAL)
        
        self.dns_input = wx.TextCtrl(self)
        self.dns_input.SetHint("Enter DNS server IP (e.g., 8.8.8.8)")
        add_sizer.Add(self.dns_input, 1, wx.EXPAND | wx.ALL, 5)
        
        add_btn = wx.Button(self, label="Add")
        add_btn.Bind(wx.EVT_BUTTON, self.on_add)
        add_sizer.Add(add_btn, 0, wx.ALL, 5)
        
        main_sizer.Add(add_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Action buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        refresh_btn = wx.Button(self, label="Refresh")
        refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh)
        button_sizer.Add(refresh_btn, 0, wx.ALL, 5)
        
        remove_btn = wx.Button(self, label="Remove Selected")
        remove_btn.Bind(wx.EVT_BUTTON, self.on_remove)
        button_sizer.Add(remove_btn, 0, wx.ALL, 5)
        
        apply_btn = wx.Button(self, label="Apply Changes")
        apply_btn.Bind(wx.EVT_BUTTON, self.on_apply)
        button_sizer.Add(apply_btn, 0, wx.ALL, 5)
        
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        # Common DNS servers reference
        reference_text = (
            "Common DNS Servers:\n"
            "Google: 8.8.8.8, 8.8.4.4\n"
            "Cloudflare: 1.1.1.1, 1.0.0.1\n"
            "Quad9: 9.9.9.9, 149.112.112.112"
        )
        reference_label = wx.StaticText(self, label=reference_text)
        font = reference_label.GetFont()
        font.SetPointSize(font.GetPointSize() - 1)
        reference_label.SetFont(font)
        main_sizer.Add(reference_label, 0, wx.ALL, 10)
        
        self.SetSizer(main_sizer)
    
    def refresh(self):
        """Refresh the DNS servers list."""
        self.logger.info("Refreshing DNS servers")
        self.dns_listbox.Clear()
        
        try:
            dns_servers = self.network_manager.get_dns_servers()
            
            for server in dns_servers:
                self.dns_listbox.Append(server)
            
            self.logger.info(f"Loaded {len(dns_servers)} DNS servers")
            
        except Exception as e:
            self.logger.error(f"Error refreshing DNS servers: {e}")
            wx.MessageBox(
                f"Error loading DNS servers:\n{str(e)}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )
    
    def on_refresh(self, event):
        """Handle refresh button."""
        self.refresh()
    
    def on_add(self, event):
        """Handle add button."""
        dns_server = self.dns_input.GetValue().strip()
        
        if not dns_server:
            wx.MessageBox(
                "Please enter a DNS server IP address.",
                "Validation Error",
                wx.OK | wx.ICON_WARNING
            )
            return
        
        # Validate IP address
        if not validate_ip_address(dns_server):
            wx.MessageBox(
                "Invalid IP address format.\nPlease enter a valid IPv4 address (e.g., 8.8.8.8)",
                "Validation Error",
                wx.OK | wx.ICON_WARNING
            )
            return
        
        # Check if already exists
        if self.dns_listbox.FindString(dns_server) != wx.NOT_FOUND:
            wx.MessageBox(
                f"DNS server {dns_server} already exists in the list.",
                "Duplicate Entry",
                wx.OK | wx.ICON_INFORMATION
            )
            return
        
        # Add to list
        self.dns_listbox.Append(dns_server)
        self.dns_input.Clear()
        
        self.logger.info(f"Added DNS server {dns_server} to list (not yet applied)")
    
    def on_remove(self, event):
        """Handle remove button."""
        selection = self.dns_listbox.GetSelection()
        
        if selection == wx.NOT_FOUND:
            wx.MessageBox(
                "Please select a DNS server to remove.",
                "No Selection",
                wx.OK | wx.ICON_WARNING
            )
            return
        
        dns_server = self.dns_listbox.GetString(selection)
        
        # Confirm removal
        result = wx.MessageBox(
            f"Remove DNS server {dns_server}?",
            "Confirm Removal",
            wx.YES_NO | wx.ICON_QUESTION
        )
        
        if result == wx.YES:
            self.dns_listbox.Delete(selection)
            self.logger.info(f"Removed DNS server {dns_server} from list (not yet applied)")
    
    def on_apply(self, event):
        """Handle apply changes button."""
        # Get all DNS servers from the listbox
        dns_servers = []
        for i in range(self.dns_listbox.GetCount()):
            dns_servers.append(self.dns_listbox.GetString(i))
        
        if not dns_servers:
            result = wx.MessageBox(
                "No DNS servers configured. This will clear all DNS settings.\n\n"
                "Are you sure you want to continue?",
                "Confirm",
                wx.YES_NO | wx.ICON_WARNING
            )
            if result != wx.YES:
                return
        else:
            # Confirm before applying
            servers_text = "\n".join(dns_servers)
            result = wx.MessageBox(
                f"Apply the following DNS servers?\n\n{servers_text}\n\n"
                "This will modify /etc/resolv.conf",
                "Confirm Changes",
                wx.YES_NO | wx.ICON_QUESTION
            )
            
            if result != wx.YES:
                return
        
        try:
            if self.network_manager.set_dns_servers(dns_servers):
                wx.MessageBox(
                    "DNS configuration applied successfully.",
                    "Success",
                    wx.OK | wx.ICON_INFORMATION
                )
                self.refresh()
            else:
                wx.MessageBox(
                    "Failed to apply DNS configuration.\n"
                    "Check the log for details.",
                    "Error",
                    wx.OK | wx.ICON_ERROR
                )
        
        except Exception as e:
            self.logger.error(f"Error applying DNS configuration: {e}")
            wx.MessageBox(
                f"Error applying DNS configuration:\n{str(e)}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )
