"""WiFi management panel for BSD Network Manager."""

import wx
import logging
import threading


class WiFiPanel(wx.Panel):
    """
    Panel for managing WiFi connections.
    
    Provides interface to scan for networks, connect, and disconnect.
    """
    
    def __init__(self, parent, network_manager):
        """
        Initialize the WiFi panel.
        
        Args:
            parent: Parent window
            network_manager: NetworkManager instance
        """
        super().__init__(parent)
        self.network_manager = network_manager
        self.logger = logging.getLogger(__name__)
        self.current_iface = None
        
        self._create_ui()
        self.refresh()
    
    def _create_ui(self):
        """Create the user interface."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Interface selection
        iface_sizer = wx.BoxSizer(wx.HORIZONTAL)
        iface_label = wx.StaticText(self, label="WiFi Interface:")
        iface_sizer.Add(iface_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        
        self.iface_choice = wx.Choice(self)
        self.iface_choice.Bind(wx.EVT_CHOICE, self.on_interface_changed)
        iface_sizer.Add(self.iface_choice, 1, wx.EXPAND | wx.ALL, 5)
        
        main_sizer.Add(iface_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Current connection status
        status_box = wx.StaticBox(self, label="Connection Status")
        status_sizer = wx.StaticBoxSizer(status_box, wx.VERTICAL)
        
        self.status_text = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 60)
        )
        status_sizer.Add(self.status_text, 1, wx.EXPAND | wx.ALL, 5)
        
        main_sizer.Add(status_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Available networks
        networks_label = wx.StaticText(self, label="Available Networks:")
        main_sizer.Add(networks_label, 0, wx.ALL, 5)
        
        self.network_list = wx.ListCtrl(
            self,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN
        )
        self.network_list.AppendColumn("SSID", width=200)
        self.network_list.AppendColumn("BSSID", width=150)
        self.network_list.AppendColumn("Signal", width=100)
        self.network_list.AppendColumn("Channel", width=80)
        self.network_list.AppendColumn("Security", width=100)
        
        main_sizer.Add(self.network_list, 1, wx.EXPAND | wx.ALL, 5)
        
        # Buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.scan_btn = wx.Button(self, label="Scan")
        self.scan_btn.Bind(wx.EVT_BUTTON, self.on_scan)
        button_sizer.Add(self.scan_btn, 0, wx.ALL, 5)
        
        self.connect_btn = wx.Button(self, label="Connect")
        self.connect_btn.Bind(wx.EVT_BUTTON, self.on_connect)
        button_sizer.Add(self.connect_btn, 0, wx.ALL, 5)
        
        self.disconnect_btn = wx.Button(self, label="Disconnect")
        self.disconnect_btn.Bind(wx.EVT_BUTTON, self.on_disconnect)
        button_sizer.Add(self.disconnect_btn, 0, wx.ALL, 5)
        
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER)
        
        self.SetSizer(main_sizer)
    
    def refresh(self):
        """Refresh WiFi interfaces and status."""
        self.logger.info("Refreshing WiFi interfaces")
        
        try:
            # Get WiFi interfaces
            wifi_ifaces = self.network_manager.get_wifi_interfaces()
            
            self.iface_choice.Clear()
            for iface in wifi_ifaces:
                self.iface_choice.Append(iface)
            
            if wifi_ifaces:
                self.iface_choice.SetSelection(0)
                self.current_iface = wifi_ifaces[0]
                self._update_connection_status()
            else:
                self.status_text.SetValue("No WiFi interfaces found.")
                self.current_iface = None
            
            self._update_button_states()
            
        except Exception as e:
            self.logger.error(f"Error refreshing WiFi interfaces: {e}")
            wx.MessageBox(
                f"Error loading WiFi interfaces:\n{str(e)}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )
    
    def on_interface_changed(self, event):
        """Handle interface selection change."""
        selection = self.iface_choice.GetSelection()
        if selection != wx.NOT_FOUND:
            self.current_iface = self.iface_choice.GetString(selection)
            self._update_connection_status()
            self._update_button_states()
    
    def _update_connection_status(self):
        """Update the connection status display."""
        if not self.current_iface:
            self.status_text.SetValue("No interface selected.")
            return
        
        try:
            connection = self.network_manager.get_current_connection(self.current_iface)
            
            if connection:
                status = f"Connected to: {connection.get('ssid', 'Unknown')}\n"
                status += f"Signal: {connection.get('signal', 'N/A')}"
                self.status_text.SetValue(status)
            else:
                self.status_text.SetValue("Not connected.")
        
        except Exception as e:
            self.logger.error(f"Error getting connection status: {e}")
            self.status_text.SetValue("Error getting status.")
    
    def _update_button_states(self):
        """Update button enabled states."""
        has_iface = self.current_iface is not None
        self.scan_btn.Enable(has_iface)
        self.connect_btn.Enable(has_iface)
        self.disconnect_btn.Enable(has_iface)
    
    def on_scan(self, event):
        """Handle scan button."""
        if not self.current_iface:
            wx.MessageBox(
                "No WiFi interface available.",
                "Error",
                wx.OK | wx.ICON_WARNING
            )
            return
        
        # Show progress dialog
        progress = wx.ProgressDialog(
            "Scanning",
            "Scanning for WiFi networks...",
            maximum=100,
            parent=self,
            style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE
        )
        
        # Perform scan in background thread
        def scan_thread():
            try:
                networks = self.network_manager.scan_networks(self.current_iface)
                wx.CallAfter(self._display_scan_results, networks, progress)
            except Exception as e:
                wx.CallAfter(self._handle_scan_error, e, progress)
        
        thread = threading.Thread(target=scan_thread)
        thread.daemon = True
        thread.start()
        
        progress.Pulse()
    
    def _display_scan_results(self, networks, progress):
        """Display scan results in the list."""
        progress.Destroy()
        
        self.network_list.DeleteAllItems()
        
        for network in networks:
            index = self.network_list.GetItemCount()
            self.network_list.InsertItem(index, network.get('ssid', ''))
            self.network_list.SetItem(index, 1, network.get('bssid', ''))
            self.network_list.SetItem(index, 2, network.get('signal', ''))
            self.network_list.SetItem(index, 3, network.get('channel', ''))
            self.network_list.SetItem(index, 4, network.get('security', ''))
        
        self.logger.info(f"Scan complete: found {len(networks)} networks")
    
    def _handle_scan_error(self, error, progress):
        """Handle scan error."""
        progress.Destroy()
        self.logger.error(f"Scan error: {error}")
        wx.MessageBox(
            f"Error scanning for networks:\n{str(error)}",
            "Scan Error",
            wx.OK | wx.ICON_ERROR
        )
    
    def on_connect(self, event):
        """Handle connect button."""
        if not self.current_iface:
            wx.MessageBox(
                "No WiFi interface available.",
                "Error",
                wx.OK | wx.ICON_WARNING
            )
            return
        
        # Get selected network
        index = self.network_list.GetFirstSelected()
        if index == -1:
            wx.MessageBox(
                "Please select a network to connect to.",
                "No Selection",
                wx.OK | wx.ICON_WARNING
            )
            return
        
        ssid = self.network_list.GetItemText(index, 0)
        security = self.network_list.GetItemText(index, 4)
        
        # Show connection dialog
        dialog = ConnectDialog(self, ssid, security, self.current_iface, self.network_manager)
        if dialog.ShowModal() == wx.ID_OK:
            self._update_connection_status()
        dialog.Destroy()
    
    def on_disconnect(self, event):
        """Handle disconnect button."""
        if not self.current_iface:
            wx.MessageBox(
                "No WiFi interface available.",
                "Error",
                wx.OK | wx.ICON_WARNING
            )
            return
        
        try:
            if self.network_manager.disconnect_network(self.current_iface):
                wx.MessageBox(
                    "Disconnected successfully.",
                    "Success",
                    wx.OK | wx.ICON_INFORMATION
                )
                self._update_connection_status()
            else:
                wx.MessageBox(
                    "Failed to disconnect.",
                    "Error",
                    wx.OK | wx.ICON_ERROR
                )
        
        except Exception as e:
            self.logger.error(f"Error disconnecting: {e}")
            wx.MessageBox(
                f"Error disconnecting:\n{str(e)}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )


class ConnectDialog(wx.Dialog):
    """Dialog for connecting to a WiFi network."""
    
    def __init__(self, parent, ssid, security, iface, network_manager):
        """
        Initialize the connect dialog.
        
        Args:
            parent: Parent window
            ssid: Network SSID
            security: Security type
            iface: Interface name
            network_manager: NetworkManager instance
        """
        super().__init__(
            parent,
            title=f"Connect to {ssid}",
            size=(400, 250)
        )
        
        self.ssid = ssid
        self.security = security
        self.iface = iface
        self.network_manager = network_manager
        self.logger = logging.getLogger(__name__)
        
        self._create_ui()
        self.Centre()
    
    def _create_ui(self):
        """Create the dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Network info
        info_text = f"Network: {self.ssid}\nSecurity: {self.security}"
        info_label = wx.StaticText(panel, label=info_text)
        main_sizer.Add(info_label, 0, wx.ALL, 10)
        
        # SSID (editable for hidden networks)
        ssid_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ssid_label = wx.StaticText(panel, label="SSID:", size=(100, -1))
        ssid_sizer.Add(ssid_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        self.ssid_text = wx.TextCtrl(panel, value=self.ssid)
        ssid_sizer.Add(self.ssid_text, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(ssid_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Password
        if self.security != 'Open':
            pwd_sizer = wx.BoxSizer(wx.HORIZONTAL)
            pwd_label = wx.StaticText(panel, label="Password:", size=(100, -1))
            pwd_sizer.Add(pwd_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
            self.password_text = wx.TextCtrl(panel, style=wx.TE_PASSWORD)
            pwd_sizer.Add(self.password_text, 1, wx.EXPAND | wx.ALL, 5)
            main_sizer.Add(pwd_sizer, 0, wx.EXPAND | wx.ALL, 5)
        else:
            self.password_text = None
        
        # Security type
        security_sizer = wx.BoxSizer(wx.HORIZONTAL)
        security_label = wx.StaticText(panel, label="Security:", size=(100, -1))
        security_sizer.Add(security_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        self.security_choice = wx.Choice(panel, choices=['Open', 'WEP', 'WPA', 'WPA2'])
        
        # Select current security type
        if self.security in ['Open', 'WEP', 'WPA', 'WPA2']:
            self.security_choice.SetStringSelection(self.security)
        else:
            self.security_choice.SetStringSelection('WPA2')
        
        security_sizer.Add(self.security_choice, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(security_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        connect_btn = wx.Button(panel, wx.ID_OK, "Connect")
        connect_btn.Bind(wx.EVT_BUTTON, self.on_connect)
        button_sizer.Add(connect_btn, 0, wx.ALL, 5)
        
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        button_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        panel.SetSizer(main_sizer)
    
    def on_connect(self, event):
        """Handle connect button."""
        ssid = self.ssid_text.GetValue().strip()
        security = self.security_choice.GetStringSelection()
        
        if not ssid:
            wx.MessageBox("SSID is required.", "Validation Error", wx.OK | wx.ICON_WARNING)
            return
        
        password = None
        if self.password_text and security != 'Open':
            password = self.password_text.GetValue()
            if not password:
                wx.MessageBox("Password is required for secured networks.", "Validation Error", wx.OK | wx.ICON_WARNING)
                return
        
        # Show progress dialog
        progress = wx.ProgressDialog(
            "Connecting",
            f"Connecting to {ssid}...",
            maximum=100,
            parent=self,
            style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE
        )
        
        # Connect in background thread
        def connect_thread():
            try:
                success = self.network_manager.connect_network(self.iface, ssid, password, security)
                wx.CallAfter(self._handle_connect_result, success, progress)
            except Exception as e:
                wx.CallAfter(self._handle_connect_error, e, progress)
        
        thread = threading.Thread(target=connect_thread)
        thread.daemon = True
        thread.start()
        
        progress.Pulse()
    
    def _handle_connect_result(self, success, progress):
        """Handle connection result."""
        progress.Destroy()
        
        if success:
            wx.MessageBox(
                f"Connected to {self.ssid} successfully.",
                "Success",
                wx.OK | wx.ICON_INFORMATION
            )
            self.EndModal(wx.ID_OK)
        else:
            wx.MessageBox(
                f"Failed to connect to {self.ssid}.",
                "Connection Error",
                wx.OK | wx.ICON_ERROR
            )
    
    def _handle_connect_error(self, error, progress):
        """Handle connection error."""
        progress.Destroy()
        self.logger.error(f"Connection error: {error}")
        wx.MessageBox(
            f"Error connecting to network:\n{str(error)}",
            "Error",
            wx.OK | wx.ICON_ERROR
        )
