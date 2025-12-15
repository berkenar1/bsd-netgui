"""Main window for BSD Network Manager."""

import wx
import logging
from .interface_panel import InterfacePanel
from .wifi_panel import WiFiPanel
from .dns_panel import DNSPanel
from .routing_panel import RoutingPanel
from ..backend.network_manager import NetworkManager


class MainWindow(wx.Frame):
    """
    Main application window with tabbed interface.
    
    This window provides a notebook-based interface with tabs for:
    - Network Interfaces
    - WiFi Management
    - DNS Configuration
    - Routing Table
    """
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__(
            None,
            title="BSD Network Manager",
            size=(900, 600),
            style=wx.DEFAULT_FRAME_STYLE
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing main window")
        
        # Initialize network manager
        try:
            self.network_manager = NetworkManager()
        except Exception as e:
            self.logger.error(f"Failed to initialize network manager: {e}")
            wx.MessageBox(
                f"Failed to initialize network manager:\n{str(e)}",
                "Initialization Error",
                wx.OK | wx.ICON_ERROR
            )
            self.Close()
            return
        
        # Create UI components
        self._create_menu_bar()
        self._create_status_bar()
        self._create_notebook()
        
        # Center the window
        self.Centre()
        
        self.logger.info("Main window initialized successfully")
    
    def _create_menu_bar(self):
        """Create the menu bar."""
        menubar = wx.MenuBar()
        
        # File menu
        file_menu = wx.Menu()
        exit_item = file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl-Q", "Exit application")
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        menubar.Append(file_menu, "&File")
        
        # View menu
        view_menu = wx.Menu()
        refresh_item = view_menu.Append(wx.ID_REFRESH, "&Refresh\tF5", "Refresh all information")
        self.Bind(wx.EVT_MENU, self.on_refresh, refresh_item)
        menubar.Append(view_menu, "&View")
        
        # Help menu
        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT, "&About", "About BSD Network Manager")
        self.Bind(wx.EVT_MENU, self.on_about, about_item)
        menubar.Append(help_menu, "&Help")
        
        self.SetMenuBar(menubar)
    
    def _create_status_bar(self):
        """Create the status bar."""
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText("Ready")
    
    def _create_notebook(self):
        """Create the notebook with all panels."""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create notebook
        notebook = wx.Notebook(panel)
        
        # Create and add tabs
        try:
            self.interface_panel = InterfacePanel(notebook, self.network_manager)
            notebook.AddPage(self.interface_panel, "Interfaces")
            
            self.wifi_panel = WiFiPanel(notebook, self.network_manager)
            notebook.AddPage(self.wifi_panel, "WiFi")
            
            self.dns_panel = DNSPanel(notebook, self.network_manager)
            notebook.AddPage(self.dns_panel, "DNS")
            
            self.routing_panel = RoutingPanel(notebook, self.network_manager)
            notebook.AddPage(self.routing_panel, "Routing")
            
        except Exception as e:
            self.logger.error(f"Failed to create panels: {e}")
            wx.MessageBox(
                f"Failed to create interface panels:\n{str(e)}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )
        
        sizer.Add(notebook, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(sizer)
    
    def on_refresh(self, event):
        """Handle refresh menu item."""
        self.logger.info("Refreshing all panels")
        self.statusbar.SetStatusText("Refreshing...")
        
        try:
            self.refresh_all()
            self.statusbar.SetStatusText("Refresh complete")
        except Exception as e:
            self.logger.error(f"Error during refresh: {e}")
            self.statusbar.SetStatusText("Refresh failed")
            wx.MessageBox(
                f"Error refreshing data:\n{str(e)}",
                "Refresh Error",
                wx.OK | wx.ICON_ERROR
            )
    
    def refresh_all(self):
        """Refresh all panels."""
        try:
            self.interface_panel.refresh()
            self.wifi_panel.refresh()
            self.dns_panel.refresh()
            self.routing_panel.refresh()
        except Exception as e:
            self.logger.error(f"Error refreshing panels: {e}")
            raise
    
    def on_about(self, event):
        """Show about dialog."""
        info = wx.adv.AboutDialogInfo()
        info.SetName("BSD Network Manager")
        info.SetVersion("0.1.0")
        info.SetDescription(
            "A modern GUI network management tool for FreeBSD and other BSD systems.\n\n"
            "Features:\n"
            "• Interface management (enable/disable, configure IP)\n"
            "• WiFi network scanning and connection\n"
            "• DNS configuration\n"
            "• Routing table management"
        )
        info.SetWebSite("https://github.com/berkenar1/bsd-netgui")
        info.SetLicense("MIT License")
        info.AddDeveloper("berkenar1")
        
        wx.adv.AboutBox(info)
    
    def on_exit(self, event):
        """Handle exit menu item."""
        self.logger.info("Application exit requested")
        self.Close()
