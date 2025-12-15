"""System utility functions for BSD Network Manager."""

import os
import subprocess
import logging
import ipaddress
from typing import List, Tuple


def execute_command(cmd: List[str], timeout: int = 30) -> Tuple[bool, str, str]:
    """
    Execute a system command safely using subprocess.
    
    Args:
        cmd: Command and arguments as a list of strings
        timeout: Command timeout in seconds (default: 30)
    
    Returns:
        Tuple of (success, stdout, stderr)
    
    Example:
        >>> success, output, error = execute_command(['ls', '-la'])
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        success = result.returncode == 0
        return success, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logging.error(f"Command timed out after {timeout} seconds: {' '.join(cmd)}")
        return False, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        logging.error(f"Error executing command {' '.join(cmd)}: {str(e)}")
        return False, "", str(e)


def check_root_privileges() -> bool:
    """
    Check if the current process is running with root privileges.
    
    Returns:
        True if running as root, False otherwise
    
    Note:
        Uses os.geteuid() which returns 0 for root on Unix-like systems
    """
    try:
        return os.geteuid() == 0
    except AttributeError:
        # Windows doesn't have geteuid()
        logging.warning("Unable to check root privileges on this platform")
        return False


def validate_ip_address(ip: str) -> bool:
    """
    Validate IPv4 address format.
    
    Args:
        ip: IP address string to validate
    
    Returns:
        True if valid IPv4 address, False otherwise
    
    Example:
        >>> validate_ip_address("192.168.1.1")
        True
        >>> validate_ip_address("invalid")
        False
    """
    try:
        ipaddress.IPv4Address(ip)
        return True
    except (ipaddress.AddressValueError, ValueError):
        return False


def validate_netmask(netmask: str) -> bool:
    """
    Validate netmask format.
    
    Args:
        netmask: Netmask string to validate (e.g., "255.255.255.0" or "24")
    
    Returns:
        True if valid netmask, False otherwise
    
    Example:
        >>> validate_netmask("255.255.255.0")
        True
        >>> validate_netmask("24")
        True
    """
    # Check if it's a CIDR notation (e.g., "24")
    if netmask.isdigit():
        prefix_len = int(netmask)
        return 0 <= prefix_len <= 32
    
    # Check if it's a dotted decimal notation (e.g., "255.255.255.0")
    try:
        # Convert to IPv4Address and check if it's a valid netmask
        addr = ipaddress.IPv4Address(netmask)
        # A valid netmask in binary should be all 1s followed by all 0s
        # Convert to int and check
        addr_int = int(addr)
        # Check if it's a valid netmask pattern
        # Valid netmasks: 0xFFFFFFFF, 0xFFFFFFFE, 0xFFFFFFFC, etc.
        # Invalid: 0xFFFFFF00, 0xFF00FFFF, etc.
        
        # Count leading ones
        binary_str = bin(addr_int)[2:].zfill(32)
        # Should be all 1s followed by all 0s
        if '01' in binary_str:
            return False
        return True
    except (ipaddress.AddressValueError, ValueError):
        return False


def setup_logging(log_file: str = "/var/log/bsd-netgui.log", level: int = logging.INFO):
    """
    Configure Python logging for the application.
    
    Args:
        log_file: Path to log file (default: /var/log/bsd-netgui.log)
        level: Logging level (default: logging.INFO)
    
    Note:
        Falls back to console logging if unable to write to log file
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    try:
        # Try to log to file
        logging.basicConfig(
            level=level,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        logging.info("Logging initialized successfully")
    except (PermissionError, OSError) as e:
        # Fall back to console-only logging
        logging.basicConfig(
            level=level,
            format=log_format,
            handlers=[logging.StreamHandler()]
        )
        logging.warning(f"Could not write to log file {log_file}: {e}. Using console logging only.")
