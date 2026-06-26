"""
Machine fingerprint — physical MAC address + CPU.

Uses wmic to query only PhysicalAdapter=True NICs on Windows, which excludes
VPN clients, VMware/Docker virtual adapters, and any other software-only
interfaces.  Falls back to uuid.getnode() on non-Windows platforms.
"""
import hashlib
import platform
import socket
import subprocess


def _get_physical_mac() -> str:
    """
    Return the MAC of the first physical network adapter.
    On Windows, uses wmic to filter out virtual/VPN adapters.
    Falls back to uuid.getnode() on failure or non-Windows.
    """
    if platform.system() == "Windows":
        try:
            raw_bytes = subprocess.check_output(
                ["wmic", "nic", "where", "PhysicalAdapter=True", "get", "MACAddress"],
                timeout=5,
                stderr=subprocess.DEVNULL,
            )
            # wmic outputs UTF-16 LE — strip null bytes so ASCII chars are clean
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
                # Alphabetically smallest physical MAC — deterministic across
                # reboots even when wmic enumeration order changes.
                return macs[0]
        except Exception:
            pass

    # Non-Windows or wmic unavailable — fall back to uuid.getnode()
    import uuid
    mac_int = uuid.getnode()
    return ':'.join(('%012X' % mac_int)[i:i+2] for i in range(0, 12, 2))


def get_machine_id() -> str:
    """Return a 64-char SHA-256 hex digest of physical MAC + CPU."""
    mac = _get_physical_mac()
    cpu = platform.processor()
    raw = f"{mac}||{cpu}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def get_machine_info() -> dict:
    """Return the fingerprint plus human-readable hardware details."""
    mac = _get_physical_mac()
    return {
        'machine_id':  get_machine_id(),
        'hostname':    socket.gethostname(),
        'mac_address': mac,
        'cpu_info':    platform.processor(),
    }
