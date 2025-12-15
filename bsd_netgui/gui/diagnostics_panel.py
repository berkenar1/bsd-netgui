"""Network diagnostics panel for BSD Network Manager."""

import wx
import logging
import threading
from ..backend.diagnostics_handler import DiagnosticsHandler


class DiagnosticsPanel(wx.Panel):
    """
    Panel for displaying network diagnostics and running connectivity tests.
    
    Provides real-time network status information and troubleshooting tools.
    """
    
    def __init__(self, parent, network_manager):
        """
        Initialize the diagnostics panel.
        
        Args:
            parent: Parent window
            network_manager: NetworkManager instance
        """
        super().__init__(parent)
        self.network_manager = network_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize diagnostics handler
        self.diag_handler = DiagnosticsHandler()
        
        self._create_ui()
        self.refresh()
    
    def _create_ui(self):
        """Create the user interface."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Title
        title = wx.StaticText(self, label="Network Diagnostics")
        title_font = title.GetFont()
        title_font.PointSize += 2
        title_font = title_font.Bold()
        title.SetFont(title_font)
        main_sizer.Add(title, 0, wx.ALL, 10)
        
        # Connectivity status indicators
        status_box = wx.StaticBox(self, label="Connectivity Status")
        status_sizer = wx.StaticBoxSizer(status_box, wx.HORIZONTAL)
        
        # Gateway status
        gateway_panel = self._create_status_indicator("Default Gateway")
        self.gateway_indicator = gateway_panel['indicator']
        self.gateway_label = gateway_panel['label']
        status_sizer.Add(gateway_panel['panel'], 1, wx.EXPAND | wx.ALL, 5)
        
        # External connectivity status
        external_panel = self._create_status_indicator("External Network")
        self.external_indicator = external_panel['indicator']
        self.external_label = external_panel['label']
        status_sizer.Add(external_panel['panel'], 1, wx.EXPAND | wx.ALL, 5)
        
        # DNS status
        dns_panel = self._create_status_indicator("DNS Resolution")
        self.dns_indicator = dns_panel['indicator']
        self.dns_label = dns_panel['label']
        status_sizer.Add(dns_panel['panel'], 1, wx.EXPAND | wx.ALL, 5)
        
        main_sizer.Add(status_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Notebook for different diagnostic sections
        self.notebook = wx.Notebook(self)
        
        # Interface Status tab
        self.interface_text = wx.TextCtrl(
            self.notebook,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP | wx.HSCROLL,
            size=(-1, 300)
        )
        self.notebook.AddPage(self.interface_text, "Interface Status")
        
        # Routing Table tab
        self.routing_text = wx.TextCtrl(
            self.notebook,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP | wx.HSCROLL
        )
        self.notebook.AddPage(self.routing_text, "Routing Table")
        
        # DNS Configuration tab
        self.dns_text = wx.TextCtrl(
            self.notebook,
            style=wx.TE_MULTILINE | wx.TE_READONLY
        )
        self.notebook.AddPage(self.dns_text, "DNS Config")
        
        # ARP Table tab
        self.arp_text = wx.TextCtrl(
            self.notebook,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP | wx.HSCROLL
        )
        self.notebook.AddPage(self.arp_text, "ARP Table")
        
        # Active Connections tab
        self.connections_text = wx.TextCtrl(
            self.notebook,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP | wx.HSCROLL
        )
        self.notebook.AddPage(self.connections_text, "Connections")
        
        # Help tab
        help_panel = self._create_help_panel()
        self.notebook.AddPage(help_panel, "Common Issues")
        
        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)
        
        # Action buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.refresh_btn = wx.Button(self, label="Refresh All")
        self.refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh)
        button_sizer.Add(self.refresh_btn, 0, wx.ALL, 5)
        
        self.test_btn = wx.Button(self, label="Run Connectivity Tests")
        self.test_btn.Bind(wx.EVT_BUTTON, self.on_run_tests)
        button_sizer.Add(self.test_btn, 0, wx.ALL, 5)
        
        button_sizer.AddStretchSpacer()
        
        self.copy_btn = wx.Button(self, label="Copy to Clipboard")
        self.copy_btn.Bind(wx.EVT_BUTTON, self.on_copy_to_clipboard)
        button_sizer.Add(self.copy_btn, 0, wx.ALL, 5)
        
        self.export_btn = wx.Button(self, label="Export Report")
        self.export_btn.Bind(wx.EVT_BUTTON, self.on_export_report)
        button_sizer.Add(self.export_btn, 0, wx.ALL, 5)
        
        main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        self.SetSizer(main_sizer)
    
    def _create_status_indicator(self, label_text):
        """
        Create a status indicator panel.
        
        Args:
            label_text: Label for the indicator
        
        Returns:
            Dictionary with panel, indicator, and label widgets
        """
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Indicator (colored circle)
        indicator = wx.Panel(panel, size=(40, 40))
        indicator.SetBackgroundColour(wx.Colour(200, 200, 200))  # Gray by default
        sizer.Add(indicator, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        # Label
        label = wx.StaticText(panel, label=label_text)
        label.SetFont(label.GetFont().Bold())
        sizer.Add(label, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        # Status text
        status_label = wx.StaticText(panel, label="Unknown")
        sizer.Add(status_label, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        panel.SetSizer(sizer)
        
        return {
            'panel': panel,
            'indicator': indicator,
            'label': status_label
        }
    
    def _create_help_panel(self):
        """Create the help panel with common issues."""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        help_text = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP,
            value="Common Network Issues and Solutions\n\n"
        )
        
        # Add common issues
        issues = self.diag_handler.get_common_issues_help()
        help_content = "Common Network Issues and Solutions\n"
        help_content += "=" * 70 + "\n\n"
        
        for issue_info in issues:
            help_content += f"Issue: {issue_info['issue']}\n"
            help_content += f"{'-' * 70}\n"
            help_content += f"Solution:\n{issue_info['help']}\n\n"
            help_content += f"Reference: {issue_info['handbook']}\n"
            help_content += "\n" + "=" * 70 + "\n\n"
        
        help_text.SetValue(help_content)
        sizer.Add(help_text, 1, wx.EXPAND | wx.ALL, 5)
        
        panel.SetSizer(sizer)
        return panel
    
    def refresh(self):
        """Refresh all diagnostic information."""
        self.logger.info("Refreshing diagnostics")
        
        # Show loading message
        self.interface_text.SetValue("Loading...")
        self.routing_text.SetValue("Loading...")
        self.dns_text.SetValue("Loading...")
        self.arp_text.SetValue("Loading...")
        self.connections_text.SetValue("Loading...")
        
        # Run in background thread
        thread = threading.Thread(target=self._refresh_in_background)
        thread.daemon = True
        thread.start()
    
    def _refresh_in_background(self):
        """Refresh diagnostics in background thread."""
        try:
            # Collect diagnostic information
            interface_status = self.diag_handler.get_interface_status()
            routing_table = self.diag_handler.get_routing_table()
            dns_config = self.diag_handler.get_dns_config()
            arp_table = self.diag_handler.get_arp_table()
            connections = self.diag_handler.get_active_connections()
            
            # Update UI in main thread
            wx.CallAfter(self._update_diagnostics_ui, 
                        interface_status, routing_table, dns_config, 
                        arp_table, connections)
        except Exception as e:
            self.logger.error(f"Error refreshing diagnostics: {e}")
            wx.CallAfter(wx.MessageBox,
                        f"Error refreshing diagnostics:\n{str(e)}",
                        "Error",
                        wx.OK | wx.ICON_ERROR)
    
    def _update_diagnostics_ui(self, interface_status, routing_table, 
                               dns_config, arp_table, connections):
        """Update diagnostics UI with collected data."""
        self.interface_text.SetValue(interface_status)
        self.routing_text.SetValue(routing_table)
        self.dns_text.SetValue(dns_config)
        self.arp_text.SetValue(arp_table)
        self.connections_text.SetValue(connections)
    
    def on_refresh(self, event):
        """Handle refresh button click."""
        self.refresh()
    
    def on_run_tests(self, event):
        """Handle run connectivity tests button click."""
        self.logger.info("Running connectivity tests")
        
        # Disable button during test
        self.test_btn.Enable(False)
        self.test_btn.SetLabel("Testing...")
        
        # Run in background thread
        thread = threading.Thread(target=self._run_tests_in_background)
        thread.daemon = True
        thread.start()
    
    def _run_tests_in_background(self):
        """Run connectivity tests in background thread."""
        try:
            # Run connectivity tests
            gateway_test = self.diag_handler.test_gateway_connectivity()
            external_test = self.diag_handler.test_external_connectivity()
            dns_test = self.diag_handler.test_dns_resolution()
            
            # Update UI in main thread
            wx.CallAfter(self._update_connectivity_status, 
                        gateway_test, external_test, dns_test)
        except Exception as e:
            self.logger.error(f"Error running connectivity tests: {e}")
            wx.CallAfter(wx.MessageBox,
                        f"Error running tests:\n{str(e)}",
                        "Error",
                        wx.OK | wx.ICON_ERROR)
        finally:
            wx.CallAfter(self.test_btn.Enable, True)
            wx.CallAfter(self.test_btn.SetLabel, "Run Connectivity Tests")
    
    def _update_connectivity_status(self, gateway_test, external_test, dns_test):
        """Update connectivity status indicators."""
        # Gateway indicator
        self._set_indicator_status(
            self.gateway_indicator,
            self.gateway_label,
            gateway_test['status'],
            gateway_test['message']
        )
        
        # External indicator
        self._set_indicator_status(
            self.external_indicator,
            self.external_label,
            external_test['status'],
            external_test['message']
        )
        
        # DNS indicator
        self._set_indicator_status(
            self.dns_indicator,
            self.dns_label,
            dns_test['status'],
            dns_test['message']
        )
    
    def _set_indicator_status(self, indicator, label, status, message):
        """
        Set status indicator color and label.
        
        Args:
            indicator: Indicator panel
            label: Status label
            status: Status ('success', 'failure', 'error')
            message: Status message
        """
        if status == 'success':
            color = wx.Colour(0, 200, 0)  # Green
        elif status == 'failure':
            color = wx.Colour(200, 0, 0)  # Red
        elif status == 'error':
            color = wx.Colour(255, 165, 0)  # Orange
        else:
            color = wx.Colour(200, 200, 200)  # Gray
        
        indicator.SetBackgroundColour(color)
        indicator.Refresh()
        label.SetLabel(message)
    
    def on_copy_to_clipboard(self, event):
        """Handle copy to clipboard button click."""
        try:
            # Get current tab content
            current_page = self.notebook.GetCurrentPage()
            
            if isinstance(current_page, wx.TextCtrl):
                text = current_page.GetValue()
            else:
                # Export full diagnostics
                diagnostics = self.diag_handler.run_full_diagnostics()
                text = self._format_diagnostics_text(diagnostics)
            
            # Copy to clipboard
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(text))
                wx.TheClipboard.Close()
                
                wx.MessageBox(
                    "Diagnostics copied to clipboard!",
                    "Success",
                    wx.OK | wx.ICON_INFORMATION
                )
        except Exception as e:
            self.logger.error(f"Error copying to clipboard: {e}")
            wx.MessageBox(
                f"Error copying to clipboard:\n{str(e)}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )
    
    def on_export_report(self, event):
        """Handle export report button click."""
        wildcard = "Text files (*.txt)|*.txt|All files (*.*)|*.*"
        dialog = wx.FileDialog(
            self,
            "Export Diagnostics Report",
            defaultFile="network_diagnostics.txt",
            wildcard=wildcard,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )
        
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            
            try:
                if self.diag_handler.export_diagnostics_report(path):
                    wx.MessageBox(
                        f"Diagnostics report exported to:\n{path}",
                        "Success",
                        wx.OK | wx.ICON_INFORMATION
                    )
                else:
                    wx.MessageBox(
                        "Failed to export diagnostics report.",
                        "Error",
                        wx.OK | wx.ICON_ERROR
                    )
            except Exception as e:
                self.logger.error(f"Error exporting report: {e}")
                wx.MessageBox(
                    f"Error exporting report:\n{str(e)}",
                    "Error",
                    wx.OK | wx.ICON_ERROR
                )
        
        dialog.Destroy()
    
    def _format_diagnostics_text(self, diagnostics):
        """Format diagnostics dictionary as text."""
        text = "Network Diagnostics Report\n"
        text += "=" * 70 + "\n\n"
        
        for key, value in diagnostics.items():
            text += f"{key.replace('_', ' ').title()}:\n"
            text += "-" * 70 + "\n"
            if isinstance(value, dict):
                for k, v in value.items():
                    text += f"{k}: {v}\n"
            else:
                text += str(value) + "\n"
            text += "\n"
        
        return text
