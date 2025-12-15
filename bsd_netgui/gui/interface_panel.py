"""Interface management panel for BSD Network Manager."""

import wx
import logging
from ..utils.system_utils import validate_ip_address, validate_netmask


class InterfacePanel(wx.Panel):
    """
    Panel for managing network interfaces.
    
    Provides interface to view, enable/disable, and configure network interfaces.
    """
    
    def __init__(self, parent, network_manager):
        """
        Initialize the interface panel.
        
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
        
        # Interface list
        list_label = wx.StaticText(self, label="Network Interfaces:")
        main_sizer.Add(list_label, 0, wx.ALL, 5)
        
        self.interface_list = wx.ListCtrl(
            self,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN
        )
        self.interface_list.AppendColumn("Interface", width=120)
        self.interface_list.AppendColumn("Status", width=80)
        self.interface_list.AppendColumn("IP Address", width=150)
        self.interface_list.AppendColumn("MAC Address", width=150)
        self.interface_list.AppendColumn("MTU", width=80)
        
        self.interface_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_interface_selected)
        main_sizer.Add(self.interface_list, 1, wx.EXPAND | wx.ALL, 5)
        
        # Details section
        details_label = wx.StaticText(self, label="Interface Details:")
        main_sizer.Add(details_label, 0, wx.ALL, 5)
        
        self.details_text = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 100)
        )
        main_sizer.Add(self.details_text, 0, wx.EXPAND | wx.ALL, 5)
        
        # Buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.refresh_btn = wx.Button(self, label="Refresh")
        self.refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh)
        button_sizer.Add(self.refresh_btn, 0, wx.ALL, 5)
        
        self.enable_btn = wx.Button(self, label="Enable")
        self.enable_btn.Bind(wx.EVT_BUTTON, self.on_enable)
        self.enable_btn.Enable(False)
        button_sizer.Add(self.enable_btn, 0, wx.ALL, 5)
        
        self.disable_btn = wx.Button(self, label="Disable")
        self.disable_btn.Bind(wx.EVT_BUTTON, self.on_disable)
        self.disable_btn.Enable(False)
        button_sizer.Add(self.disable_btn, 0, wx.ALL, 5)
        
        self.config_btn = wx.Button(self, label="Configure IP")
        self.config_btn.Bind(wx.EVT_BUTTON, self.on_configure_ip)
        self.config_btn.Enable(False)
        button_sizer.Add(self.config_btn, 0, wx.ALL, 5)
        
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER)
        
        self.SetSizer(main_sizer)
    
    def refresh(self):
        """Refresh the interface list."""
        self.logger.info("Refreshing interface list")
        self.interface_list.DeleteAllItems()
        
        try:
            interfaces = self.network_manager.list_interfaces()
            
            for iface in interfaces:
                index = self.interface_list.GetItemCount()
                self.interface_list.InsertItem(index, iface['name'])
                self.interface_list.SetItem(index, 1, iface['status'])
                self.interface_list.SetItem(index, 2, iface.get('ipv4', ''))
                self.interface_list.SetItem(index, 3, iface.get('mac', ''))
                self.interface_list.SetItem(index, 4, iface.get('mtu', ''))
            
            self.logger.info(f"Loaded {len(interfaces)} interfaces")
            
        except Exception as e:
            self.logger.error(f"Error refreshing interfaces: {e}")
            wx.MessageBox(
                f"Error loading interfaces:\n{str(e)}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )
    
    def on_interface_selected(self, event):
        """Handle interface selection."""
        index = event.GetIndex()
        iface_name = self.interface_list.GetItemText(index, 0)
        
        try:
            iface_details = self.network_manager.get_interface_details(iface_name)
            
            if iface_details:
                details_text = f"Interface: {iface_details['name']}\n"
                details_text += f"Status: {iface_details['status']}\n"
                details_text += f"IP Address: {iface_details.get('ipv4', 'N/A')}\n"
                details_text += f"Netmask: {iface_details.get('netmask', 'N/A')}\n"
                details_text += f"MAC Address: {iface_details.get('mac', 'N/A')}\n"
                details_text += f"MTU: {iface_details.get('mtu', 'N/A')}\n"
                
                self.details_text.SetValue(details_text)
                
                # Enable buttons
                self.enable_btn.Enable(True)
                self.disable_btn.Enable(True)
                self.config_btn.Enable(True)
        
        except Exception as e:
            self.logger.error(f"Error getting interface details: {e}")
            wx.MessageBox(
                f"Error getting interface details:\n{str(e)}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )
    
    def on_refresh(self, event):
        """Handle refresh button."""
        self.refresh()
    
    def on_enable(self, event):
        """Handle enable button."""
        iface_name = self._get_selected_interface()
        if not iface_name:
            return
        
        try:
            if self.network_manager.enable_interface(iface_name):
                wx.MessageBox(
                    f"Interface {iface_name} enabled successfully.",
                    "Success",
                    wx.OK | wx.ICON_INFORMATION
                )
                self.refresh()
            else:
                wx.MessageBox(
                    f"Failed to enable interface {iface_name}.",
                    "Error",
                    wx.OK | wx.ICON_ERROR
                )
        except Exception as e:
            self.logger.error(f"Error enabling interface: {e}")
            wx.MessageBox(
                f"Error enabling interface:\n{str(e)}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )
    
    def on_disable(self, event):
        """Handle disable button."""
        iface_name = self._get_selected_interface()
        if not iface_name:
            return
        
        try:
            if self.network_manager.disable_interface(iface_name):
                wx.MessageBox(
                    f"Interface {iface_name} disabled successfully.",
                    "Success",
                    wx.OK | wx.ICON_INFORMATION
                )
                self.refresh()
            else:
                wx.MessageBox(
                    f"Failed to disable interface {iface_name}.",
                    "Error",
                    wx.OK | wx.ICON_ERROR
                )
        except Exception as e:
            self.logger.error(f"Error disabling interface: {e}")
            wx.MessageBox(
                f"Error disabling interface:\n{str(e)}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )
    
    def on_configure_ip(self, event):
        """Handle configure IP button."""
        iface_name = self._get_selected_interface()
        if not iface_name:
            return
        
        dialog = ConfigureIPDialog(self, iface_name, self.network_manager)
        if dialog.ShowModal() == wx.ID_OK:
            self.refresh()
        dialog.Destroy()
    
    def _get_selected_interface(self):
        """Get the currently selected interface name."""
        index = self.interface_list.GetFirstSelected()
        if index == -1:
            wx.MessageBox(
                "Please select an interface first.",
                "No Selection",
                wx.OK | wx.ICON_WARNING
            )
            return None
        return self.interface_list.GetItemText(index, 0)


class ConfigureIPDialog(wx.Dialog):
    """Dialog for configuring IP address on an interface."""
    
    def __init__(self, parent, iface_name, network_manager):
        """
        Initialize the configure IP dialog.
        
        Args:
            parent: Parent window
            iface_name: Interface name to configure
            network_manager: NetworkManager instance
        """
        super().__init__(
            parent,
            title=f"Configure IP - {iface_name}",
            size=(400, 300)
        )
        
        self.iface_name = iface_name
        self.network_manager = network_manager
        self.logger = logging.getLogger(__name__)
        
        self._create_ui()
        self.Centre()
    
    def _create_ui(self):
        """Create the dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Configuration type
        config_box = wx.StaticBox(panel, label="IP Configuration")
        config_sizer = wx.StaticBoxSizer(config_box, wx.VERTICAL)
        
        self.dhcp_radio = wx.RadioButton(panel, label="DHCP (Automatic)", style=wx.RB_GROUP)
        self.dhcp_radio.Bind(wx.EVT_RADIOBUTTON, self.on_config_type_changed)
        config_sizer.Add(self.dhcp_radio, 0, wx.ALL, 5)
        
        self.static_radio = wx.RadioButton(panel, label="Static IP")
        self.static_radio.Bind(wx.EVT_RADIOBUTTON, self.on_config_type_changed)
        config_sizer.Add(self.static_radio, 0, wx.ALL, 5)
        
        main_sizer.Add(config_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Static IP configuration
        static_box = wx.StaticBox(panel, label="Static IP Settings")
        static_sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)
        
        # IP Address
        ip_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ip_label = wx.StaticText(panel, label="IP Address:", size=(100, -1))
        ip_sizer.Add(ip_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        self.ip_text = wx.TextCtrl(panel)
        ip_sizer.Add(self.ip_text, 1, wx.EXPAND | wx.ALL, 5)
        static_sizer.Add(ip_sizer, 0, wx.EXPAND)
        
        # Netmask
        netmask_sizer = wx.BoxSizer(wx.HORIZONTAL)
        netmask_label = wx.StaticText(panel, label="Netmask:", size=(100, -1))
        netmask_sizer.Add(netmask_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        self.netmask_text = wx.TextCtrl(panel, value="255.255.255.0")
        netmask_sizer.Add(self.netmask_text, 1, wx.EXPAND | wx.ALL, 5)
        static_sizer.Add(netmask_sizer, 0, wx.EXPAND)
        
        # Gateway
        gateway_sizer = wx.BoxSizer(wx.HORIZONTAL)
        gateway_label = wx.StaticText(panel, label="Gateway:", size=(100, -1))
        gateway_sizer.Add(gateway_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        self.gateway_text = wx.TextCtrl(panel)
        gateway_sizer.Add(self.gateway_text, 1, wx.EXPAND | wx.ALL, 5)
        static_sizer.Add(gateway_sizer, 0, wx.EXPAND)
        
        main_sizer.Add(static_sizer, 1, wx.EXPAND | wx.ALL, 10)
        
        # Buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(panel, wx.ID_OK, "Apply")
        ok_btn.Bind(wx.EVT_BUTTON, self.on_apply)
        button_sizer.Add(ok_btn, 0, wx.ALL, 5)
        
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        button_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        panel.SetSizer(main_sizer)
        
        # Initialize state
        self.dhcp_radio.SetValue(True)
        self.on_config_type_changed(None)
    
    def on_config_type_changed(self, event):
        """Handle configuration type change."""
        use_static = self.static_radio.GetValue()
        self.ip_text.Enable(use_static)
        self.netmask_text.Enable(use_static)
        self.gateway_text.Enable(use_static)
    
    def on_apply(self, event):
        """Handle apply button."""
        try:
            if self.dhcp_radio.GetValue():
                # Configure DHCP
                if self.network_manager.configure_dhcp(self.iface_name):
                    wx.MessageBox(
                        "DHCP configuration applied successfully.",
                        "Success",
                        wx.OK | wx.ICON_INFORMATION
                    )
                    self.EndModal(wx.ID_OK)
                else:
                    wx.MessageBox(
                        "Failed to configure DHCP.",
                        "Error",
                        wx.OK | wx.ICON_ERROR
                    )
            else:
                # Configure static IP
                ip = self.ip_text.GetValue().strip()
                netmask = self.netmask_text.GetValue().strip()
                gateway = self.gateway_text.GetValue().strip()
                
                # Validate inputs
                if not ip:
                    wx.MessageBox("IP address is required.", "Validation Error", wx.OK | wx.ICON_WARNING)
                    return
                
                if not validate_ip_address(ip):
                    wx.MessageBox("Invalid IP address format.", "Validation Error", wx.OK | wx.ICON_WARNING)
                    return
                
                if not netmask:
                    wx.MessageBox("Netmask is required.", "Validation Error", wx.OK | wx.ICON_WARNING)
                    return
                
                if not validate_netmask(netmask):
                    wx.MessageBox("Invalid netmask format.", "Validation Error", wx.OK | wx.ICON_WARNING)
                    return
                
                if gateway and not validate_ip_address(gateway):
                    wx.MessageBox("Invalid gateway address format.", "Validation Error", wx.OK | wx.ICON_WARNING)
                    return
                
                # Apply static IP
                if self.network_manager.configure_static_ip(self.iface_name, ip, netmask, gateway or None):
                    wx.MessageBox(
                        "Static IP configuration applied successfully.",
                        "Success",
                        wx.OK | wx.ICON_INFORMATION
                    )
                    self.EndModal(wx.ID_OK)
                else:
                    wx.MessageBox(
                        "Failed to configure static IP.",
                        "Error",
                        wx.OK | wx.ICON_ERROR
                    )
        
        except Exception as e:
            self.logger.error(f"Error applying IP configuration: {e}")
            wx.MessageBox(
                f"Error applying configuration:\n{str(e)}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )
