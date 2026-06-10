# Device Trust System

A security feature that restricts critical database operations (DELETE, MIGRATE, DROP, etc.) to only **trusted devices**.

## How It Works

1. **Device Identification** - Each device gets a unique fingerprint based on:
   - Hostname (computer name)
   - MAC address (network card ID)
   - Windows username
   - Fingerprint hash

2. **Whitelist** - Trusted devices are stored in `device_whitelist.json`

3. **Authorization** - Before critical operations:
   - Current device fingerprint is calculated
   - Checked against the whitelist
   - Operation is ALLOWED or BLOCKED

4. **Audit Log** - All operations are logged in `logs/device_audit.log`

## Setup Instructions

### Step 1: Check Current Device

First, see your current device information:

```powershell
python device_trust.py info
```

Output will show:
```
Hostname: YOUR-COMPUTER
Username: admin
MAC Address: AA:BB:CC:DD:EE:FF
Device Fingerprint: YOUR-COMPUTER_admin_abc123def456
```

### Step 2: Add Your Device as Trusted

Add your current device to the whitelist:

```powershell
python device_trust.py add "My Work Device"
```

The device name is for your reference (can be anything, e.g., "Server", "Admin PC", "Laptop").

### Step 3: Add Server Device (if applicable)

On the server machine, run:

```powershell
python device_trust.py add "Server"
```

### Step 4: Verify Trusted Devices

List all trusted devices:

```powershell
python device_trust.py list
```

Output:
```
TRUSTED DEVICES

1. My Work Device
   Hostname: YOUR-COMPUTER
   Username: admin
   MAC Address: AA:BB:CC:DD:EE:FF
   Added: 2026-06-10T09:30:00
   Last Used: 2026-06-10T09:35:15

2. Server
   Hostname: DATABASE-SERVER
   Username: system
   MAC Address: 11:22:33:44:55:66
   Added: 2026-06-10T10:00:00
   Last Used: 2026-06-10T10:05:00
```

## Restricted Operations

These operations are restricted to **trusted devices only**:
- `DELETE` - Deleting data
- `MIGRATE` - Migrating data between tables
- `DROP` - Dropping tables/databases
- `TRUNCATE` - Clearing tables
- `ALTER` - Modifying table structure
- `RESTORE` - Restoring from backups

All other operations are allowed on any device.

## Blocked Device Behavior

When an untrusted device tries a restricted operation:

1. **Operation is BLOCKED** - The action is prevented
2. **Error is logged** - Details recorded in audit log
3. **User is informed** - Clear message explaining what to do

Error message:
```
ERROR: Untrusted device: ATTACKER-COMPUTER
Only trusted devices can perform DELETE operations.
To add this device as trusted, run:
  python device_trust.py add 'DeviceName'
```

## Viewing Audit Log

See recent operations:

```powershell
python device_trust.py audit [limit]
```

Examples:
```powershell
python device_trust.py audit 10     # Last 10 operations
python device_trust.py audit 50     # Last 50 operations
```

Audit log output:
```
AUDIT LOG (Last 20 entries)

✓ 2026-06-10T09:30:00
   Operation: MIGRATE
   Device: YOUR-COMPUTER
   Status: ALLOWED
   Details: Trusted device: YOUR-COMPUTER

✓ 2026-06-10T09:31:00
   Operation: DELETE
   Device: DATABASE-SERVER
   Status: ALLOWED
   Details: Trusted device: DATABASE-SERVER

✗ 2026-06-10T09:32:00
   Operation: DELETE
   Device: UNKNOWN-COMPUTER
   Status: BLOCKED
   Details: Untrusted device: UNKNOWN-COMPUTER
```

## Files

### device_whitelist.json
Stores the list of trusted devices (format below):

