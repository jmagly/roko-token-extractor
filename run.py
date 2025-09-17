#!/usr/bin/env python3
"""
Quick start script for ROKO Token Data Extractor
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

if __name__ == "__main__":
    from main import main
    main()
