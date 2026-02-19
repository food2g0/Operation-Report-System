"""
Directory Cleanup Utility
Removes temporary files, logs, and test artifacts from the project directory.

Usage:
    python cleanup_directory.py

Options:
    --dry-run    Show what would be deleted without actually deleting
    --all        Clean everything including build outputs
"""
import os
import sys
import shutil
from pathlib import Path


# Files and directories to clean
CLEANUP_TARGETS = {
    'logs': [
        'database.log',
        'performance.log',
        'db_deadlock_retries.log',
        '*.log'
    ],
    'temp_files': [
        '~$*.docx',
        '~$*.xlsx',
        '*.tmp',
        '*.bak',
        '*.swp'
    ],
    'test_files': [
        'test_*.py',
        'check_*.py',
        'inspect_*.py',
        'alter_*.py',
        'add_missing_lotes.py',
        'add_unique_index.py',
        'execute_sql_file.py',
        'refresh_summary.py',
        'test_insert_lotes.py'
    ],
    'example_files': [
        'palawan_page_optimized_example.py'
    ],
    'generated_reports': [
        'Palawan_Report_*.docx',
        'PEPP_Reconciliation_*.xlsx',
        '*.docx',  # All Word docs in root
        '*.xlsx'   # All Excel files in root
    ],
    'build_outputs': [
        'build/',
        'dist/',
        '__pycache__/',
        '*.pyc',
        '*.pyo',
        '*.egg-info/'
    ]
}


def find_files(pattern, base_path='.'):
    """Find files matching a glob pattern"""
    from glob import glob
    return glob(os.path.join(base_path, pattern), recursive=False)


def clean_category(category, targets, dry_run=False, base_path='.'):
    """Clean files in a specific category"""
    print(f"\n{'🔍' if dry_run else '🗑️'}  Cleaning {category}...")
    removed_count = 0
    
    for pattern in targets:
        # Handle directories
        if pattern.endswith('/'):
            dir_path = os.path.join(base_path, pattern.rstrip('/'))
            if os.path.isdir(dir_path):
                if dry_run:
                    print(f"   Would remove directory: {dir_path}")
                else:
                    try:
                        shutil.rmtree(dir_path)
                        print(f"   ✅ Removed directory: {dir_path}")
                        removed_count += 1
                    except Exception as e:
                        print(f"   ❌ Error removing {dir_path}: {e}")
        else:
            # Handle file patterns
            matches = find_files(pattern, base_path)
            for file_path in matches:
                # Skip if it's a directory
                if os.path.isdir(file_path):
                    continue
                    
                if dry_run:
                    print(f"   Would remove: {file_path}")
                else:
                    try:
                        os.remove(file_path)
                        print(f"   ✅ Removed: {file_path}")
                        removed_count += 1
                    except Exception as e:
                        print(f"   ❌ Error removing {file_path}: {e}")
    
    if removed_count == 0:
        print(f"   No files found to clean")
    else:
        print(f"   Removed {removed_count} item(s)")
    
    return removed_count


def cleanup_directory(dry_run=False, clean_all=False):
    """Main cleanup function"""
    print("=" * 60)
    print("🧹 DIRECTORY CLEANUP UTILITY")
    print("=" * 60)
    
    if dry_run:
        print("⚠️  DRY RUN MODE - No files will be deleted")
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    total_removed = 0
    
    # Clean categories
    categories_to_clean = ['logs', 'temp_files']
    
    if '--keep-tests' not in sys.argv:
        categories_to_clean.append('test_files')
        categories_to_clean.append('example_files')
    
    if '--keep-reports' not in sys.argv:
        if input("\n⚠️  Delete generated reports (*.docx, *.xlsx)? [y/N]: ").lower() == 'y':
            categories_to_clean.append('generated_reports')
    
    if clean_all or '--clean-build' in sys.argv:
        categories_to_clean.append('build_outputs')
    
    # Perform cleanup
    for category in categories_to_clean:
        if category in CLEANUP_TARGETS:
            removed = clean_category(category, CLEANUP_TARGETS[category], dry_run, base_path)
            total_removed += removed
    
    # Summary
    print("\n" + "=" * 60)
    if dry_run:
        print(f"✅ Dry run complete. {total_removed} item(s) would be removed.")
        print("\nRun without --dry-run to actually delete files:")
        print("   python cleanup_directory.py")
    else:
        print(f"✅ Cleanup complete! {total_removed} item(s) removed.")
    print("=" * 60)
    
    return total_removed


def create_dev_directory():
    """Move test/development files to a separate dev/ folder"""
    dev_dir = 'dev_scripts'
    if not os.path.exists(dev_dir):
        os.makedirs(dev_dir)
        print(f"\n📁 Created {dev_dir}/ directory")
    
    # Files to move to dev/
    dev_files = [
        'test_connection.py',
        'test_insert_lotes.py',
        'check_lotes_column.py',
        'inspect_daily_reports.py',
        'alter_lotes_to_smallint.py',
        'add_missing_lotes.py',
        'add_unique_index.py',
        'execute_sql_file.py',
        'refresh_summary.py',
        'test_performance_improvements.py',
        'palawan_page_optimized_example.py'
    ]
    
    moved_count = 0
    for filename in dev_files:
        if os.path.exists(filename):
            try:
                shutil.move(filename, os.path.join(dev_dir, filename))
                print(f"   ✅ Moved {filename} → {dev_dir}/")
                moved_count += 1
            except Exception as e:
                print(f"   ❌ Error moving {filename}: {e}")
    
    if moved_count > 0:
        print(f"\n✅ Moved {moved_count} development file(s) to {dev_dir}/")
    
    return moved_count


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up project directory')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without deleting')
    parser.add_argument('--all', action='store_true', help='Clean everything including build outputs')
    parser.add_argument('--organize-dev', action='store_true', help='Move dev files to dev_scripts/ folder')
    
    args = parser.parse_args()
    
    # Organize dev files first if requested
    if args.organize_dev:
        print("\n📂 Organizing development files...\n")
        create_dev_directory()
    
    # Perform cleanup
    cleanup_directory(dry_run=args.dry_run, clean_all=args.all)
    
    print("\n💡 Tips:")
    print("   • Add files to .gitignore to prevent them from being tracked")
    print("   • Use --dry-run to preview changes before deleting")
    print("   • Use --organize-dev to move test files to dev_scripts/")
