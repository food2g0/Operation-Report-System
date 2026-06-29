"""
Machine fingerprint — hostname + CPU.

Uses the PC name (hostname) as the primary identity so the fingerprint is
stable across reboots, VPN connections, and network-adapter changes.
MAC address is still collected for display in the admin panel but is NOT
used in the machine_id hash.
"""
import hashlib
import platform
import socket
import subprocess


def _get_physical_mac() -> str:
    """
    Return the MAC of the first physical network adapter (for display only).
    On Windows uses wmic to filter virtual/VPN adapters.
    """
    if platform.system() == "Windows":
        try:
            raw_bytes = subprocess.check_output(
                ["wmic", "nic", "where", "PhysicalAdapter=True", "get", "MACAddress"],
                timeout=5,
                stderr=subprocess.DEVNULL,
            )
            out = raw_bytes.replace(b'\x00', b'').decode("ascii", errors="ignore")
            _INVALID = {"00:00:00:00:00:00", "FF:FF:FF:FF:FF:FF"}
            macs = sorted(
                m for m in (
                    line.strip().replace("-", ":").upper()
                    for line in out.splitlines()
                    if line.strip() and line.strip() != "MACAddress"
                )
                if len(m) == 17 and m not in _INVALID
            )
            if macs:
                return macs[0]
        except Exception:
            pass

    import uuid
    mac_int = uuid.getnode()
    return ':'.join(('%012X' % mac_int)[i:i+2] for i in range(0, 12, 2))


def get_machine_id() -> str:
    """Return a 64-char SHA-256 hex digest of hostname + CPU.

    Using hostname (PC name) instead of MAC address prevents false
    re-registrations caused by VPN adapters or virtual NICs changing
    the apparent MAC between sessions.
    """
    hostname = socket.gethostname()
    cpu = platform.processor()
    raw = f"{hostname}||{cpu}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def get_machine_info() -> dict:
    """Return the fingerprint plus human-readable hardware details."""
    hostname = socket.gethostname()
    mac = _get_physical_mac()
    return {
        'machine_id':  get_machine_id(),
        'hostname':    hostname,
        'mac_address': mac,
        'cpu_info':    platform.processor(),
    }
