"""IPC (Inter-Process Communication) module for daemon communication."""

from .server import IPCServer
from .client import IPCClient

__all__ = ["IPCServer", "IPCClient"]
