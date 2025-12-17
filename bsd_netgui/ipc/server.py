"""Unix socket server for daemon communication."""

import os
import json
import logging
import socket
import threading
from pathlib import Path

logger = logging.getLogger(__name__)


class IPCServer:
    """Unix socket server for IPC communication."""

    def __init__(self, socket_path="/var/run/bsd-netgui.sock"):
        """
        Initialize IPC server.

        Args:
            socket_path: Path to Unix socket
        """
        self.socket_path = socket_path
        self.socket = None
        self.running = False
        self.request_handler = None

    def set_request_handler(self, handler):
        """
        Set the request handler callback.

        Args:
            handler: Callable that takes (request_dict) and returns response_dict
        """
        self.request_handler = handler

    def start(self):
        """Start the IPC server."""
        # Clean up old socket if it exists
        if os.path.exists(self.socket_path):
            try:
                os.remove(self.socket_path)
            except OSError:
                logger.warning(f"Could not remove old socket {self.socket_path}")

        # Create socket directory if needed
        socket_dir = os.path.dirname(self.socket_path)
        if socket_dir and not os.path.exists(socket_dir):
            Path(socket_dir).mkdir(parents=True, exist_ok=True)

        # Create Unix socket
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(self.socket_path)
        self.socket.listen(1)
        self.running = True

        logger.info(f"IPC server listening on {self.socket_path}")

        # Run server in background thread
        server_thread = threading.Thread(target=self._accept_connections, daemon=True)
        server_thread.start()

    def stop(self):
        """Stop the IPC server."""
        self.running = False
        if self.socket:
            self.socket.close()
        if os.path.exists(self.socket_path):
            try:
                os.remove(self.socket_path)
            except OSError:
                pass

    def _accept_connections(self):
        """Accept and handle incoming connections."""
        while self.running:
            try:
                connection, client_address = self.socket.accept()
                # Handle connection in a thread
                thread = threading.Thread(
                    target=self._handle_client, args=(connection,), daemon=True
                )
                thread.start()
            except (OSError, KeyboardInterrupt):
                if self.running:
                    logger.error("Error accepting connection", exc_info=True)
                break

    def _handle_client(self, connection):
        """Handle a client connection."""
        try:
            # Read request
            data = b""
            while True:
                chunk = connection.recv(4096)
                if not chunk:
                    break
                data += chunk
                # Check if we have a complete JSON message (ends with \0)
                if b"\0" in data:
                    break

            if data:
                request_str = data.decode("utf-8").rstrip("\0")
                request = json.loads(request_str)

                # Process request
                response = {"success": False, "error": "No handler set"}
                if self.request_handler:
                    response = self.request_handler(request)

                # Send response
                response_str = json.dumps(response) + "\0"
                connection.sendall(response_str.encode("utf-8"))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            connection.close()
