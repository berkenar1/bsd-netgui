"""Main entry point for BSD Network Manager."""

import sys
import logging
import wx
from .utils.system_utils import check_root_privileges, setup_logging
from .gui.main_window import MainWindow


def main():
    """
    Main entry point for the application.
    
    This function:
    1. Sets up logging
    2. Checks for root privileges (required for network management)
    3. Initializes the wxPython application
    4. Creates and shows the main window
    5. Starts the application event loop
    """
    # Setup logging
    try:
        setup_logging()
    except Exception as e:
        print(f"Warning: Could not setup file logging: {e}")
        logging.basicConfig(level=logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting BSD Network Manager")
    
    # Check for root privileges
    if not check_root_privileges():
        logger.error("Root privileges required")
        
        # Show error dialog
        app = wx.App(False)
        wx.MessageBox(
            "BSD Network Manager requires root privileges to manage network settings.\n\n"
            "Please run the application with sudo:\n"
            "  sudo bsd-netgui\n\n"
            "or:\n"
            "  sudo python -m bsd_netgui.main",
            "Root Privileges Required",
            wx.OK | wx.ICON_ERROR
        )
        return 1
    
    # Create the application
    try:
        app = wx.App(False)
        
        # Create and show the main window
        frame = MainWindow()
        frame.Show()
        
        logger.info("Main window created and shown")
        
        # Start the event loop
        app.MainLoop()
        
        logger.info("Application closed")
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        
        # Try to show error dialog
        try:
            wx.MessageBox(
                f"A fatal error occurred:\n\n{str(e)}\n\n"
                "Please check the log file for details.",
                "Fatal Error",
                wx.OK | wx.ICON_ERROR
            )
        except:
            pass
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
