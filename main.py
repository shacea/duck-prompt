#!/usr/bin/env python3
"""
Duck Prompt - FAH Edition
Main entry point for the FAH-based application
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the FAH application
from src.app import main

if __name__ == "__main__":
    main()
