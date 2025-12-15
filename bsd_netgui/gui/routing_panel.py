"""Routing table panel for BSD Network Manager."""

import wx
import logging
from ..utils.system_utils import validate_ip_address, validate_netmask


class RoutingPanel(wx.Panel):
    """
    Panel for managing routing tables.
    
    Provides interface to view, add, and delete routes.
    """
    
    def __init__(self, parent, network_manager):
        """
        Initialize the routing panel.
        
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
        info_text = "View and manage the system routing table."
        info_label = wx.StaticText(self, label=info_text)
        main_sizer.Add(info_label, 0, wx.ALL, 10)
        
        # Routing table
        list_label = wx.StaticText(self, label="Routing Table:")
        main_sizer.Add(list_label, 0, wx.ALL, 5)
        
        self.route_list = wx.ListCtrl(
            self,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN
        )
        self.route_list.AppendColumn("Destination", width=150)
        self.route_list.AppendColumn("Gateway", width=150)
        self.route_list.AppendColumn("Flags", width=100)
        self.route_list.AppendColumn("Interface", width=100)
        self.route_list.AppendColumn("Metric", width=80)
        
        main_sizer.Add(self.route_list, 1, wx.EXPAND | wx.ALL, 5)
        
        # Buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        refresh_btn = wx.Button(self, label="Refresh")
        refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh)
        button_sizer.Add(refresh_btn, 0, wx.ALL, 5)
        
        add_route_btn = wx.Button(self, label="Add Route")
        add_route_btn.Bind(wx.EVT_BUTTON, self.on_add_route)
        button_sizer.Add(add_route_btn, 0, wx.ALL, 5)
        
        delete_route_btn = wx.Button(self, label="Delete Route")
        delete_route_btn.Bind(wx.EVT_BUTTON, self.on_delete_route)
        button_sizer.Add(delete_route_btn, 0, wx.ALL, 5)
        
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        self.SetSizer(main_sizer)
    
    def refresh(self):
        """Refresh the routing table."""
        self.logger.info("Refreshing routing table")
        self.route_list.DeleteAllItems()
        
        try:
            routes = self.network_manager.get_routing_table()
            
            for route in routes:
                index = self.route_list.GetItemCount()
                self.route_list.InsertItem(index, route.get('destination', ''))
                self.route_list.SetItem(index, 1, route.get('gateway', ''))
                self.route_list.SetItem(index, 2, route.get('flags', ''))
                self.route_list.SetItem(index, 3, route.get('interface', ''))
                self.route_list.SetItem(index, 4, route.get('metric', ''))
            
            self.logger.info(f"Loaded {len(routes)} routes")
            
        except Exception as e:
            self.logger.error(f"Error refreshing routing table: {e}")
            wx.MessageBox(
                f"Error loading routing table:\n{str(e)}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )
    
    def on_refresh(self, event):
        """Handle refresh button."""
        self.refresh()
    
    def on_add_route(self, event):
        """Handle add route button."""
        dialog = AddRouteDialog(self, self.network_manager)
        if dialog.ShowModal() == wx.ID_OK:
            self.refresh()
        dialog.Destroy()
    
    def on_delete_route(self, event):
        """Handle delete route button."""
        index = self.route_list.GetFirstSelected()
        
        if index == -1:
            wx.MessageBox(
                "Please select a route to delete.",
                "No Selection",
                wx.OK | wx.ICON_WARNING
            )
            return
        
        destination = self.route_list.GetItemText(index, 0)
        
        # Confirm deletion
        result = wx.MessageBox(
            f"Delete route to {destination}?",
            "Confirm Deletion",
            wx.YES_NO | wx.ICON_QUESTION
        )
        
        if result == wx.YES:
            try:
                if self.network_manager.delete_route(destination):
                    wx.MessageBox(
                        f"Route to {destination} deleted successfully.",
                        "Success",
                        wx.OK | wx.ICON_INFORMATION
                    )
                    self.refresh()
                else:
                    wx.MessageBox(
                        f"Failed to delete route to {destination}.",
                        "Error",
                        wx.OK | wx.ICON_ERROR
                    )
            
            except Exception as e:
                self.logger.error(f"Error deleting route: {e}")
                wx.MessageBox(
                    f"Error deleting route:\n{str(e)}",
                    "Error",
                    wx.OK | wx.ICON_ERROR
                )


class AddRouteDialog(wx.Dialog):
    """Dialog for adding a new route."""
    
    def __init__(self, parent, network_manager):
        """
        Initialize the add route dialog.
        
        Args:
            parent: Parent window
            network_manager: NetworkManager instance
        """
        super().__init__(
            parent,
            title="Add Route",
            size=(400, 280)
        )
        
        self.network_manager = network_manager
        self.logger = logging.getLogger(__name__)
        
        self._create_ui()
        self.Centre()
    
    def _create_ui(self):
        """Create the dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Instructions
        info_text = "Enter route information:"
        info_label = wx.StaticText(panel, label=info_text)
        main_sizer.Add(info_label, 0, wx.ALL, 10)
        
        # Destination
        dest_sizer = wx.BoxSizer(wx.HORIZONTAL)
        dest_label = wx.StaticText(panel, label="Destination:", size=(100, -1))
        dest_sizer.Add(dest_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        self.dest_text = wx.TextCtrl(panel)
        self.dest_text.SetHint("e.g., 192.168.1.0 or default")
        dest_sizer.Add(self.dest_text, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(dest_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Gateway
        gateway_sizer = wx.BoxSizer(wx.HORIZONTAL)
        gateway_label = wx.StaticText(panel, label="Gateway:", size=(100, -1))
        gateway_sizer.Add(gateway_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        self.gateway_text = wx.TextCtrl(panel)
        self.gateway_text.SetHint("e.g., 192.168.1.1")
        gateway_sizer.Add(self.gateway_text, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(gateway_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Netmask
        netmask_sizer = wx.BoxSizer(wx.HORIZONTAL)
        netmask_label = wx.StaticText(panel, label="Netmask:", size=(100, -1))
        netmask_sizer.Add(netmask_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        self.netmask_text = wx.TextCtrl(panel)
        self.netmask_text.SetHint("e.g., 255.255.255.0 or 24 (optional)")
        netmask_sizer.Add(self.netmask_text, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(netmask_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Help text
        help_text = (
            "• For default gateway, use 'default' as destination\n"
            "• Netmask is optional for host routes\n"
            "• Use CIDR notation (e.g., 24) or dotted decimal (255.255.255.0)"
        )
        help_label = wx.StaticText(panel, label=help_text)
        font = help_label.GetFont()
        font.SetPointSize(font.GetPointSize() - 1)
        help_label.SetFont(font)
        main_sizer.Add(help_label, 0, wx.ALL, 10)
        
        # Buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        add_btn = wx.Button(panel, wx.ID_OK, "Add")
        add_btn.Bind(wx.EVT_BUTTON, self.on_add)
        button_sizer.Add(add_btn, 0, wx.ALL, 5)
        
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        button_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        panel.SetSizer(main_sizer)
    
    def on_add(self, event):
        """Handle add button."""
        destination = self.dest_text.GetValue().strip()
        gateway = self.gateway_text.GetValue().strip()
        netmask = self.netmask_text.GetValue().strip()
        
        # Validate inputs
        if not destination:
            wx.MessageBox(
                "Destination is required.",
                "Validation Error",
                wx.OK | wx.ICON_WARNING
            )
            return
        
        if not gateway:
            wx.MessageBox(
                "Gateway is required.",
                "Validation Error",
                wx.OK | wx.ICON_WARNING
            )
            return
        
        # Validate gateway IP
        if not validate_ip_address(gateway):
            wx.MessageBox(
                "Invalid gateway IP address format.",
                "Validation Error",
                wx.OK | wx.ICON_WARNING
            )
            return
        
        # Validate destination (unless it's "default")
        if destination.lower() != 'default':
            if not validate_ip_address(destination):
                wx.MessageBox(
                    "Invalid destination IP address format.\n"
                    "Use 'default' for default gateway or a valid IP address.",
                    "Validation Error",
                    wx.OK | wx.ICON_WARNING
                )
                return
        
        # Validate netmask if provided
        if netmask and not validate_netmask(netmask):
            wx.MessageBox(
                "Invalid netmask format.\n"
                "Use dotted decimal (e.g., 255.255.255.0) or CIDR notation (e.g., 24).",
                "Validation Error",
                wx.OK | wx.ICON_WARNING
            )
            return
        
        try:
            # Add the route
            if destination.lower() == 'default':
                success = self.network_manager.add_default_gateway(gateway)
            else:
                success = self.network_manager.add_route(
                    destination,
                    gateway,
                    netmask if netmask else None
                )
            
            if success:
                wx.MessageBox(
                    "Route added successfully.",
                    "Success",
                    wx.OK | wx.ICON_INFORMATION
                )
                self.EndModal(wx.ID_OK)
            else:
                wx.MessageBox(
                    "Failed to add route.\nCheck the log for details.",
                    "Error",
                    wx.OK | wx.ICON_ERROR
                )
        
        except Exception as e:
            self.logger.error(f"Error adding route: {e}")
            wx.MessageBox(
                f"Error adding route:\n{str(e)}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )
