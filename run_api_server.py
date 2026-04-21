"""
REST API Server Entry Point
Run this to start the API server
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.app import app

if __name__ == '__main__':
    app.run()
