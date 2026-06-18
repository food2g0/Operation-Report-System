# Compatibility shim - imports from new location
# This file allows old imports like: from api_config import API_MODE
# to continue working after moving to tools/api_utilities/

import sys
from pathlib import Path

# Add tools/api_utilities to path so imports work
sys.path.insert(0, str(Path(__file__).parent / 'tools' / 'api_utilities'))

# Re-export everything from the new location
from tools.api_utilities.api_config import *

__all__ = ['API_MODE', 'API_URL', 'API_KEY', 'API_TIMEOUT']
