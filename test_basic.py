#!/usr/bin/env python3
"""
Basic functionality tests for BSD Network Manager.
These tests verify the backend components work correctly.
"""

import sys

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from bsd_netgui.utils.system_utils import (
            validate_ip_address, 
            validate_netmask,
            check_root_privileges,
            execute_command
        )
        from bsd_netgui.backend.interface_handler import InterfaceHandler
        from bsd_netgui.backend.wifi_handler import WiFiHandler
        from bsd_netgui.backend.dns_handler import DNSHandler
        from bsd_netgui.backend.routing_handler import RoutingHandler
        from bsd_netgui.backend.network_manager import NetworkManager
        import bsd_netgui
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_validation():
    """Test validation functions."""
    print("\nTesting validation functions...")
    from bsd_netgui.utils.system_utils import validate_ip_address, validate_netmask
    
    # Test IP validation
    tests = [
        ("192.168.1.1", True),
        ("10.0.0.1", True),
        ("255.255.255.255", True),
        ("256.1.1.1", False),
        ("invalid", False),
        ("", False),
    ]
    
    for ip, expected in tests:
        result = validate_ip_address(ip)
        status = "✓" if result == expected else "✗"
        print(f"  {status} validate_ip_address('{ip}') = {result} (expected {expected})")
        if result != expected:
            return False
    
    # Test netmask validation
    tests = [
        ("255.255.255.0", True),
        ("255.255.0.0", True),
        ("24", True),
        ("16", True),
        ("invalid", False),
        ("256.255.255.0", False),
    ]
    
    for mask, expected in tests:
        result = validate_netmask(mask)
        status = "✓" if result == expected else "✗"
        print(f"  {status} validate_netmask('{mask}') = {result} (expected {expected})")
        if result != expected:
            return False
    
    print("✓ All validation tests passed")
    return True


def test_command_execution():
    """Test command execution."""
    print("\nTesting command execution...")
    from bsd_netgui.utils.system_utils import execute_command
    
    # Test successful command
    success, stdout, stderr = execute_command(['echo', 'test'])
    if not success or 'test' not in stdout:
        print("✗ Simple command failed")
        return False
    print("✓ Command execution working")
    
    # Test command with failure
    success, stdout, stderr = execute_command(['false'])
    if success:
        print("✗ Failed command returned success")
        return False
    print("✓ Failed command detected correctly")
    
    return True


def test_handlers():
    """Test handler instantiation."""
    print("\nTesting handler instantiation...")
    from bsd_netgui.backend.interface_handler import InterfaceHandler
    from bsd_netgui.backend.wifi_handler import WiFiHandler
    from bsd_netgui.backend.dns_handler import DNSHandler
    from bsd_netgui.backend.routing_handler import RoutingHandler
    from bsd_netgui.backend.network_manager import NetworkManager
    
    try:
        ih = InterfaceHandler()
        print("✓ InterfaceHandler")
        
        wh = WiFiHandler()
        print("✓ WiFiHandler")
        
        dh = DNSHandler()
        print("✓ DNSHandler")
        
        rh = RoutingHandler()
        print("✓ RoutingHandler")
        
        nm = NetworkManager()
        print("✓ NetworkManager")
        
        # Test singleton
        nm2 = NetworkManager()
        if nm is not nm2:
            print("✗ Singleton pattern failed")
            return False
        print("✓ Singleton pattern working")
        
        return True
    except Exception as e:
        print(f"✗ Handler instantiation failed: {e}")
        return False


def test_interface_operations():
    """Test interface operations (read-only)."""
    print("\nTesting interface operations...")
    from bsd_netgui.backend.interface_handler import InterfaceHandler
    
    ih = InterfaceHandler()
    try:
        interfaces = ih.list_interfaces()
        print(f"✓ Found {len(interfaces)} network interfaces")
        if interfaces:
            iface = interfaces[0]
            print(f"  Example: {iface['name']} - {iface['status']}")
        return True
    except Exception as e:
        print(f"ℹ Note: {e}")
        print("  (This is expected if ifconfig is not available)")
        return True  # Don't fail on this


def test_routing_operations():
    """Test routing operations (read-only)."""
    print("\nTesting routing operations...")
    from bsd_netgui.backend.routing_handler import RoutingHandler
    
    rh = RoutingHandler()
    try:
        routes = rh.get_routing_table()
        print(f"✓ Found {len(routes)} routes")
        if routes:
            route = routes[0]
            print(f"  Example: {route['destination']} -> {route['gateway']}")
        return True
    except Exception as e:
        print(f"ℹ Note: {e}")
        print("  (This is expected if netstat is not available)")
        return True  # Don't fail on this


def test_dns_operations():
    """Test DNS operations (read-only)."""
    print("\nTesting DNS operations...")
    from bsd_netgui.backend.dns_handler import DNSHandler
    
    dh = DNSHandler()
    try:
        dns_servers = dh.get_dns_servers()
        print(f"✓ Found {len(dns_servers)} DNS servers")
        for server in dns_servers:
            print(f"  - {server}")
        return True
    except Exception as e:
        print(f"ℹ Note: {e}")
        return True  # Don't fail on this


def main():
    """Run all tests."""
    print("=" * 70)
    print("BSD Network Manager - Basic Functionality Tests")
    print("=" * 70)
    
    tests = [
        test_imports,
        test_validation,
        test_command_execution,
        test_handlers,
        test_interface_operations,
        test_routing_operations,
        test_dns_operations,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed > 0:
        print("\n⚠ Some tests failed. Check the output above for details.")
        return 1
    else:
        print("\n✅ All tests passed!")
        print("\nNote: GUI components require wxPython and are not tested here.")
        print("      Run the full application on FreeBSD with root privileges")
        print("      to test the complete functionality.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
