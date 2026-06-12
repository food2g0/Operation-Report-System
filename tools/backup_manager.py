"""Database backup manager - creates and manages database backups.

Usage:
    python backup_manager.py --backup          # Create backup
    python backup_manager.py --list            # List backups
    python backup_manager.py --restore FILE    # Restore from backup
    python backup_manager.py --cleanup         # Remove old backups
"""

import os
import sys
import logging
import datetime
import subprocess
import json
import argparse
from pathlib import Path
from config import DB_CONFIG

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Backup configuration
BACKUP_DIR = Path("backups")
BACKUP_DIR.mkdir(exist_ok=True)
MAX_BACKUPS = 10  # Keep last 10 backups
BACKUP_MANIFEST = BACKUP_DIR / "manifest.json"


class DatabaseBackupManager:
    """Manages database backups and restores."""

    def __init__(self, host=None, user=None, password=None,
                 database=None, port=None):
        """Initialize backup manager.

        Args:
            host: Database host
            user: Database user
            password: Database password
            database: Database name
            port: Database port
        """
        self.host = host or DB_CONFIG.get('host')
        self.user = user or DB_CONFIG.get('user')
        self.password = password or DB_CONFIG.get('password')
        self.database = database or DB_CONFIG.get('database')
        self.port = port or DB_CONFIG.get('port')
        self.backup_dir = BACKUP_DIR
        self.manifest_file = BACKUP_MANIFEST

    def create_backup(self, description="", compress=True):
        """Create a database backup.

        Args:
            description: Optional backup description
            compress: Whether to compress the backup

        Returns:
            tuple: (success, backup_file, message)
        """
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backup_{self.database}_{timestamp}"

            if compress:
                backup_file = self.backup_dir / f"{filename}.sql.gz"
                cmd = (
                    f"mysqldump -h {self.host} -P {self.port} -u {self.user} "
                    f"-p{self.password} {self.database} | gzip > \"{backup_file}\""
                )
            else:
                backup_file = self.backup_dir / f"{filename}.sql"
                cmd = (
                    f"mysqldump -h {self.host} -P {self.port} -u {self.user} "
                    f"-p{self.password} {self.database} > \"{backup_file}\""
                )

            # Execute backup command
            logger.info(f"Starting backup: {backup_file}")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else "Unknown error"
                logger.error(f"Backup failed: {error_msg}")
                return False, None, f"Backup failed: {error_msg}"

            # Get file size
            file_size = backup_file.stat().st_size
            size_mb = file_size / (1024 * 1024)

            # Record in manifest
            self._add_to_manifest(str(backup_file), description, size_mb)

            # Cleanup old backups
            self._cleanup_old_backups()

            message = f"Backup created: {backup_file.name} ({size_mb:.2f} MB)"
            logger.info(message)
            return True, str(backup_file), message

        except Exception as e:
            logger.error(f"Backup error: {e}")
            return False, None, f"Backup error: {str(e)}"

    def restore_backup(self, backup_file):
        """Restore database from backup.

        Args:
            backup_file: Path to backup file

        Returns:
            tuple: (success, message)
        """
        try:
            backup_path = Path(backup_file)

            if not backup_path.exists():
                return False, f"Backup file not found: {backup_file}"

            # Determine if compressed
            is_compressed = backup_path.suffix == ".gz"

            logger.info(f"Starting restore from: {backup_path}")

            # Build restore command
            if is_compressed:
                cmd = (
                    f"gunzip < \"{backup_path}\" | "
                    f"mysql -h {self.host} -P {self.port} -u {self.user} "
                    f"-p{self.password} {self.database}"
                )
            else:
                cmd = (
                    f"mysql -h {self.host} -P {self.port} -u {self.user} "
                    f"-p{self.password} {self.database} < \"{backup_path}\""
                )

            # Execute restore
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else "Unknown error"
                logger.error(f"Restore failed: {error_msg}")
                return False, f"Restore failed: {error_msg}"

            message = f"Database restored from: {backup_path.name}"
            logger.info(message)
            return True, message

        except Exception as e:
            logger.error(f"Restore error: {e}")
            return False, f"Restore error: {str(e)}"

    def list_backups(self):
        """List all available backups.

        Returns:
            list: List of backup info dicts
        """
        try:
            if not self.manifest_file.exists():
                return []

            with open(self.manifest_file, 'r') as f:
                data = json.load(f)
                return data.get('backups', [])

        except Exception as e:
            logger.error(f"Error reading backups: {e}")
            return []

    def _add_to_manifest(self, backup_file, description, size_mb):
        """Add backup to manifest file.

        Args:
            backup_file: Path to backup file
            description: Backup description
            size_mb: File size in MB
        """
        try:
            # Read existing manifest
            if self.manifest_file.exists():
                with open(self.manifest_file, 'r') as f:
                    data = json.load(f)
            else:
                data = {'backups': []}

            # Add new backup
            backup_info = {
                'file': backup_file,
                'timestamp': datetime.datetime.now().isoformat(),
                'description': description,
                'size_mb': round(size_mb, 2)
            }
            data['backups'].append(backup_info)

            # Write back
            with open(self.manifest_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.warning(f"Could not update manifest: {e}")

    def _cleanup_old_backups(self):
        """Remove old backups, keeping only the latest."""
        try:
            manifest_data = self.list_backups()

            if len(manifest_data) <= MAX_BACKUPS:
                return

            # Sort by timestamp, newest first
            manifest_data.sort(
                key=lambda x: x['timestamp'],
                reverse=True
            )

            # Remove old backups
            for old_backup in manifest_data[MAX_BACKUPS:]:
                backup_path = Path(old_backup['file'])
                if backup_path.exists():
                    backup_path.unlink()
                    logger.info(f"Deleted old backup: {backup_path.name}")

            # Update manifest
            with open(self.manifest_file, 'w') as f:
                data = {'backups': manifest_data[:MAX_BACKUPS]}
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.warning(f"Cleanup error: {e}")

    def get_backup_stats(self):
        """Get backup statistics.

        Returns:
            dict: Backup statistics
        """
        backups = self.list_backups()
        total_size = sum(b.get('size_mb', 0) for b in backups)

        return {
            'total_backups': len(backups),
            'total_size_mb': round(total_size, 2),
            'latest_backup': backups[0] if backups else None,
            'oldest_backup': backups[-1] if backups else None
        }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Database backup manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python backup_manager.py --backup                Create backup
  python backup_manager.py --list                  List backups
  python backup_manager.py --restore backups/backup_ors_20260612_120000.sql.gz
  python backup_manager.py --cleanup               Remove old backups
  python backup_manager.py --stats                 Show backup statistics
        '''
    )

    parser.add_argument('--backup', action='store_true', help='Create backup')
    parser.add_argument('--list', action='store_true', help='List backups')
    parser.add_argument('--restore', metavar='FILE', help='Restore from backup')
    parser.add_argument('--cleanup', action='store_true', help='Cleanup old backups')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--description', default='', help='Backup description')

    args = parser.parse_args()

    manager = DatabaseBackupManager()

    if args.backup:
        success, backup_file, message = manager.create_backup(args.description)
        print(message)
        sys.exit(0 if success else 1)

    elif args.list:
        backups = manager.list_backups()
        if not backups:
            print("No backups found")
        else:
            print(f"\n{'File':<50} {'Size (MB)':<12} {'Date':<20}")
            print("-" * 82)
            for backup in reversed(backups):
                timestamp = backup['timestamp'][:10]  # YYYY-MM-DD
                print(
                    f"{Path(backup['file']).name:<50} "
                    f"{backup.get('size_mb', 0):<12.2f} {timestamp:<20}"
                )
            print()

    elif args.restore:
        success, message = manager.restore_backup(args.restore)
        print(message)
        sys.exit(0 if success else 1)

    elif args.cleanup:
        manager._cleanup_old_backups()
        print("Cleanup completed")

    elif args.stats:
        stats = manager.get_backup_stats()
        print(f"\nBackup Statistics:")
        print(f"  Total backups: {stats['total_backups']}")
        print(f"  Total size: {stats['total_size_mb']:.2f} MB")
        if stats['latest_backup']:
            print(f"  Latest: {Path(stats['latest_backup']['file']).name}")
            print(f"  Timestamp: {stats['latest_backup']['timestamp']}")
        print()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