```json
{
  "trusted_devices": [
    {
      "name": "My Work Device",
      "hostname": "YOUR-COMPUTER",
      "username": "admin",
      "mac_address": "AA:BB:CC:DD:EE:FF",
      "fingerprint_hash": "abc123def456",
      "added_at": "2026-06-10T09:30:00",
      "last_used": "2026-06-10T09:35:15"
    }
  ],
  "created_at": "2026-06-10T09:00:00"
}
```

### logs/device_audit.log
Audit trail of all critical operations (JSON format):

```json
{"timestamp": "2026-06-10T09:30:00", "operation": "MIGRATE", "device": "YOUR-COMPUTER", "status": "ALLOWED", "details": "..."}
{"timestamp": "2026-06-10T09:32:00", "operation": "DELETE", "device": "ATTACKER-PC", "status": "BLOCKED", "details": "..."}
```

## Integration with Migrations

The daily palawan migration (`migrate_palawan_daily.py`) enforces device trust:

1. Before starting migration, device is identified
2. Device is checked against whitelist
3. If **trusted**: Migration proceeds normally
4. If **untrusted**: Migration is BLOCKED with error

Migration logs show:
```
Device: YOUR-COMPUTER (User: admin)
✓ Device is trusted. Proceeding with migration...

[Migration process...]

Device: YOUR-COMPUTER (User: admin)
- Migrated & Deleted: 25
- Skipped (duplicates): 3
```

## Security Notes

### Device Fingerprint is Based On:
- ✓ Hostname (computer name)
- ✓ MAC address (network card)
- ✓ Windows username

### Not Based On:
- ✗ IP address (can change)
- ✗ Login credentials (can be shared)
- ✗ Just device name (can be spoofed)

### Considerations:
- Changing Windows username = **new device** (won't be recognized)
- Replacing network card = **new device** (new MAC address)
- Changing computer name = **new device** (new hostname)
- If you need to update: Remove old device, add new device

### Audit Trail:
- All critical operations are logged
- Timestamps are recorded
- Device and user info captured
- Status (ALLOWED/BLOCKED) tracked
- Can investigate security incidents

## Troubleshooting

### Device not recognized as trusted

**Symptom:** Migration runs but device is blocked

**Solution:**
```powershell
python device_trust.py add "DeviceName"
```

### Too many devices in whitelist

**Symptom:** Old computers still in the list

**Solution:**
1. Edit `device_whitelist.json` manually
2. Remove old device entries
3. Save and retry

### MAC address changed

**Symptom:** Same device no longer recognized

**Cause:** Network card replaced or changed

**Solution:**
```powershell
python device_trust.py add "UpdatedDeviceName"
```

## Best Practices

1. **Add all authorized devices immediately** - Don't wait for blocked operations
2. **Use descriptive names** - e.g., "Admin Desktop", "Backup Server", "Laptop"
3. **Review audit log regularly** - Weekly or monthly
4. **Update whitelist after hardware changes** - New network cards, computer name changes
5. **Monitor for blocked operations** - Investigate any suspicious attempts
6. **Backup device_whitelist.json** - In case of file corruption

## FAQ

**Q: Can attackers bypass this?**
A: Difficult. Would require:
- Physical access to authorized device, OR
- Knowing MAC address + hostname + username, AND
- Having admin access to install/modify code

**Q: What if I add the wrong device?**
A: Edit `device_whitelist.json` and remove the incorrect entry

**Q: Can I run migrations from any device?**
A: No, only trusted devices can perform migrations and deletes

**Q: What if server is compromised?**
A: Attacker still needs to be on a trusted device to run migrations

**Q: Do I need to trust the server?**
A: Yes, the server itself should be added as a trusted device

**Q: What about multi-user systems?**
A: Device fingerprint includes username, so different users = different devices

## Support

For issues:
1. Check `logs/device_audit.log` for blocked operations
2. Verify device info: `python device_trust.py info`
3. List trusted devices: `python device_trust.py list`
4. Review audit log: `python device_trust.py audit`
