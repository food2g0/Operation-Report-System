"""
Machine fingerprint — MAC address + CPU only.
Stable across reboots and app updates; changes only if the NIC or CPU is replaced.
"""
import uuid
import hashlib
import platform
import socket


def get_machine_id() -> str:
    """Return a 64-char SHA-256 hex digest of MAC + CPU."""
    mac_int = uuid.getnode()
    mac = ':'.join(('%012X' % mac_int)[i:i+2] for i in range(0, 12, 2))
    cpu = platform.processor()
    raw = f"{mac}||{cpu}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def get_machine_info() -> dict:
    """Return the fingerprint plus human-readable hardware details."""
    mac_int = uuid.getnode()
    mac = ':'.join(('%012X' % mac_int)[i:i+2] for i in range(0, 12, 2))
    return {
        'machine_id':  get_machine_id(),
        'hostname':    socket.gethostname(),
        'mac_address': mac,
        'cpu_info':    platform.processor(),
    }
