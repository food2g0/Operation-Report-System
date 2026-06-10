"""
Device Trust System - Only allow critical database operations from trusted devices.

This module:
1. Generates a unique device fingerprint
2. Maintains a whitelist of trusted devices
3. Validates device before allowing delete/migrate operations
4. Logs all critical operations with device info

Trusted devices can perform:
- DELETE operations
- MIGRATE operations
- DROP operations
- Any other destructive database operations

Untrusted devices are BLOCKED from these operations.
"""

import os
import json
import uuid
import socket
import logging
from pathlib import Path
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

# Configuration
WHITELIST_FILE = os.path.join(os.path.dirname(__file__), 'device_whitelist.json')
AUDIT_LOG = os.path.join(os.path.dirname(__file__), 'logs', 'device_audit.log')

# Ensure logs directory exists
os.makedirs(os.path.dirname(AUDIT_LOG), exist_ok=True)


def get_device_fingerprint():
    """
    Generate a unique device fingerprint using:
    - Windows machine name (hostname)
    - MAC address
    - Windows user name

    This creates a stable identifier that's hard to spoof.
    """
    try:
        import platform
        import uuid as uuid_lib

        # Get components
        hostname = socket.gethostname()
        username = os.getenv('USERNAME', 'unknown')

        # Get MAC address (first non-loopback interface)
        mac_address = None
        for iface in uuid_lib.getnode.__doc__:  # Fallback approach
            try:
                mac_address = ':'.join(['{:02x}'.format((uuid_lib.getnode() >> ele) & 0xff)
                                       for ele in range(0, 8*6, 8)][::-1])
                break
            except:
                pass

        if not mac_address:
            # Use simpler approach
            mac_address = ':'.join(['{:02x}'.format(x) for x in uuid_lib.getnode().to_bytes(6, 'big')])

        # Create fingerprint string
        fingerprint_str = f"{hostname}|{mac_address}|{username}"

        # Hash for privacy (but include original components for reference)
        fingerprint_hash = hashlib.sha256(fingerprint_str.encode()).hexdigest()[:16]

        return {
            'hostname': hostname,
            'username': username,
            'mac_address': mac_address,
            'fingerprint': f"{hostname}_{username}_{fingerprint_hash}",
            'fingerprint_hash': fingerprint_hash,
            'created_at': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get device fingerprint: {e}")
        return None


def load_whitelist():
    """Load trusted device whitelist from file"""
    if not os.path.exists(WHITELIST_FILE):
        return {'trusted_devices': [], 'created_at': datetime.now().isoformat()}

    try:
        with open(WHITELIST_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load whitelist: {e}")
        return {'trusted_devices': [], 'created_at': datetime.now().isoformat()}


def save_whitelist(whitelist):
    """Save trusted device whitelist to file"""
    try:
        with open(WHITELIST_FILE, 'w') as f:
            json.dump(whitelist, f, indent=2)
        logger.info(f"Whitelist saved with {len(whitelist['trusted_devices'])} trusted devices")
        return True
    except Exception as e:
        logger.error(f"Failed to save whitelist: {e}")
        return False


def add_trusted_device(device_info, device_name):
    """Add current device to whitelist"""
    if not device_info:
        logger.error("Cannot add device: invalid device info")
        return False

    whitelist = load_whitelist()

    # Check if already in whitelist
    for device in whitelist['trusted_devices']:
        if device['fingerprint_hash'] == device_info['fingerprint_hash']:
            logger.warning(f"Device already in whitelist: {device_name}")
            return True

    # Add new device
    trusted_device = {
        'name': device_name,
        'hostname': device_info['hostname'],
        'username': device_info['username'],
        'mac_address': device_info['mac_address'],
        'fingerprint_hash': device_info['fingerprint_hash'],
        'added_at': datetime.now().isoformat(),
        'last_used': datetime.now().isoformat()
    }

    whitelist['trusted_devices'].append(trusted_device)

    if save_whitelist(whitelist):
        logger.info(f"✓ Device added to whitelist: {device_name} ({device_info['hostname']})")
        return True

    return False


def is_device_trusted(device_info):
    """Check if current device is in the trusted whitelist"""
    if not device_info:
        return False

    whitelist = load_whitelist()

    for device in whitelist['trusted_devices']:
        if device['fingerprint_hash'] == device_info['fingerprint_hash']:
            # Update last used timestamp
            device['last_used'] = datetime.now().isoformat()
            save_whitelist(whitelist)
            return True

    return False


def audit_operation(operation, device_info, status, details=""):
    """Log critical operations for audit trail"""
    try:
        os.makedirs(os.path.dirname(AUDIT_LOG), exist_ok=True)

        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'device': device_info['hostname'] if device_info else 'unknown',
            'username': device_info['username'] if device_info else 'unknown',
            'status': status,  # 'ALLOWED' or 'BLOCKED'
            'details': details
        }

        with open(AUDIT_LOG, 'a') as f:
            f.write(json.dumps(audit_entry) + '\n')

        logger.info(f"[AUDIT] {operation}: {status} by {device_info['hostname'] if device_info else 'unknown'}")

    except Exception as e:
        logger.error(f"Failed to log audit entry: {e}")


def check_operation_allowed(operation_type, device_info=None):
    """
    Check if an operation is allowed on this device.

    Args:
        operation_type: Type of operation ('DELETE', 'MIGRATE', 'DROP', etc.)
        device_info: Device fingerprint info (if None, gets current device)

    Returns:
        (allowed: bool, reason: str)
    """

    if device_info is None:
        device_info = get_device_fingerprint()

    # Always allow on server/backend operations
    if operation_type not in ['DELETE', 'MIGRATE', 'DROP', 'TRUNCATE', 'ALTER', 'RESTORE']:
        return True, "Non-critical operation"

    # Check if device is trusted
    if is_device_trusted(device_info):
        audit_operation(operation_type, device_info, 'ALLOWED', f'Trusted device: {device_info["hostname"]}')
        return True, "Device is trusted"

    # Operation blocked
    reason = f"Untrusted device: {device_info['hostname']}. Only trusted devices can perform {operation_type} operations."
    audit_operation(operation_type, device_info, 'BLOCKED', reason)
    logger.warning(f"Operation BLOCKED: {operation_type} from untrusted device {device_info['hostname']}")

    return False, reason


def display_device_info():
    """Display current device information"""
    device_info = get_device_fingerprint()

    if not device_info:
        print("ERROR: Could not get device information")
        return

    print("\n" + "=" * 70)
    print("CURRENT DEVICE INFORMATION")
    print("=" * 70)
    print(f"Hostname: {device_info['hostname']}")
    print(f"Username: {device_info['username']}")
    print(f"MAC Address: {device_info['mac_address']}")
    print(f"Device Fingerprint: {device_info['fingerprint']}")
    print(f"Fingerprint Hash: {device_info['fingerprint_hash']}")
    print("=" * 70 + "\n")


def display_trusted_devices():
    """Display all trusted devices"""
    whitelist = load_whitelist()

    print("\n" + "=" * 100)
    print("TRUSTED DEVICES")
    print("=" * 100)

    if not whitelist['trusted_devices']:
        print("No trusted devices configured yet.\n")
        return

    for i, device in enumerate(whitelist['trusted_devices'], 1):
        print(f"\n{i}. {device.get('name', 'Unknown')}")
        print(f"   Hostname: {device['hostname']}")
        print(f"   Username: {device['username']}")
        print(f"   MAC Address: {device['mac_address']}")
        print(f"   Added: {device['added_at']}")
        print(f"   Last Used: {device.get('last_used', 'Never')}")

    print("\n" + "=" * 100 + "\n")


def get_audit_log_summary(limit=50):
    """Get recent audit log entries"""
    if not os.path.exists(AUDIT_LOG):
        return []

    entries = []
    try:
        with open(AUDIT_LOG, 'r') as f:
            for line in f:
                try:
                    entries.append(json.loads(line))
                except:
                    pass
    except Exception as e:
        logger.error(f"Failed to read audit log: {e}")

    return entries[-limit:]


def display_audit_log(limit=20):
    """Display recent audit log entries"""
    entries = get_audit_log_summary(limit)

    print("\n" + "=" * 100)
    print(f"AUDIT LOG (Last {limit} entries)")
    print("=" * 100)

    if not entries:
        print("No audit log entries yet.\n")
        return

    for entry in entries:
        status_icon = "✓" if entry['status'] == 'ALLOWED' else "✗"
        print(f"\n{status_icon} {entry['timestamp']}")
        print(f"   Operation: {entry['operation']}")
        print(f"   Device: {entry['device']}")
        print(f"   Status: {entry['status']}")
        if entry['details']:
            print(f"   Details: {entry['details']}")

    print("\n" + "=" * 100 + "\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Device Trust System\n")
        print("Usage:")
        print("  python device_trust.py info              - Show current device info")
        print("  python device_trust.py list              - List trusted devices")
        print("  python device_trust.py add <name>        - Add current device as trusted")
        print("  python device_trust.py audit [limit]     - Show audit log")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'info':
        display_device_info()

    elif command == 'list':
        display_trusted_devices()

    elif command == 'add':
        if len(sys.argv) < 3:
            print("ERROR: Device name required")
            print("Usage: python device_trust.py add <device_name>")
            sys.exit(1)

        device_name = sys.argv[2]
        device_info = get_device_fingerprint()

        if add_trusted_device(device_info, device_name):
            print(f"\n✓ Device '{device_name}' added to trusted whitelist!")
            display_device_info()
            display_trusted_devices()
        else:
            print(f"\n✗ Failed to add device")
            sys.exit(1)

    elif command == 'audit':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        display_audit_log(limit)

    elif command == 'check':
        device_info = get_device_fingerprint()
        allowed, reason = check_operation_allowed('DELETE', device_info)
        print(f"\nOperation allowed: {allowed}")
        print(f"Reason: {reason}\n")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
