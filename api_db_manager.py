# Compatibility shim - imports from new location
# This file allows old imports like: from api_db_manager import db_manager
# to continue working after moving to tools/api_utilities/

import sys
from pathlib import Path

# Add tools/api_utilities to path so imports work
sys.path.insert(0, str(Path(__file__).parent / 'tools' / 'api_utilities'))

# Re-export everything from the new location
from tools.api_utilities.api_db_manager import APIDbManager, db_manager

__all__ = ['APIDbManager', 'db_manager']
