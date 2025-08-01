#!/usr/bin/env python3
"""
Zentrafuge v9 - Render Startup Script
Handles the correct path setup for Render deployment
"""

import os
import sys

# Add backend directory to Python path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

# Change to backend directory
os.chdir(backend_dir)

# Import and run the main app
try:
    from app import app
    
    if __name__ == "__main__":
        port = int(os.environ.get("PORT", 5000))
        app.run(host="0.0.0.0", port=port, debug=False)
except ImportError as e:
    print(f"Failed to import app: {e}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Files in directory: {os.listdir('.')}")
    sys.exit(1)
