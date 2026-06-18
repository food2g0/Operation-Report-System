"""
WebSocket notification system for ORS using Socket.IO
Manages client connections and broadcasts notifications to affected clients.
"""

import json
import threading
from datetime import datetime
from typing import Dict, List, Set, Optional
from logging_config import get_logger

log = get_logger("NotificationManager")


class NotificationManager:
    """Manages Socket.IO connections and notification delivery."""

    def __init__(self):
        # Maps branch_name -> set of connected client IDs
        self.branch_clients: Dict[str, Set[str]] = {}
        # Maps client_id -> branch_name
        self.client_branches: Dict[str, str] = {}
        # Lock for thread-safe operations
        self.lock = threading.Lock()
        # Reference to Socket.IO server (set after initialization)
        self.sio = None

    def set_sio(self, sio):
        """Set the Socket.IO server instance."""
        self.sio = sio

    def register_client(self, client_id: str, branch: str) -> None:
        """Register a client connection for a specific branch."""
        with self.lock:
            if branch not in self.branch_clients:
                self.branch_clients[branch] = set()
            self.branch_clients[branch].add(client_id)
            self.client_branches[client_id] = branch
            log.info(f"Client {client_id} connected for branch: {branch}")

    def unregister_client(self, client_id: str) -> None:
        """Unregister a client when disconnected."""
        with self.lock:
            branch = self.client_branches.pop(client_id, None)
            if branch and branch in self.branch_clients:
                self.branch_clients[branch].discard(client_id)
                if not self.branch_clients[branch]:
                    del self.branch_clients[branch]
            log.info(f"Client {client_id} disconnected from branch: {branch}")

    def get_branch_clients(self, branch: str) -> List[str]:
        """Get all connected client IDs for a branch."""
        with self.lock:
            return list(self.branch_clients.get(branch, set()))

    def broadcast_to_branch(self, branch: str, event: str, data: dict) -> int:
        """
        Broadcast a notification to all connected clients of a branch.
        Returns the number of clients notified.
        """
        if not self.sio:
            log.warning("Socket.IO server not initialized")
            return 0

        clients = self.get_branch_clients(branch)
        if not clients:
            log.debug(f"No connected clients for branch {branch}")
            return 0

        log.info(f"Broadcasting to {len(clients)} clients in branch {branch}: {event}")

        for client_id in clients:
            try:
                self.sio.emit(event, data, to=client_id)
            except Exception as e:
                log.error(f"Failed to emit to client {client_id}: {e}")

        return len(clients)

    def get_connection_stats(self) -> dict:
        """Get current connection statistics."""
        with self.lock:
            total_clients = len(self.client_branches)
            total_branches = len(self.branch_clients)
            return {
                "total_clients": total_clients,
                "total_branches": total_branches,
                "branches": {
                    branch: len(clients)
                    for branch, clients in self.branch_clients.items()
                }
            }


# Global notification manager instance
notification_manager = NotificationManager()
