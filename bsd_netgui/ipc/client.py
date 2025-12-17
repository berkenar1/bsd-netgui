"""Unix socket client for daemon communication."""

import json
import logging
import socket

logger = logging.getLogger(__name__)


class IPCClient:
    """Unix socket client for IPC communication."""

    def __init__(self, socket_path="/var/run/bsd-netgui.sock"):
        """
        Initialize IPC client.

        Args:
            socket_path: Path to Unix socket
        """
        self.socket_path = socket_path

    def send_request(self, request_dict, timeout=5.0):
        """
        Send request to daemon and get response.

        Args:
            request_dict: Dictionary with request data
            timeout: Socket timeout in seconds

        Returns:
            Response dictionary or None if error
        """
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect(self.socket_path)

            # Send request
            request_str = json.dumps(request_dict) + "\0"
            sock.sendall(request_str.encode("utf-8"))

            # Receive response
            response_data = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                if b"\0" in response_data:
                    break

            sock.close()

            # Parse response
            if response_data:
                response_str = response_data.decode("utf-8").rstrip("\0")
                return json.loads(response_str)

            return {"success": False, "error": "No response from daemon"}
        except socket.timeout:
            logger.error("Request timeout")
            return {"success": False, "error": "Request timeout"}
        except ConnectionRefusedError:
            logger.error(f"Could not connect to daemon at {self.socket_path}")
            return {"success": False, "error": "Daemon not running"}
        except Exception as e:
            logger.error(f"IPC error: {e}")
            return {"success": False, "error": str(e)}
